from aiogram.fsm.state import State, StatesGroup


class WorkedLastYearStates(StatesGroup):
    """States for stamp transfer process"""
    start = State()
    hiring_date = State()
    org_name = State()
    job_title = State()
    work_adress = State()
    is_working = State()
    dismissal_date = State()
