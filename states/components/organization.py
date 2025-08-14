from aiogram.fsm.state import State, StatesGroup


class OrganizationStates(StatesGroup):
    """States for organization process"""

    name_organization = State()
    inn = State()
    adress = State()
    full_name_contact_of_organization = State()
    phone_contact_of_organization = State()
    profession = State()