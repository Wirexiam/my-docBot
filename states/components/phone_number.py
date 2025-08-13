from aiogram.fsm.state import State, StatesGroup


class PhoneNumberStates(StatesGroup):
    phone_number_input = State()
