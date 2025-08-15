from aiogram.fsm.state import State, StatesGroup


class DocResidenceNotificationStates(StatesGroup):
    """States for stamp transfer process"""

    waiting_confirm_start = State()
    after_select_mvd = State()
    after_passport = State()
    after_adress = State()
    worked_last_year_data = State()
    check_data = State()
    start_worked_last_year = State()






class TravelOutsideRuStates(StatesGroup):
    """States for stamp transfer process"""
    start = State()
    date = State()
    place = State()




class IncomeLastYearStates(StatesGroup):
    """States for stamp transfer process"""

    start = State()
    income = State()
    after_income = State()



