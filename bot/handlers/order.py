"""
Buyurtma yaratish handleri — savat → band qilish → to'lov kutish
YANGI STRUKTURA: duration_tier yo'q, narx products.price dan
"""
import logging
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


async def get_setting_or_empty(key: str) -> str:
    try:
        from bot.utils.settings import get_setting
        return await get_setting(key, "")
    except Exception:
        return ""

from bot.db.models import (
    get_user, cart_get, cart_clear,
    create_order, add_order_item,
    reserve_accounts, release_reserved,
    update_order_status, get_promo_by_code,
    increment_promo_usage,
)
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()


async def create_order_handler(
    message: Message,
    user_telegram_id: int,
    lang: str,
    state: FSMContext
) -> None:
    """
    Savat → Buyurtma yaratish asosiy logikasi.
    Savat elementlarini tekshiradi, band qiladi, orders/order_items ga yozadi.
    """
    try:
        items = await cart_get(user_telegram_id)
        if not items:
            await message.answer(t("cart_empty", lang))
            return

        await message.answer(t("order_creating", lang))

        # Narxlar hisoblash (price to'g'ridan-to'g'ri product dan keladi)
        total = sum(item["price"] * item["quantity"] for item in items)

        # FSM dan promo ni olish
        fsm_data = await state.get_data()
        promo_code = fsm_data.get("promo_code")
        promo = None
        if promo_code:
            promo = await get_promo_by_code(promo_code)

        # VIP chegirma
        user = await get_user(user_telegram_id)
        vip_pct = 0
        try:
            from bot.db.models import get_vip_levels
            vip_levels = await get_vip_levels()
            vip_level = user.get("vip_level", "standard") if user else "standard"
            for vl in vip_levels:
                if vl["level"] == vip_level:
                    vip_pct = vl["discount_percent"]
                    break
        except Exception:
            pass

        promo_pct = promo["discount_percent"] if promo else 0
        final_pct = max(vip_pct, promo_pct)
        discount_amount = int(total * final_pct / 100)
        final_amount = total - discount_amount

        promo_id = promo["id"] if promo else None

        # Buyurtma yaratish
        order_id = await create_order(
            user_telegram_id=user_telegram_id,
            total_amount=final_amount,
            discount_amount=discount_amount,
            promo_code_id=promo_id
        )

        # Har bir savat elementi uchun akkauntlarni band qilish
        shortage_details = []
        for item in items:
            cost_price = item.get("cost_price", 0)
            unit_price = item["price"]

            # Akkauntlarni band qilish
            reserved = await reserve_accounts(
                product_id=item["product_id"],
                quantity=item["quantity"],
                order_id=order_id
            )

            if len(reserved) < item["quantity"]:
                shortage = item["quantity"] - len(reserved)
                name = item.get(f"name_{lang}", item.get("name_uz", "?"))
                shortage_details.append(
                    f"• {name}: {shortage} ta yetmaydi" if lang == "uz"
                    else f"• {name}: не хватает {shortage} шт"
                )

            # order_items ga yozish
            await add_order_item(
                order_id=order_id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=unit_price,
                cost_price=cost_price
            )

        # Yetarli akkaunt yo'q bo'lsa — buyurtmani bekor qilish
        if shortage_details:
            await release_reserved(order_id)
            await update_order_status(order_id, "cancelled")
            details_text = "\n".join(shortage_details)
            await message.answer(t("order_insufficient_stock", lang, details=details_text))
            return

        # Savatni tozalash
        await cart_clear(user_telegram_id)

        # Promo foydalanish sonini oshirish
        if promo_id:
            await increment_promo_usage(promo_id)

        # PHASE 4: Auto-confirmation tekshirish
        try:
            from bot.utils.settings import get_setting_bool, get_setting_int  # noqa: F401
            auto_enabled = await get_setting_bool("auto_confirm_enabled", False)
            auto_limit = await get_setting_int("auto_confirm_limit", 50000)
            if auto_enabled and final_amount <= auto_limit:
                # Avtomatik tasdiqlash
                from bot.db.models import (
                    confirm_reserved, increment_purchase_count,
                    increment_user_purchases, check_and_upgrade_vip,
                    get_order_items
                )
                from bot.handlers.payment import build_account_delivery_text

                sold_accounts = await confirm_reserved(order_id, user_telegram_id)

                fresh_items = await get_order_items(order_id)
                for item in fresh_items:
                    await increment_purchase_count(item["product_id"])

                await increment_user_purchases(user_telegram_id, final_amount)
                await check_and_upgrade_vip(user_telegram_id)
                await update_order_status(order_id, "confirmed")

                accounts_text = build_account_delivery_text(fresh_items, lang)
                await cart_clear(user_telegram_id)
                await state.clear()

                await message.answer("✅ To'lovingiz avtomatik tasdiqlandi!\n\n" + t("order_delivered", lang,
                                     order_id=order_id, accounts_text=accounts_text),
                                     parse_mode="HTML")
                return
        except Exception as e:
            logger.warning(f"Auto-confirm check error: {e}")

        # To'lov ma'lumotlarini settings dan olish
        try:
            from bot.utils.settings import get_setting
            import json
            methods_json = await get_setting("payment_methods", "[]")
            methods = json.loads(methods_json)
            payment_info = ""
            for m in methods:
                if m.get("active"):
                    payment_info += f"\n💳 {m['name']}: {m.get('card', '')}"
            if not payment_info:
                payment_info = "\n💳 To'lov ma'lumotlari sozlanmagan"
        except Exception:
            payment_info = ""

        # Payme/Click URL lari
        payme_id = await get_setting_or_empty("payme_merchant_id")
        click_merchant_id = await get_setting_or_empty("click_merchant_id")
        click_service_id = await get_setting_or_empty("click_service_id")

        payment_kb_rows = []
        if payme_id:
            import base64 as b64
            amount_tiyin = final_amount * 100
            payme_params = f"m={payme_id};ac.order_id={order_id};a={amount_tiyin}"
            payme_encoded = b64.b64encode(payme_params.encode()).decode()
            payme_url = f"https://checkout.paycom.uz/{payme_encoded}"
            payment_kb_rows.append([
                InlineKeyboardButton(text="💳 Payme orqali to'lash", url=payme_url)
            ])
        if click_merchant_id and click_service_id:
            click_url = (
                f"https://my.click.uz/services/pay?service_id={click_service_id}"
                f"&merchant_id={click_merchant_id}&amount={final_amount}"
                f"&transaction_param={order_id}&return_url="
            )
            payment_kb_rows.append([
                InlineKeyboardButton(text="💳 Click orqali to'lash", url=click_url)
            ])

        payment_kb = InlineKeyboardMarkup(inline_keyboard=payment_kb_rows) if payment_kb_rows else None

        # Progress bar xabarini yuborish
        progress_msg = await message.answer(
            t("order_created_progress", lang,
              order_id=order_id,
              amount=final_amount,
              payment_info=payment_info),
            reply_markup=payment_kb
        )

        # progress_message_id ni saqlash
        await update_order_status(order_id, "pending_payment",
                                  progress_message_id=progress_msg.message_id)
        await state.clear()

    except Exception as e:
        logger.exception(f"create_order_handler error: {e}")
        await message.answer(t("error_general", lang))
