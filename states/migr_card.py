from aiogram.fsm.state import State, StatesGroup


class MigrCardManualStates(StatesGroup):
    """States for manual card handling"""
    
    migr_card_start_manual = State()
    full_name_input = State()
    entry_date_input = State()
    citizenship_input = State()
    place_point_input = State()
    card_serial_number_input = State()
    pretria_period_input = State()
    goal = State()
    after_select_goal = State()
    before_select_goal = State()
    # passport_issue_place_input = State()