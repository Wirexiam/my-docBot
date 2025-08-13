from aiogram.fsm.state import State, StatesGroup


class LiveAdress(StatesGroup):
    adress = State()
