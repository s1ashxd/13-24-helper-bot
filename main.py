import logging
from asyncio import run, get_event_loop
from datetime import datetime
from os import environ, getenv
from time import tzset

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiomysql import create_pool, Pool
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler_di import ContextSchedulerDecorator
from httpx import AsyncClient
from redis.asyncio import Redis

from app.callback_router import callback_router
from app.database.migrate import migrate
from app.message_router import message_router
from app.tasks.schedule_update_cron import schedule_update_cron
from definitions import LOGGER


async def main():
    redis = Redis(
        host=getenv('REDIS_HOST'),
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
                host=getenv('REDIS_HOST'),
                jobs_key='jobs_all',
                run_times_key='jobs_run_times',
                db=2,
            )
        }
    ))
    api_client = AsyncClient()
    database_pool = await create_pool(host=getenv('MARIADB_HOST'),
                                      port=int(getenv('MARIADB_PORT')),
                                      user=getenv('MARIADB_USER'),
                                      password=getenv('MARIADB_PASSWORD'),
                                      db=getenv('MARIADB_DATABASE'),
                                      loop=get_event_loop())
    try:
        await migrate(database_pool)
        await schedule_update_cron(api_client, redis, database_pool, force=True)
        scheduler.ctx.add_instance(bot, declared_class=Bot)
        scheduler.ctx.add_instance(api_client, declared_class=AsyncClient)
        scheduler.ctx.add_instance(redis, declared_class=Redis)
        scheduler.ctx.add_instance(database_pool, declared_class=Pool)
        prev_job_id = await redis.get('schedule_update_job_id')
        if prev_job_id is None:
            job = scheduler.add_job(
                schedule_update_cron,
                trigger='cron',
                hour=19,
                minute=30,
                start_date=datetime.now(),
                kwargs={
                    'force': False
                }
            )
            await redis.set('schedule_update_job_id', job.id)
        scheduler.start()
        dispatcher.include_routers(message_router, callback_router)
        await dispatcher.start_polling(bot,
                                       scheduler=scheduler,
                                       api_client=api_client,
                                       database_pool=database_pool,
                                       redis=redis)
    finally:
        await api_client.aclose()
        database_pool.close()
        await database_pool.wait_closed()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - '
                                                  '%(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - '
                                                  '%(message)s')
    environ['TZ'] = 'Europe/Moscow'
    tzset()
    try:
        run(main())
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info('bot stopped')
