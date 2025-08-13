from aiogram.fsm.state import State, StatesGroup


class Stamp_transfer(StatesGroup):
    """States for stamp transfer process"""

    waiting_confirm_stamp_transfer_start = State()
    after_select_mvd = State()
    after_old_passport = State()
    after_new_passport = State()
