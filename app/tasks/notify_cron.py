from datetime import datetime

from aiogram import Bot
from httpx import AsyncClient

from app.utils.schedule_utils import get_current_week, get_daily_schedule


async def notify_cron_task(bot: Bot, api_client: AsyncClient, chat_id: int, morning_cron: bool):
    week = await get_current_week(api_client)
    if week is None:
        await bot.send_message(chat_id, 'Во время выполнения cron-задачи произошла ошибка API')
        return
    weekday = datetime.today().weekday()
    if not morning_cron:
        weekday += 1
    raw = await get_daily_schedule(
        api_client,
        week,
        weekday
    )
    if raw is not None:
        await bot.send_message(chat_id, raw)
