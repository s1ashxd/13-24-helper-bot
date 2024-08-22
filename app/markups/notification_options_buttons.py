from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def notification_options_buttons(morning: bool, evening: bool, back_button: bool):
    ikb = (InlineKeyboardBuilder()
           .add(InlineKeyboardButton(text=f"Уведомления утром: "
                                          f"{'включены' if morning else 'выключены'}",
                                     callback_data='change_option_morning'))
           .add(InlineKeyboardButton(text=f"Уведомления вечером: "
                                          f"{'включены' if evening else 'выключены'}",
                                     callback_data='change_option_evening')))
    if back_button:
        ikb.add(InlineKeyboardButton(text='Назад', callback_data='back'))
    return ikb.adjust(1).as_markup()
