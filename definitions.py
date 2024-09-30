import logging
from os import path

ROOT_DIR = path.dirname(path.abspath(__file__))
DB_FILE_PATH = path.join(ROOT_DIR, 'app', 'database' 'database.db')

WEEKDAY_NAMES = ['Понедельник',
                 'Вторник',
                 'Среда',
                 'Четверг',
                 'Пятница',
                 'Суббота',
                 'Воскресенье']

LESSON_TYPES = {
    'ПР': 'Семинар',
    'ЛК': 'Лекция',
    'ЛАБ': 'Лабораторная'
}
LESSON_INTERVALS = {
    'ПР': 2,
    'ЛК': 2,
    'ЛАБ': 4
}

LOGGER = logging.getLogger('main')
