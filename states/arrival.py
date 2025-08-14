from aiogram.fsm.state import State, StatesGroup

class Arrival_transfer(StatesGroup):
    """Для процесса состояний по мигр учету"""

    waiting_confirm_start = State()
    # after_select_mvd = State()
    # after_old_passport = State()
    after_passport = State()
    after_migr_card = State()
    after_about_home = State()
