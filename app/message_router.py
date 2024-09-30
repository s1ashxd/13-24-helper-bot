from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiomysql import Pool

import app.markups as markups
from app.utils.schedule_utils import get_weekly_schedule, get_daily_schedule

message_router = Router()


@message_router.message(CommandStart())
async def handle_start_message(message: Message):
    await message.answer(
        f'Я бот, упрощающий жизнь студентам университета МИРЭА группы ИКБО-13-24.\n\n'
        'Взаимодействие со мной осуществляется кнопками ниже или текстовыми командами:\n\n'
        '<i>расписание</i> или <i>распес</i> — расписание на сегодня, если сообщение отправлено раньше 19:00, иначе расписание на завтра\n'
        '/today — расписание на сегодня\n'
        '/tomorrow — расписание на завтра\n'
        '/week — расписание на текущую неделю\n'
        '/notifications — параметры уведомлений',
        reply_markup=markups.start_buttons()
    )
    return


@message_router.message(F.text.lower() == 'распес')
@message_router.message(F.text.lower() == 'расписание')
@message_router.message(Command('today'))
@message_router.message(Command('tomorrow'))
async def handle_flexible_schedule(message: Message, database_pool: Pool):
    day = datetime.today()
    if message.text.startswith('/tomorrow') or \
            (not message.text.startswith('/') and day.hour > 18):
        day += timedelta(days=1)
    raw = await get_daily_schedule(database_pool, day)
    if len(raw) == 0:
        await message.answer('Выбранный вами день — выходной!')
    else:
        await message.answer(raw)


@message_router.message(Command('week'))
async def handle_week_schedule_message(message: Message, database_pool: Pool):
    raw = await get_weekly_schedule(database_pool, datetime.today())
    if len(raw) == 0:
        await message.answer('На текущей неделе занятий нет!')
        return
    await message.answer(raw)


@message_router.message(Command('notifications'))
async def handle_notification_options(message: Message, state: FSMContext, bot: Bot):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if message.chat.type in (ChatType.SUPERGROUP, ChatType.GROUP) and \
            member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
        await message.answer('Использование панели уведомлений разрешено только администраторам чата')
        return
    data = await state.get_data()
    await message.answer('Выберите когда вы хотите получать уведомления с расписанием.\n'
                         '<i>Сообщения будут приходить в топик, из которого была вызвана команда, если бот находится в супергруппе.</i>\n\n'
                         'Если уведомления утром включены, ежедневно в 7:00 будет приходить уведомление '
                         'с расписанием на текущий день\n'
                         'Если уведомления вечером включены, ежедневно в 19:00 будет приходить уведомление'
                         'с расписанием на следующий день',
                         reply_markup=markups.notification_options_buttons(
                             morning='morning_job_id' in data and data['morning_job_id'] is not None,
                             evening='evening_job_id' in data and data['evening_job_id'] is not None,
                         ))
