from aiogram.fsm.state import State, StatesGroup


class RepresentativeStates(StatesGroup):
    """
    Состояние для Законного представителя
    """

    who_representative = State()
    full_name_representative = State()
    data_birth_representative = State()
