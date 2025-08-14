from aiogram.fsm.state import State, StatesGroup

class HomeMigrData(StatesGroup):
    adress = State()
    havedoc = State()
