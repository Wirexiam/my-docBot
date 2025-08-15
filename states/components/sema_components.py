from aiogram.fsm.state import State, StatesGroup


class WorkedLastYearStates(StatesGroup):
    """тут только стейты, кооторые в диалоге"""
    # start = State() лучше так не делать, а перенести в другой класс
    hiring_date = State()
    org_name = State()
    job_title = State()
    work_adress = State()
    is_working = State()
    dismissal_date = State()
