from aiogram.fsm.state import StatesGroup, State

class WorkActivityPhotoStates(StatesGroup):
    waiting_passport_or_patent_photo = State()  # ждём фото (паспорт/патент)
    preview = State()                            # показ предпросмотра OCR-данных
