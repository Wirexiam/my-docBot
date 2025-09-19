from aiogram.fsm.state import State, StatesGroup


class ResidenceReasonPatentStates(StatesGroup):
    """States for handling residence reason patent input"""

    choose_photo_or_manual = State()
    patient_numper = State()
    issue_date = State()
