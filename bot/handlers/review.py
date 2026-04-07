from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from bot.db.models import get_user, create_review
from bot.utils.texts import t

router = Router()

STARS = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]


class ReviewFSM(StatesGroup):
    enter_comment = State()


@router.callback_query(F.data.startswith("review_rate:"))
async def review_rate(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    order_item_id = int(parts[1])
    rating = int(parts[2])

    user = await get_user(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    await state.update_data(order_item_id=order_item_id, rating=rating)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_review_skip", lang), callback_data="review_skip")]
    ])
    await call.message.edit_text(
        f"{STARS[rating-1]} Baho: {rating}/5\n\n" + t("review_comment_prompt", lang),
        reply_markup=kb
    )
    await state.set_state(ReviewFSM.enter_comment)
    await call.answer()


@router.callback_query(F.data == "review_skip")
async def review_skip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    from bot.db.database import get_db
    async with get_db() as db:
        cursor = await db.execute("SELECT product_id FROM order_items WHERE id = ?", (data["order_item_id"],))
        row = await cursor.fetchone()
    product_id = dict(row)["product_id"] if row else 0
    await create_review(
        user_telegram_id=call.from_user.id,
        product_id=product_id,
        order_item_id=data["order_item_id"],
        rating=data["rating"],
        comment=None
    )
    await state.clear()
    await call.message.edit_text(t("review_thanks", lang))
    await call.answer()


@router.message(ReviewFSM.enter_comment)
async def review_comment(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    data = await state.get_data()

    from bot.db.database import get_db
    async with get_db() as db:
        cursor = await db.execute("SELECT product_id FROM order_items WHERE id = ?", (data["order_item_id"],))
        row = await cursor.fetchone()
    product_id = dict(row)["product_id"] if row else 0
    await create_review(
        user_telegram_id=message.from_user.id,
        product_id=product_id,
        order_item_id=data["order_item_id"],
        rating=data["rating"],
        comment=message.text
    )
    await state.clear()
    await message.answer(t("review_thanks", lang))


def make_review_keyboard(order_item_id: int, lang: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i in range(1, 6):
        row.append(InlineKeyboardButton(
            text=f"{'⭐' * i}",
            callback_data=f"review_rate:{order_item_id}:{i}"
        ))
    buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text=t("btn_review_skip", lang),
        callback_data="review_skip_all"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "review_skip_all")
async def review_skip_all(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
