"""
Admin rol tekshirish middleware
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery

from bot.config import ADMIN_IDS
from bot.db.models import get_admin_by_telegram_id, create_admin_role


# Rol darajalari (qaysi rol qaysi darajada)
ROLE_LEVELS = {
    "operator": 1,
    "manager": 2,
    "boss": 3,
}


class RoleCheckMiddleware(BaseMiddleware):
    """
    Admin handlerlar uchun rol tekshirish.
    data['admin_role'] ga joriy adminning rolini yozadi.
    Agar admin bo'lmasa yoki huquq bo'lmasa — None yozadi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        telegram_id: int | None = None

        if isinstance(event, Update):
            if event.message:
                telegram_id = event.message.from_user.id
            elif event.callback_query:
                telegram_id = event.callback_query.from_user.id

        admin_role = None

        if telegram_id:
            # Birinchi ADMIN_ID avtomatik 'boss'
            if telegram_id == ADMIN_IDS[0]:
                # DB da yo'q bo'lsa yaratib qo'yish
                existing = await get_admin_by_telegram_id(telegram_id)
                if not existing:
                    await create_admin_role(telegram_id, role="boss")
                admin_role = "boss"
            else:
                admin_record = await get_admin_by_telegram_id(telegram_id)
                if admin_record:
                    admin_role = admin_record["role"]

        data["admin_role"] = admin_role
        return await handler(event, data)


def require_role(min_role: str = "operator"):
    """
    Dekorator: handler uchun minimal rol talabi.
    Rol yetarli bo'lmasa — rад xabar yuborib, handlerni to'xtatadi.
    """
    def decorator(handler: Callable) -> Callable:
        async def wrapper(event: Any, *args, **kwargs) -> Any:
            # data dict ni topish
            data = {}
            for arg in args:
                if isinstance(arg, dict):
                    data = arg
                    break
            data.update(kwargs)

            admin_role = data.get("admin_role")
            if not admin_role:
                # Admin emas
                if isinstance(event, Message):
                    from bot.utils.texts import t
                    lang = data.get("lang", "uz")
                    await event.answer(t("access_denied", lang))
                elif isinstance(event, CallbackQuery):
                    from bot.utils.texts import t
                    lang = data.get("lang", "uz")
                    await event.answer(t("access_denied", lang), show_alert=True)
                return

            required_level = ROLE_LEVELS.get(min_role, 1)
            user_level = ROLE_LEVELS.get(admin_role, 0)

            if user_level < required_level:
                if isinstance(event, Message):
                    from bot.utils.texts import t
                    lang = data.get("lang", "uz")
                    await event.answer(t("access_denied", lang))
                elif isinstance(event, CallbackQuery):
                    from bot.utils.texts import t
                    lang = data.get("lang", "uz")
                    await event.answer(t("access_denied", lang), show_alert=True)
                return

            return await handler(event, *args, **kwargs)
        return wrapper
    return decorator
