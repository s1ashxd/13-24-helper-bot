from datetime import timedelta, datetime

from aiogram import Bot
from aiomysql import Pool

from app.utils.schedule_utils import get_daily_schedule


async def notify_cron_task(
        bot: Bot,
        chat_id: int,
        morning_cron: bool,
        database_pool: Pool,
        thread_id: int,
):
    day = datetime.now()
    if not morning_cron:
        day += timedelta(days=1)
    raw = await get_daily_schedule(database_pool, day)
    if len(raw) > 0:
        await bot.send_message(chat_id, raw, message_thread_id=thread_id or None)
