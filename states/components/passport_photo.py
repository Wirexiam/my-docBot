from aiogram.fsm.state import State, StatesGroup


class PassportPhotoStates(StatesGroup):
    waiting_old_passport_photo = State()  # ждём фото СТАРОГО
    waiting_new_passport_photo = State()  # ждём фото НОВОГО
    waiting_passport_photo = State()
