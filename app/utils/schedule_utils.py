from datetime import datetime
from os import path

from httpx import AsyncClient

from definitions import ROOT_DIR, LESSON_TYPES, UNIVERSITY_GROUP


async def get_daily_schedule(api_client: AsyncClient, week: int, weekday: int) -> (str | None):
    if weekday == 6:
        return ''
    if weekday > 6:
        weekday %= 6
    res = await api_client.get(f'groups/certain?name={UNIVERSITY_GROUP}')
    if res.status_code == 404:
        return None
    json_schedule = res.json()[0]
    week_lessons_time = json_schedule['lessonsTimes']
    week_schedule = json_schedule['schedule']
    return generate_daily_response(
        week_lessons_time[weekday],
        week_schedule[weekday],
        week % 2 == 1
    )


async def get_current_week(api_client: AsyncClient) -> (int | None):
    res = await api_client.get('time/week')
    if res.status_code != 200:
        return None
    return res.json()


async def get_weekly_schedule(api_client: AsyncClient, week: int, adaptive: bool) -> (str | None):
    res = await api_client.get(f'groups/certain?name={UNIVERSITY_GROUP}')
    if res.status_code == 404:
        return None
    json_schedule = res.json()[0]
    return generate_weekly_response(
        json_schedule['lessonsTimes'],
        json_schedule['schedule'],
        week,
        adaptive
    )


def generate_daily_response(day_lessons_time: list[str], day_schedule: dict[str, any], odd_week: bool) -> str:
    lesson_data_list = day_schedule['odd' if odd_week else 'even']
    lesson_html_list = []
    with open(path.join(ROOT_DIR, 'assets', 'lesson_template.html'), 'r', encoding='UTF-8') as f:
        lesson_template = f.read()
        for i in range(len(lesson_data_list)):
            if len(lesson_data_list[i]) == 0:
                continue
            lesson = lesson_data_list[i][0]
            lesson['type'] = LESSON_TYPES[lesson['type']]
            lesson_html_list.append(
                lesson_template.format(
                    **lesson,
                    num=i + 1,
                    time=day_lessons_time[i]
                ))
        if len(lesson_html_list) == 0:
            return ''
    with open(path.join(ROOT_DIR, 'assets', 'daily_template.html'), 'r', encoding='UTF-8') as t:
        daily_template = t.read()
        return daily_template.format(day_name=day_schedule['day'], lessons='\n\n'.join(lesson_html_list))


def generate_weekly_response(week_lessons_time: list[list[str]], week_schedule: list[dict[str, any]], week: int,
                             adaptive: bool) -> str:
    day_html_list = []
    for i in range(datetime.today().weekday() if adaptive else 0, len(week_schedule)):
        res = generate_daily_response(week_lessons_time[i], week_schedule[i], week % 2 == 1)
        if res is None:
            continue
        if len(res) == 0:
            day_html_list.append(f"Занятий в <b>{week_schedule[i]['day']}</b> нет.")
            continue
        day_html_list.append(res)
    if len(day_html_list) == 0:
        return ''
    with open(path.join(ROOT_DIR, 'assets', 'weekly_template.html'), 'r', encoding='UTF-8') as f:
        weekly_template = f.read()
        return weekly_template.format(num=week, days='\n\n~~~~~~~~\n\n'.join(day_html_list))
