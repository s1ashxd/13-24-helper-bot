import logging
from asyncio import run
from os import getenv

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler_di import ContextSchedulerDecorator
from dotenv import load_dotenv
from httpx import AsyncClient
from redis.asyncio import Redis

from app.callback_router import callback_router
from app.message_router import message_router


async def main():
    redis = Redis(
        host=getenv("REDIS_HOST"),
        db=1
    )
    bot = Bot(
        token=getenv('BOT_TOKEN'),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dispatcher = Dispatcher(storage=RedisStorage(redis=redis))
    scheduler = ContextSchedulerDecorator(AsyncIOScheduler(
        timezone='Europe/Moscow',
        jobstores={
            'default': RedisJobStore(
                host=getenv("REDIS_HOST"),
                jobs_key='jobs_all',
                run_times_key='jobs_run_times',
                db=2,
            )
        }
    ))
    api_client = AsyncClient(base_url='https://mirea.xyz/api/v1.3/')

    try:
        scheduler.ctx.add_instance(bot, declared_class=Bot)
        scheduler.ctx.add_instance(api_client, declared_class=AsyncClient)
        scheduler.start()
        dispatcher.include_routers(message_router, callback_router)
        await dispatcher.start_polling(bot, scheduler=scheduler, api_client=api_client)
    finally:
        await api_client.aclose()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - '
                                                   '%(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - '
                                                   '%(message)s')
    load_dotenv()
    try:
        run(main())
        logger.info('bot started')
    except (KeyboardInterrupt, SystemExit):
        logger.info('bot stopped')
