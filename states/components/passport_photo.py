from aiogram.fsm.state import State, StatesGroup

class PassportPhotoStates(StatesGroup):
    """Состояния ветки 'паспорт по фото'"""
    waiting_passport_photo = State()
