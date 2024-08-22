from datetime import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import AsyncClient

import app.markups as markups
from app.utils.schedule_utils import get_current_week, get_weekly_schedule, get_daily_schedule
from definitions import UNIVERSITY_GROUP

message_router = Router()


@message_router.message(CommandStart())
async def handle_start_message(message: Message):
    await message.answer(
        f'Я бот, упрощающий жизнь студентам университета МИРЭА группы {UNIVERSITY_GROUP}.\n\n'
        'Взаимодействие со мной осуществляется кнопками ниже или текстовыми командами:\n\n'
        '<i>расписание</i> или <i>распес</i> — расписание на сегодня, если сообщение отправлено раньше 19:00, иначе расписание на завтра\n'
        '/today — расписание на сегодня\n'
        '/tomorrow — расписание на завтра\n'
        '/week — расписание на текущую неделю\n'
        '/notifications — параметры уведомлений',
        reply_markup=markups.start_buttons()
    )
    return


@message_router.message(F.text.contains('распес'))
@message_router.message(F.text.contains('расписание'))
async def handle_flexible_schedule(message: Message, api_client: AsyncClient):
    week = await get_current_week(api_client)
    if week is None:
        await message.answer('Произошла ошибка API')
        return
    weekday = datetime.today().weekday()
    if datetime.now().hour > 18:
        weekday += 1
    raw = await get_daily_schedule(
        api_client,
        week,
        weekday
    )
    if raw is None:
        await message.answer('Учеба в вашей группе еще не началась!')
    elif len(raw) == 0:
        await message.answer('Выбранный вами день — выходной!')
    else:
        await message.answer(raw)


@message_router.message(Command('today'))
@message_router.message(Command('tomorrow'))
async def handle_daily_schedule_message(message: Message, api_client: AsyncClient):
    week = await get_current_week(api_client)
    if week is None:
        await message.answer('Произошла ошибка API')
        return
    weekday = datetime.today().weekday()
    if message.text == '/tomorrow':
        weekday += 1
    raw = await get_daily_schedule(
        api_client,
        week,
        weekday
    )
    if raw is None:
        await message.answer('Учеба в вашей группе еще не началась!')
    elif len(raw) == 0:
        await message.answer('Выбранный вами день — выходной!')
    else:
        await message.answer(raw)


@message_router.message(Command('week'))
async def handle_week_schedule_message(message: Message, api_client: AsyncClient):
    week = await get_current_week(api_client)
    if week is None:
        await message.answer('Произошла ошибка API')
        return
    raw = await get_weekly_schedule(
        api_client,
        week,
        adaptive=True
    )
    if raw is None:
        await message.answer('Учеба в вашей группе еще не началась!')
        return
    if len(raw) == 0:
        await message.answer('На текущей неделе занятий нет!')
        return
    await message.answer(raw)


@message_router.message(Command('notifications'))
async def handle_notification_options(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer('Выберите когда вы хотите получать уведомления с расписанием.\n\n'
                         'Если уведомления утром включены, ежедневно в 7:00 будет приходить уведомление '
                         'с расписанием на текущий день\n'
                         'Если уведомления вечером включены, ежедневно в 19:00 будет приходить уведомление'
                         'с расписанием на следующий день',
                         reply_markup=markups.notification_options_buttons(
                             morning='morning_job_id' in data and data['morning_job_id'] is not None,
                             evening='evening_job_id' in data and data['evening_job_id'] is not None,
                             back_button=False
                         ))
