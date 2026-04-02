"""
Buyurtma yaratish handleri — savat → band qilish → to'lov kutish
"""
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import PAYMENT_GROUP_ID
from bot.db.models import (
    get_user, cart_get, cart_clear,
    create_order, create_order_item,
    get_prices_by_product, get_vip_level,
    reserve_accounts_for_order, release_reserved_accounts,
    update_order_status, set_order_progress_message,
    get_order, increment_promo_usage, get_promo_by_code,
)
from bot.utils.texts import t
from bot.utils.duration import tier_display_name

router = Router()

# To'lov rekvizitlari (config ga qo'shilishi kerak, hozir hardcode)
CLICK_NUMBER = "8600 0000 0000 0000"
PAYME_NUMBER = "8600 0000 0000 0000"


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
        # Savatni olish
        items = await cart_get(user_telegram_id)
        if not items:
            await message.answer(t("cart_empty", lang))
            return

        await message.answer(t("order_creating", lang))

        # Narxlar va chegirma hisoblash
        total = sum(item["price"] * item["quantity"] for item in items)

        # FSM dan promo ni olish
        fsm_data = await state.get_data()
        promo_code = fsm_data.get("promo_code")
        promo = None
        if promo_code:
            promo = await get_promo_by_code(promo_code)

        user = await get_user(user_telegram_id)
        vip_level = user.get("vip_level", "standard") if user else "standard"
        vip_info = await get_vip_level(vip_level)
        vip_pct = vip_info["discount_percent"] if vip_info else 0
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
            # Narxni topish
            prices = await get_prices_by_product(item["product_id"])
            price_info = next((p for p in prices if p["duration_tier"] == item["duration_tier"]), None)
            cost_price = price_info["cost_price"] if price_info else 0
            unit_price = item["price"]

            # Akkauntlarni band qilish
            reserved = await reserve_accounts_for_order(
                order_id=order_id,
                product_id=item["product_id"],
                duration_tier=item["duration_tier"],
                quantity=item["quantity"]
            )

            if len(reserved) < item["quantity"]:
                shortage = item["quantity"] - len(reserved)
                tier_name = tier_display_name(item["duration_tier"], lang)
                name = item[f"name_{lang}"]
                shortage_details.append(f"• {name} ({tier_name}): {shortage} ta yetmaydi" if lang == "uz"
                                         else f"• {name} ({tier_name}): не хватает {shortage} шт")

            # order_items ga yozish
            await create_order_item(
                order_id=order_id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                duration_tier=item["duration_tier"],
                unit_price=unit_price,
                cost_price=cost_price
            )

        # Yetarli akkaunt yo'q bo'lsa — buyurtmani bekor qilish
        if shortage_details:
            await release_reserved_accounts(order_id)
            await update_order_status(order_id, "cancelled")
            details_text = "\n".join(shortage_details)
            await message.answer(t("order_insufficient_stock", lang, details=details_text))
            return

        # Savatni tozalash
        await cart_clear(user_telegram_id)

        # Promo foydalanish sonini oshirish
        if promo_id:
            await increment_promo_usage(promo_id)

        # Progress bar xabarini yuborish
        progress_msg = await message.answer(
            t("order_created_progress", lang,
              order_id=order_id,
              amount=final_amount,
              click=CLICK_NUMBER,
              payme=PAYME_NUMBER)
        )

        # progress_message_id ni saqlash
        await set_order_progress_message(order_id, progress_msg.message_id)
        await state.clear()

    except Exception as e:
        await message.answer(t("error_general", lang))
