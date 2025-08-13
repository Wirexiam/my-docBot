from aiogram.fsm.state import State, StatesGroup


class SelectRegionStates(StatesGroup):
    """States for selecting region and MVD"""

    start_msg = State()
    getting_text = State()
    confirm_region = State()
