from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiomysql import Pool
from apscheduler_di import ContextSchedulerDecorator

import app.markups as markups
from app.markups.back_buttons import back_button
from app.tasks import notify_cron_task
from app.utils.schedule_utils import get_daily_schedule, get_weekly_schedule

callback_router = Router()


@callback_router.callback_query(F.data == 'back')
async def handle_back_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        f'Я бот, упрощающий жизнь студентам университета МИРЭА группы ИКБО-13-24.\n\n'
        'Взаимодействие со мной осуществляется кнопками ниже или текстовыми командами:\n\n'
        '<i>расписание</i> или <i>распес</i> — расписание на сегодня, если сообщение отправлено раньше 19:00, иначе расписание на завтра\n'
        '/today — расписание на сегодня\n'
        '/tomorrow — расписание на завтра\n'
        '/week — расписание на текущую неделю\n'
        '/notifications — параметры уведомлений',
        reply_markup=markups.start_buttons()
    )
    await callback.answer()


@callback_router.callback_query(F.data == 'today_schedule')
@callback_router.callback_query(F.data == 'tomorrow_schedule')
async def handle_daily_schedule_callback(callback: CallbackQuery, database_pool: Pool):
    day = datetime.now()
    if callback.data == 'tomorrow_schedule':
        day += timedelta(days=1)
    raw = await get_daily_schedule(database_pool, day)
    if len(raw) == 0:
        await callback.message.answer('Выбранный вами день — выходной!')
    else:
        await callback.message.answer(raw)
    await callback.answer()


@callback_router.callback_query(F.data == 'current_week_schedule')
@callback_router.callback_query(F.data == 'next_week_schedule')
async def handle_week_schedule_callback(callback: CallbackQuery, database_pool: Pool):
    if callback.data == 'current_week_schedule':
        raw = await get_weekly_schedule(database_pool, datetime.today())
    else:
        raw = await get_weekly_schedule(database_pool, datetime.today() + timedelta(weeks=1))
    if len(raw) == 0:
        await callback.message.answer('На текущей неделе занятий нет!')
        return
    await callback.message.answer(raw)
    await callback.answer()


@callback_router.callback_query(F.data == 'notification_options')
@callback_router.callback_query(F.data == 'change_option_morning')
@callback_router.callback_query(F.data == 'change_option_evening')
async def handle_notification_options(callback: CallbackQuery, state: FSMContext,
                                      scheduler: ContextSchedulerDecorator, bot: Bot):
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if callback.message.chat.type in (ChatType.SUPERGROUP, ChatType.GROUP) and \
            member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
        await callback.message.edit_text(
            'Использование панели уведомлений разрешено только администраторам чата',
            reply_markup=back_button()
        )
        await callback.answer()
        return
    data = await state.get_data()
    if callback.data == 'change_option_morning':
        if 'morning_job_id' not in data or data['morning_job_id'] is None:
            job = scheduler.add_job(
                notify_cron_task,
                trigger='cron',
                hour=7,
                minute=0,
                start_date=datetime.now(),
                kwargs={
                    'chat_id': callback.message.chat.id,
                    'thread_id': callback.message.message_thread_id or 0,
                    'morning_cron': True
                }
            )
            data = await state.update_data(morning_job_id=job.id)
        else:
            scheduler.remove_job(data['morning_job_id'])
            data = await state.update_data(morning_job_id=None)
    elif callback.data == 'change_option_evening':
        if 'evening_job_id' not in data or data['evening_job_id'] is None:
            job = scheduler.add_job(
                notify_cron_task,
                trigger='cron',
                hour=19,
                minute=0,
                start_date=datetime.now(),
                kwargs={
                    'chat_id': callback.message.chat.id,
                    'thread_id': callback.message.message_thread_id or 0,
                    'morning_cron': False
                }
            )
            data = await state.update_data(evening_job_id=job.id)
        else:
            scheduler.remove_job(data['evening_job_id'])
            data = await state.update_data(evening_job_id=None)
    await callback.message.edit_text('Выберите когда вы хотите получать уведомления с расписанием.\n'
                                     '<i>Сообщения будут приходить в топик, из которого была вызвана команда, если бот находится в супергруппе.</i>\n\n'
                                     'Если уведомления утром включены, ежедневно в 7:00 будет приходить уведомление '
                                     'с расписанием на текущий день\n'
                                     'Если уведомления вечером включены, ежедневно в 19:00 будет приходить уведомление'
                                     'с расписанием на следующий день',
                                     reply_markup=markups.notification_options_buttons(
                                         morning='morning_job_id' in data and data['morning_job_id'] is not None,
                                         evening='evening_job_id' in data and data['evening_job_id'] is not None,
                                     ))
    await callback.answer()
