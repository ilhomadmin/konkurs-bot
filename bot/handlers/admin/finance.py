import io
from datetime import date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.models import get_finance_report, get_daily_finance_data, add_expense
from bot.utils.texts import t

router = Router()


class ExpenseFSM(StatesGroup):
    enter_amount = State()
    enter_desc = State()


def _make_finance_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_finance_today", lang), callback_data="fin_today"),
            InlineKeyboardButton(text=t("btn_finance_week", lang), callback_data="fin_week"),
            InlineKeyboardButton(text=t("btn_finance_month", lang), callback_data="fin_month"),
        ],
        [InlineKeyboardButton(text=t("btn_add_expense", lang), callback_data="fin_add_expense")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_main")],
    ])


@router.callback_query(F.data == "adm_finance")
async def admin_finance(call: CallbackQuery):
    await _show_report(call, "today")


@router.callback_query(F.data.in_({"fin_today", "fin_week", "fin_month"}))
async def finance_period(call: CallbackQuery):
    period_map = {"fin_today": "today", "fin_week": "week", "fin_month": "month"}
    await _show_report(call, period_map[call.data])


async def _show_report(call: CallbackQuery, period: str):
    today = date.today()
    if period == "today":
        date_from = today
        period_label = "Bugun"
    elif period == "week":
        date_from = today - timedelta(days=7)
        period_label = "Hafta"
    else:
        date_from = today - timedelta(days=30)
        period_label = "Oy"

    report = await get_finance_report(date_from.isoformat(), today.isoformat())
    revenue = report.get("revenue", 0) or 0
    expense = report.get("expense", 0) or 0
    orders = report.get("orders", 0) or 0
    profit = revenue - expense
    avg = revenue // orders if orders > 0 else 0

    text = t("finance_report", "uz",
             period=period_label,
             revenue=revenue,
             expense=expense,
             profit=profit,
             orders=orders,
             avg=avg)

    kb = _make_finance_kb()

    # Try to generate chart for week/month
    if period in ("week", "month"):
        try:
            chart_buf = await _generate_chart(date_from, today)
            if chart_buf:
                file = BufferedInputFile(chart_buf, filename="finance.png")
                await call.message.answer_photo(file, caption=text, reply_markup=kb, parse_mode="HTML")
                await call.message.delete()
                await call.answer()
                return
        except Exception:
            pass

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


async def _generate_chart(date_from: date, date_to: date) -> bytes | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        days_count = (date_to - date_from).days + 1
        data = await get_daily_finance_data(days=days_count)
        if not data:
            return None

        dates = [row["date"] for row in data]
        revenues = [row.get("revenue", 0) or 0 for row in data]
        expenses = [row.get("expense", 0) or 0 for row in data]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(dates)), revenues, label="Daromad", color="#4CAF50", alpha=0.8)
        ax.bar(range(len(dates)), expenses, label="Xarajat", color="#F44336", alpha=0.8)
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("So'm")
        ax.set_title("Moliyaviy hisobot")
        ax.legend()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except ImportError:
        return None


@router.callback_query(F.data == "fin_add_expense")
async def add_expense_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(t("expense_enter_amount", "uz"))
    await state.set_state(ExpenseFSM.enter_amount)
    await call.answer()


@router.message(ExpenseFSM.enter_amount)
async def expense_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Noto'g'ri format:")
        return
    await state.update_data(amount=amount)
    await message.answer(t("expense_enter_description", "uz"))
    await state.set_state(ExpenseFSM.enter_desc)


@router.message(ExpenseFSM.enter_desc)
async def expense_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    today = date.today().isoformat()
    await add_expense(today, "general", data["amount"], message.text)
    await state.clear()
    await message.answer(t("expense_added", "uz", amount=data["amount"], desc=message.text))
