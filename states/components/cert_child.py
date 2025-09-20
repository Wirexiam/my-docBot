from aiogram.fsm.state import State, StatesGroup


class CertificateChildStates(StatesGroup):
    """States for handling residence reason patent input"""

    choose_photo_or_manual = State()
    child_fio = State()
    child_birth_date = State()
    child_citizenship = State()
    child_certificate_number = State()
    child_certificate_issue_place = State()
