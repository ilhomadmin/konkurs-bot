"""
Katalog handler — (keyingi bosqichda to'liq implement qilinadi)
"""
from aiogram import Router, F
from aiogram.types import Message

from bot.db.models import get_user
from bot.utils.texts import t

router = Router()


@router.message(F.text.in_(["📦 Obunalar", "📦 Подписки"]))
async def catalog_handler(message: Message) -> None:
    """Katalog (keyingi bosqichda implement qilinadi)"""
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    await message.answer("🚧 Katalog tez orada..." if lang == "uz" else "🚧 Каталог скоро...")


@router.message(F.text.in_(["🛒 Savat", "🛒 Корзина"]))
async def cart_handler(message: Message) -> None:
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    await message.answer("🚧 Savat tez orada..." if lang == "uz" else "🚧 Корзина скоро...")


@router.message(F.text.in_(["📋 Buyurtmalarim", "📋 Мои заказы"]))
async def orders_handler(message: Message) -> None:
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    await message.answer("🚧 Buyurtmalar tez orada..." if lang == "uz" else "🚧 Заказы скоро...")


@router.message(F.text.in_(["🎁 To'plamlar", "🎁 Комплекты"]))
async def bundles_handler(message: Message) -> None:
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    await message.answer("🚧 To'plamlar tez orada..." if lang == "uz" else "🚧 Комплекты скоро...")
