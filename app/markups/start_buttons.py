from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_buttons():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text='Расписание на сегодня', callback_data='today_schedule'))
            .add(InlineKeyboardButton(text='Расписание на завтра', callback_data='tomorrow_schedule'))
            .add(InlineKeyboardButton(text='Расписание на текущую неделю', callback_data='current_week_schedule'))
            .add(InlineKeyboardButton(text='Расписание на следующую неделю', callback_data='next_week_schedule'))
            .add(InlineKeyboardButton(text='Параметры уведомлений', callback_data='notification_options'))
            .adjust(1)
            .as_markup())
