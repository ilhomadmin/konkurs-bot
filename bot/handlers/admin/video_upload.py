"""
Admin: Video yuklash handler
Bot admin videoni yuboradi, caption ga #video_KEYWORD yozadi
→ obuna turi yoki turkumga instruction_video_file_id biriktiriladi
"""
import logging
from aiogram import Router, F
from aiogram.types import Message

from bot.db.database import get_db
from bot.db.models import get_admin_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.video)
async def handle_video_upload(message: Message) -> None:
    """Admin video xabarlarini tekshiradi"""
    caption = message.caption or ""
    if not caption.startswith("#video_"):
        return  # Oddiy video — o'tkazib yubor

    # Admin tekshirish
    admin = await get_admin_by_telegram_id(message.from_user.id)
    if not admin:
        return

    keyword = caption[7:].strip().split()[0]  # #video_ dan keyin birinchi so'z
    file_id = message.video.file_id

    try:
        if keyword.startswith("cat_"):
            # Turkum videosi: #video_cat_dizayn
            cat_keyword = keyword[4:]
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT id, name_uz FROM categories WHERE video_keyword = ?",
                    (cat_keyword,)
                )
                row = await cursor.fetchone()
                if row:
                    await db.execute(
                        "UPDATE categories SET instruction_video_file_id = ? WHERE id = ?",
                        (file_id, row["id"])
                    )
                    await db.commit()
                    await message.reply(
                        f"✅ Video '{row['name_uz']}' turkumiga biriktirildi!"
                    )
                else:
                    await message.reply(
                        f"❌ '{cat_keyword}' keyword li turkum topilmadi.\n"
                        "Turkum yaratishda video_keyword maydonini to'ldiring."
                    )
        else:
            # Obuna turi videosi: #video_chatgpt1oy
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT id, name_uz FROM products WHERE video_keyword = ?",
                    (keyword,)
                )
                row = await cursor.fetchone()
                if row:
                    await db.execute(
                        "UPDATE products SET instruction_video_file_id = ? WHERE id = ?",
                        (file_id, row["id"])
                    )
                    await db.commit()
                    await message.reply(
                        f"✅ Video '{row['name_uz']}' obuna turiga biriktirildi!"
                    )
                else:
                    await message.reply(
                        f"❌ '{keyword}' keyword li obuna turi topilmadi.\n"
                        "Obuna turi yaratishda video_keyword maydonini to'ldiring."
                    )
    except Exception as e:
        logger.exception(f"Video upload error: {e}")
        await message.reply(f"❌ Xato: {e}")
