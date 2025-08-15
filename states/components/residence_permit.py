from aiogram.fsm.state import State, StatesGroup


class ResidencePermitDataStates(StatesGroup):
    """States for handling residence reason patent input"""

    choose_photo_or_manual = State()
    serial_number = State()
    issue_date = State()
