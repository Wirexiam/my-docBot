from aiogram.fsm.state import State, StatesGroup

class Arrival_transfer(StatesGroup):
    """Для процесса состояний по мигр учету"""

    waiting_confirm_start = State()
    # after_select_mvd = State()
    # after_old_passport = State()
    after_cert_kid = State()
    after_organisation = State()
    after_passport = State()
    after_migr_card = State()
    after_about_home = State()
    check_data = State()
    check_child_data = State()


