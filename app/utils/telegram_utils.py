from aiogram.types import Message, CallbackQuery


def create_universal_answerer(message: Message = None, callback: CallbackQuery = None):
    if message is not None:
        async def func(text: str):
            await message.answer(text)

        return func
    if callback is not None:
        async def func(text: str):
            await callback.message.answer(text)
            await callback.answer()

        return func
    return None
