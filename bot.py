import asyncio
import re
import logging
from yapsl import SmsType, SmsGateway
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

# Настройки для бота
BOT_TOKEN = ''  # Замените на свой токен
SMS_GATEWAY_PORT = '/dev/ttyUSB0'  # Порт SMS-шлюза

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализация SMS-шлюза
sms_gateway = SmsGateway(SMS_GATEWAY_PORT, verbose=False)

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Шаблон для проверки номера телефона
PHONE_NUMBER_PATTERN = r'^7\d{10}$'


@dp.message_handler(commands=['start', 'help'])
async def handle_start_help(message: types.Message):
    """
    Обработчик команды /start или /help.
    Отправляет информационное сообщение о функциях бота.
    """
    text = (
        "Привет! Я бот для отправки SMS. Вот список доступных команд:\n\n"
        "/send - отправить SMS на номер\n"
        "/help - показать это сообщение снова"
    )
    await message.answer(text)


@dp.message_handler(commands=['send'])
async def handle_send_command(message: types.Message, state: FSMContext):
    """
    Обработчик команды /send.
    Запрашивает у пользователя номер телефона и текст сообщения.
    """
    await message.answer("Введите номер телефона (например, 71234567890):")
    await state.set_state("wait_for_phone_number")


@dp.message_handler(state="wait_for_phone_number")
async def handle_phone_number(message: types.Message, state: FSMContext):
    """
    Обработчик ввода номера телефона.
    Проверяет введенный номер и сохраняет его в контексте состояния.
    """
    phone_number = message.text.strip()

    if not re.match(PHONE_NUMBER_PATTERN, phone_number):
        await message.answer("Неправильный формат номера. Введите номер телефона еще раз.")
        return

    await state.update_data(phone_number=phone_number)
    await message.answer("Введите текст сообщения:")
    await state.set_state("wait_for_message_text")


@dp.message_handler(state="wait_for_message_text")
async def handle_message_text(message: types.Message, state: FSMContext):
    """
    Обработчик ввода текста сообщения.
    Отправляет SMS с введенными данными и сообщает об успешной отправке.
    """
    data = await state.get_data()
    phone_number = data.get("phone_number")
    message_text = message.text.strip()

    # Опционально: Проверка, подключен ли SMS-шлюз к сети
    if not sms_gateway.is_connected():
        await message.answer("SMS-шлюз не подключен к сети.")
        return

    # Отправка SMS
    try:
        sms_gateway.send(phone_number, message_text)
        await message.answer("Сообщение успешно отправлено!")
    except Exception as e:
        await message.answer(f"Ошибка при отправке сообщения: {str(e)}")

    await state.finish()


@dp.message_handler()
async def handle_invalid_commands(message: types.Message):
    """
    Обработчик некорректных команд.
    """
    await message.answer("Некорректная команда. Введите /help, чтобы увидеть список доступных команд.")


if __name__ == '__main__':
    # Запуск бота
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(dp.start_polling())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(dp.bot.close())
        loop.close()
