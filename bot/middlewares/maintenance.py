"""
Maintenance middleware — texnik tanaffus vaqtida foydalanuvchilarni bloklaydi
"""
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

from bot.config import ADMIN_IDS

logger = logging.getLogger(__name__)


class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        try:
            from bot.utils.settings import get_setting_bool, get_setting

            if await get_setting_bool("bot_maintenance_mode"):
                user_id = event.from_user.id if event.from_user else 0
                if user_id in ADMIN_IDS:
                    return await handler(event, data)

                # Check if admin in db
                from bot.db.models import get_admin_by_telegram_id
                admin = await get_admin_by_telegram_id(user_id)
                if admin:
                    return await handler(event, data)

                # Send maintenance message
                user = None
                try:
                    from bot.db.models import get_user
                    user = await get_user(user_id)
                except Exception:
                    pass
                lang = user.get("language", "uz") if user else "uz"
                msg = await get_setting(f"maintenance_message_{lang}",
                                        "Bot vaqtinchalik ishlamayapti.")

                if isinstance(event, Message):
                    await event.answer(msg)
                elif isinstance(event, CallbackQuery):
                    await event.answer(msg, show_alert=True)
                return
        except Exception as e:
            logger.exception(f"Maintenance middleware error: {e}")

        return await handler(event, data)
