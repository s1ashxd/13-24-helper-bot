from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def notification_options_buttons(morning: bool, evening: bool):
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text=f"Уведомления утром: "
                                           f"{'включены' if morning else 'выключены'}",
                                      callback_data='change_option_morning'))
            .add(InlineKeyboardButton(text=f"Уведомления вечером: "
                                           f"{'включены' if evening else 'выключены'}",
                                      callback_data='change_option_evening'))
            .add(InlineKeyboardButton(text='Меню', callback_data='back'))
            .adjust(1).as_markup())
