from aiogram.fsm.state import State, StatesGroup


class PassportManualStates(StatesGroup):
    """States for manual passport handling"""

    full_name_input = State()
    birth_date_input = State()
    citizenship_input = State()
    passport_serial_number_input = State()
    passport_issue_date_input = State()
    passport_expiry_date_input = State()
    passport_issue_place_input = State()
