from aiogram.fsm.state import State, StatesGroup


class AboutHomeManualStates(StatesGroup):
    """States for manual home inforamtion handling"""

    where_live = State()
    addres_home = State()
    doc = State()
    details_doc = State()
    who_accepts = State()