from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_button():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text='Меню', callback_data='back'))
            .adjust(1)
            .as_markup())
