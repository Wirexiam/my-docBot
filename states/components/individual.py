from aiogram.fsm.state import State, StatesGroup


class IndividualStates(StatesGroup):
    """States for individual process"""
    
    full_name_input = State()
    passport_serial_number_input = State()
    adress = State()
    phone = State()
    passport_expiry_date_input = State()
    passport_issue_place_input = State()