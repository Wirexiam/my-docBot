from aiogram.fsm.state import State, StatesGroup


class ResidenceReasonChildStates(StatesGroup):
    """States for handling residence reason child input"""

    choose_photo_or_manual = State()
    child_fio = State()
    child_birth_date = State()
    child_citizenship = State()
    child_certificate_number = State()
    child_certificate_issue_place = State()
    who_for_child = State()
