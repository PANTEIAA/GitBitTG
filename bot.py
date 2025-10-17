import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 📧 Настройки почты Яндекс
EMAIL_SENDER = "artempanteleev83@yandex.ru"           # твоя Яндекс-почта
EMAIL_PASSWORD = "dejedpgrhemgqxnp"                   # пароль приложения
EMAIL_RECEIVER = "artempanteleev2004@gmail.com"       # куда отправлять заявки

def send_email(order_text: str):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "Новая заявка из Telegram бота"
    msg.attach(MIMEText(order_text, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.yandex.ru", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Письмо успешно отправлено!")
    except Exception as e:
        print("⚠️ Ошибка при отправке письма:", e)

# 🔹 Твой токен
TOKEN = "8358423233:AAFyUlknvq846kwCZrIyaiyK85g0YlLda4c"

# 🔹 Создаём бота и диспетчер
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# 🔹 FSM — машина состояний
class Order(StatesGroup):
    name = State()
    phone = State()
    product = State()
    quantity = State()

# 🔹 Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📦 Список товаров", "📝 Оформить заявку")
    await message.answer("👋 Привет! Я бот-магазин.\nВыбери действие ниже:", reply_markup=keyboard)

# 🔹 Список товаров
@dp.message(lambda message: message.text == "📦 Список товаров")
async def show_products(message: types.Message):
    await message.answer("Вот список доступных товаров:\n\n1️⃣ Товар A\n2️⃣ Товар B\n3️⃣ Товар C")

# 🔹 Начало оформления заявки
@dp.message(lambda message: message.text == "📝 Оформить заявку")
async def create_order(message: types.Message, state: FSMContext):
    await state.set_state(Order.name)
    await message.answer("Введите ваше имя:")

# 🔹 Шаг 1 — имя
@dp.message(Order.name)
async def process_name(message: types.Message, state: FSMContext):
    if not message.text.isalpha() or len(message.text) < 2:
        await message.answer("⚠️ Пожалуйста, введите корректное имя (только буквы, минимум 2 символа).")
        return
    await state.update_data(name=message.text)
    await state.set_state(Order.phone)
    await message.answer("Введите ваш номер телефона:")

# 🔹 Шаг 2 — телефон
@dp.message(Order.phone)
async def process_phone(message: types.Message, state: FSMContext):
    digits = ''.join(filter(str.isdigit, message.text))
    if len(digits) < 10:
        await message.answer("⚠️ Пожалуйста, введите корректный номер телефона (минимум 10 цифр).")
        return
    await state.update_data(phone=digits)
    await state.set_state(Order.product)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Товар A", "Товар B", "Товар C")
    await message.answer("Выберите товар из списка:", reply_markup=keyboard)

# 🔹 Шаг 3 — товар
@dp.message(Order.product)
async def process_product(message: types.Message, state: FSMContext):
    valid_products = ["Товар A", "Товар B", "Товар C"]
    if message.text not in valid_products:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*valid_products)
        await message.answer("⚠️ Ошибка! Выберите товар из кнопок ниже.", reply_markup=keyboard)
        return
    await state.update_data(product=message.text)
    await state.set_state(Order.quantity)
    await message.answer("Введите количество товара:")

# 🔹 Шаг 4 — количество и завершение
@dp.message(Order.quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("⚠️ Введите корректное количество (число больше 0).")
        return
    await state.update_data(quantity=int(message.text))
    data = await state.get_data()
    await state.clear()
    order_text = (
        f"🆕 Новая заявка!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📦 Товар: {data['product']}\n"
        f"🔢 Количество: {data['quantity']}"
    )
    await message.answer("✅ Ваша заявка отправлена! Мы скоро с вами свяжемся.")
    send_email(order_text)

# 🔹 Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
