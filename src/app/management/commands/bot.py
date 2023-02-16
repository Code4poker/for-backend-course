from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, types, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.models import *
from django.core.management.base import BaseCommand
from channels.db import database_sync_to_async

token = "5647374914:AAGy8zHi4JUS5Ppu5LRlrG9MGkT0LtWfZ90"
storage = MemoryStorage()
bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)


class Condition(StatesGroup):
    user_name_surname = State()
    user_email = State()
    user_date_of_birth = State()
    user_phone = State()
    write_in_db = State()


@database_sync_to_async
def make_user(name, surname, email, date_of_birth):
    return User.objects.create(name=name, surname=surname, email=email, date_of_birth=date_of_birth)


@dp.message_handler(state="*", commands='start')
async def asking_name_and_surname(message: types.Message):
    await bot.send_message(message.chat.id, "Введите имя и фамилию через пробел")
    await Condition.user_name_surname.set()


@dp.message_handler(state=Condition.user_name_surname)
async def input_name_processing(message: types.Message, state: FSMContext):
    await state.update_data(user_name_surname=message.text.lower().split())
    await bot.send_message(message.chat.id, "Введите email")
    await Condition.user_email.set()


@dp.message_handler(state=Condition.user_email)
async def input_email_processing(message: types.Message, state: FSMContext):
    await state.update_data(user_email=message.text.lower().strip())
    await bot.send_message(message.chat.id, "Введите дату вашшего рождения по следующему формату: yyyy-mm-dd")
    await Condition.user_date_of_birth.set()


@dp.message_handler(state=Condition.user_date_of_birth)
async def input_date_processing(message: types.Message, state: FSMContext):
    await state.update_data(user_date_of_birth=message.text)
    await bot.send_message(message.chat.id, "Данные записаны, спасибо.\n "
                                            "Нажмите на команду /set_phone для записи номера телефона")
    await Condition.write_in_db.set()


@dp.message_handler(state="*", commands="set_phone")
async def asking_phone_number(message: types.Message):
    await bot.send_message(message.chat.id, 'Введите номер телефона')
    await Condition.user_phone.set()


@dp.message_handler(state=Condition.user_phone)
async def phone_number_processing(message: types.Message, state: FSMContext):
    await state.update_data(user_phone=message.text)
    await Condition.write_in_db.set()


@dp.message_handler(state=Condition.write_in_db, commands="me")
async def recording_information(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        name = data.get("user_name_surname")[0]
        surname = data.get("user_name_surname")[1]
        phone_number = data.get("user_phone")
        email = data.get("user_email")
        date_of_birth = data.get("user_date_of_birth")
    except TypeError:
        await bot.send_message(message.chat.id, "Упс... Похоже у нас нехватает данных о вас.\n"
                                                "Вызовите команду /start для ввода личных данных\n"
                                                "Или команду /set_phone для ввода номера телефона")
        await Condition.next()
    else:
        await make_user(name, surname, email, date_of_birth)
        await bot.send_message(message.chat.id, f"Имя и фамилия: {name} {surname}\n"
                                                f"Email: {email}\n"
                                                f"Номер телефона: {phone_number}\n"
                                                f"Дата рождения: {date_of_birth}")


# @dp.message_handler(state="*", commands="endpoint_me")
# async def processing_endpoint_me_command(message: types.Message, state: FSMContext):
#     await bot.send_message(message.chat.id, )


class Command(BaseCommand):
    help = 'Implemented to Django application telegram bot setup command'

    def handle(self, *args, **kwargs):
        executor.start_polling(dp, skip_updates=True)
