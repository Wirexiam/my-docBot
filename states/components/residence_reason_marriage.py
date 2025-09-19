from aiogram.fsm.state import State, StatesGroup


class ResidenceReasonMarriageStates(StatesGroup):
    """States for handling residence reason patent input"""

    choose_photo_or_manual = State()
    spouse_fio = State()
    issue_date = State()
    marriage_number = State()
    issue_place = State()
