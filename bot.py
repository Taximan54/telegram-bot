import asyncio
import json
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart

TOKEN = "8770383990:AAH6t8cdpDYpiKLibUhcMQCiUCA1nlRvfIc"

dp = Dispatcher()

PRICE_PER_NIGHT = 70
FILE = "bookings.json"

user_states = {}  # хранит выбор пользователя

# ---------- ЗАГРУЗКА ----------
def load_bookings():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_bookings(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

bookings = load_bookings()

# ---------- ПРОВЕРКА ----------
def is_busy(day):
    return any(b["day"] == day for b in bookings)

# ---------- КАЛЕНДАРЬ ----------
def get_calendar():
    buttons = []

    for i in range(1, 15):
        if is_busy(i):
            text = f"❌ {i}"
            callback = "busy"
        else:
            text = f"{i}"
            callback = f"day_{i}"

        buttons.append(InlineKeyboardButton(text=text, callback_data=callback))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        buttons[:5],
        buttons[5:10],
        buttons[10:]
    ])
    return kb

# ---------- СТАРТ ----------
@dp.message(CommandStart())
async def start(message: Message):
    kb = [
        [types.KeyboardButton(text="📅 Забронировать")],
        [types.KeyboardButton(text="💰 Цена")],
        [types.KeyboardButton(text="📞 Связаться")]
    ]

    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(
        "🏠 *Добро пожаловать!*\n\n"
        "✨ Квартира посуточно\n"
        "💸 70€ / ночь\n\n"
        "Выбери действие 👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ---------- КНОПКИ ----------
@dp.message(lambda m: m.text == "💰 Цена")
async def price(message: Message):
    await message.answer("💸 70€ / ночь")

@dp.message(lambda m: m.text == "📞 Связаться")
async def contact(message: Message):
    await message.answer("Напиши: https://t.me/@Taximan54")

@dp.message(lambda m: m.text == "📅 Забронировать")
async def booking(message: Message):
    user_states[message.from_user.id] = {}
    await message.answer("📅 Выбери дату заезда:", reply_markup=get_calendar())

# ---------- ЗАНЯТО ----------
@dp.callback_query(lambda c: c.data == "busy")
async def busy(callback: CallbackQuery):
    await callback.answer("❌ Эта дата занята", show_alert=True)

# ---------- ВЫБОР ДАТ ----------
@dp.callback_query(lambda c: c.data.startswith("day_"))
async def select_day(callback: CallbackQuery):
    user_id = callback.from_user.id
    day = int(callback.data.split("_")[1])

    state = user_states.get(user_id, {})

    # первый клик = заезд
    if "checkin" not in state:
        state["checkin"] = day
        user_states[user_id] = state
        await callback.message.answer(f"📅 Заезд: {day}\nТеперь выбери дату выезда")
        await callback.answer()
        return

    # второй клик = выезд
    checkin = state["checkin"]

    if day <= checkin:
        await callback.answer("❌ Выезд должен быть позже", show_alert=True)
        return

    # проверка занятости диапазона
    for d in range(checkin, day):
        if is_busy(d):
            await callback.answer("❌ В диапазоне есть занятые даты", show_alert=True)
            return

    # сохраняем
    for d in range(checkin, day):
        bookings.append({"day": d})

    save_bookings(bookings)

    nights = day - checkin
    total = nights * PRICE_PER_NIGHT

    await callback.message.answer(
        f"✅ Бронь подтверждена!\n\n"
        f"📅 {checkin} → {day}\n"
        f"🌙 Ночей: {nights}\n"
        f"💸 Сумма: {total}€"
    )

    user_states[user_id] = {}
    await callback.answer()

# ---------- ЗАПУСК ----------
async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())