"""
Til middleware — har bir so'rovda foydalanuvchi tilini aniqlaydi
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.db.models import get_user


class LanguageMiddleware(BaseMiddleware):
    """
    Har bir yangilanishda foydalanuvchi tilini DB dan o'qib,
    data['lang'] ga yozadi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Telegram ID ni aniqlash
        telegram_id: int | None = None

        if isinstance(event, Update):
            if event.message:
                telegram_id = event.message.from_user.id
            elif event.callback_query:
                telegram_id = event.callback_query.from_user.id

        lang = "uz"
        if telegram_id:
            try:
                user = await get_user(telegram_id)
                if user:
                    lang = user.get("language", "uz")
            except Exception:
                pass

        data["lang"] = lang
        return await handler(event, data)
