from datetime import datetime, timedelta
from datetime import datetime, timedelta
from hashlib import sha256

from aiomysql import Pool, DictCursor
from httpx import AsyncClient
from icalendar import Calendar
from redis import Redis

from app.database.handles import get_all_weeks
from app.database.handles import insert_lesson
from app.database.handles import insert_metadata, insert_week, insert_subject
from definitions import LOGGER


async def schedule_update_cron(api_client: AsyncClient, redis: Redis, database_pool: Pool, force: bool):
    res = await api_client.get('https://schedule-of.mirea.ru/schedule/api/ical/1/4784')
    text = res.text
    prev_hash = await redis.get('schedule_sha256')
    current_hash = sha256(text.encode()).hexdigest()
    if force or (prev_hash is not None and prev_hash.decode() == current_hash):
        cal = Calendar.from_ical(text)
        async with database_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute('TRUNCATE lessons')
                await cursor.execute('TRUNCATE periods_metadata')
                await cursor.execute('TRUNCATE weeks')
                await conn.commit()
                for comp in cal.walk('VEVENT'):
                    if comp.get('RRULE') is None:
                        if 'неделя' in comp.get('SUMMARY'):
                            await insert_week(cursor, comp.get('DTSTART').dt, comp.get('DTEND').dt)
                        else:
                            await insert_metadata(cursor,
                                                  comp.get('DTSTART').dt,
                                                  comp.get('DTEND').dt,
                                                  str(comp.get('SUMMARY')))
                await conn.commit()
                all_weeks = await get_all_weeks(cursor)
                for comp in cal.walk('VEVENT'):
                    if comp.get('RRULE') is not None:
                        summary = str(comp.get('SUMMARY')).split(' ', 1)
                        await cursor.execute('SELECT id FROM subjects WHERE name = %s LIMIT 1', (summary[1],))
                        subject = await cursor.fetchone()
                        if subject is None:
                            desc = str(comp.get('DESCRIPTION')).strip()
                            if desc is not None and len(desc) > 0:
                                desc = desc.split('\n', 1)[0]
                                if 'Преподаватель' not in desc:
                                    desc = None
                            await insert_subject(cursor,
                                                 summary[1],
                                                 summary[0],
                                                 desc if desc is not None else '',
                                                 str(comp.get('LOCATION')))
                            subject_id = conn.insert_id()
                        else:
                            subject_id = subject['id']
                        current_time = datetime.today().replace(hour=9, minute=0)
                        dt_start = comp.get('DTSTART').dt.replace(tzinfo=None)
                        serial_number = 0
                        for i in range(7):
                            if current_time < dt_start.replace(day=current_time.day) + timedelta(
                                    minutes=45) < current_time + timedelta(hours=1, minutes=30):
                                serial_number = i + 1
                                break
                            current_time += timedelta(hours=1, minutes=30)
                            current_time += timedelta(minutes=30) if i % 2 == 1 and i < 5 else timedelta(minutes=10)
                        week_num = 0
                        for week in all_weeks:
                            if week['start'] <= datetime.date(dt_start) <= week['end']:
                                week_num = week['id']
                        await insert_lesson(cursor,
                                            subject_id,
                                            serial_number,
                                            comp.get('DTSTART').dt,
                                            comp.get('DTEND').dt,
                                            week_num % 2 == 1,
                                            comp.get('RRULE').get('UNTIL')[0])
                await conn.commit()
        await redis.set('schedule_sha256', current_hash)
        LOGGER.info('schedule updated')
        LOGGER.info(f'old hash: {prev_hash.decode()}')
        LOGGER.info(f'new hash: {current_hash}')
