from datetime import datetime

from aiomysql import Cursor


async def get_all_lessons(cursor: Cursor) -> list[dict]:
    await cursor.execute('SELECT * FROM lessons '
                         'LEFT JOIN subjects ON subjects.id = lessons.subject_id')
    all_schedule = await cursor.fetchall()
    return all_schedule


async def get_all_weeks(cursor: Cursor) -> list[dict]:
    await cursor.execute('SELECT * FROM weeks')
    all_weeks = await cursor.fetchall()
    return all_weeks


async def get_all_metadata(cursor: Cursor) -> list[dict]:
    await cursor.execute('SELECT * FROM periods_metadata')
    all_periods = await cursor.fetchall()
    return all_periods


async def get_all_subjects(cursor: Cursor) -> list[dict]:
    await cursor.execute('SELECT * FROM subjects')
    all_subjects = await cursor.fetchall()
    return all_subjects


async def get_subject_by_name(cursor: Cursor, name: str) -> dict:
    await cursor.execute('SELECT * FROM subjects WHERE name = %s LIMIT 1', (name,))
    subject = await cursor.fetchall()
    return subject[0] if len(subject) > 0 else None


async def insert_lesson(cursor: Cursor, subject_id: int, serial_number: int, dt_start: datetime, dt_end: datetime,
                        odd_week: bool, dt_until: datetime):
    await cursor.execute(
        '''
           INSERT INTO lessons (
               subject_id,
               serial_number,
               start, 
               end, 
               odd_week,
               repeat_until
           ) VALUES (%s, %s, %s, %s, %s, %s)
       ''',
        (
            subject_id,
            serial_number,
            dt_start.strftime('%Y-%m-%d %H:%M'),
            dt_end.strftime('%Y-%m-%d %H:%M'),
            odd_week,
            dt_until.strftime('%Y-%m-%d')
        )
    )


async def insert_week(cursor: Cursor, dt_start: datetime, dt_end: datetime):
    await cursor.execute(
        'INSERT INTO weeks (start, end) VALUES (%s, %s)',
        (dt_start.strftime('%Y-%m-%d %H:%M'), dt_end.strftime('%Y-%m-%d %H:%M'))
    )


async def insert_metadata(cursor: Cursor, dt_start: datetime, dt_end: datetime, summary: str):
    await cursor.execute(
        'INSERT INTO periods_metadata (start, end, summary) VALUES (%s, %s, %s)',
        (
            dt_start.strftime('%Y-%m-%d'),
            dt_end.strftime('%Y-%m-%d'),
            str(summary)
        )
    )


async def insert_subject(cursor: Cursor, name: str, category: str, description: str, location: str):
    await cursor.execute(
        '''
            INSERT INTO subjects (
                name,
                category,
                description, 
                location
            ) VALUES (%s, %s, %s, %s)
        ''', [
            str(name),
            str(category),
            str(description),
            str(location)
        ]
    )
