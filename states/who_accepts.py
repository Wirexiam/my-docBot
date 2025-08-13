from aiogram.fsm.state import State, StatesGroup


class PersonStates(StatesGroup):
    """States about an individual handling"""

    
class OrganizationStates(StatesGroup):
    """States about an rganization handling"""

    where_live = State()
    addres_home = State()
    doc = State()
    details_doc = State()
    who_accepts = State()