from datetime import datetime, timedelta

from aiomysql import Pool, DictCursor

from app.database.handles import get_all_lessons, get_all_weeks, get_all_metadata
from definitions import LESSON_TYPES, WEEKDAY_NAMES, LESSON_INTERVALS


async def get_daily_schedule(database_pool: Pool, day: datetime):
    async with database_pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cursor:
            all_schedule = await get_all_lessons(cursor)
            all_metadata = await get_all_metadata(cursor)
            all_weeks = await get_all_weeks(cursor)
    week_num = 0
    for week in all_weeks:
        if week['start'] <= datetime.date(day) <= week['end']:
            week_num = week['id']
    return generate_raw_daily(all_schedule, all_metadata, week_num, day)


def generate_raw_daily(all_schedule: list[dict], all_metadata: list[dict], week_num: int, day: datetime):
    lesson_html_list = []
    maybe_outdated = False
    for row in all_schedule:
        if int(row['odd_week']) == week_num % LESSON_INTERVALS[row['category']] and \
                row['start'].weekday() == day.weekday():
            raw = (
                f"<u>Пара №{row['serial_number']} ({row['start'].strftime('%H:%M')} - {row['end'].strftime('%H:%M')})</u>\n"
                f"<b>{row['name']}</b> ({LESSON_TYPES[row['category']]})\n"
                f"<i>{row['location'].strip()}</i>")
            if len(row['description']) > 0:
                raw += f"<i>\n{row['description']}</i>"
            if day > row['repeat_until']:
                maybe_outdated = True
            lesson_html_list.append(raw)
    metadata = None
    for row in all_metadata:
        if row['start'] <= datetime.date(day) <= row['end']:
            metadata = row['summary']
            break
    if len(lesson_html_list) == 0:
        return ''
    raw = f'Расписание на <b>{WEEKDAY_NAMES[day.weekday()]}</b>.\n'
    if maybe_outdated:
        raw += '<i>Расписание может быть неточным.<i/>\n'
    if metadata is not None and len(metadata) > 0:
        raw += f'<b>{metadata}</b>.\n'
    raw += ('\n'
            f'{'\n\n'.join(lesson_html_list)}')
    return raw


async def get_weekly_schedule(database_pool: Pool, day_on_week: datetime):
    async with database_pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cursor:
            all_weeks = await get_all_weeks(cursor)
            all_schedule = await get_all_lessons(cursor)
            all_metadata = await get_all_metadata(cursor)
    week_num = 0
    for week in all_weeks:
        if week['start'] <= datetime.date(day_on_week) <= week['end']:
            week_num = week['id']
    week_day = day_on_week - timedelta(days=day_on_week.weekday())
    day_html_list = []
    for i in range(6):
        res = generate_raw_daily(all_schedule, all_metadata, week_num, week_day)
        if len(res) == 0:
            day_html_list.append(f"Занятий в <b>{WEEKDAY_NAMES[i]}</b> нет.")
        else:
            day_html_list.append(res)
        week_day += timedelta(days=1)
    return (f'Неделя <b>#{week_num}</b>\n\n'
            f'{'\n\n~~~~~~~~\n\n'.join(day_html_list)}')
