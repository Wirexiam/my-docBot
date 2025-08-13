from aiogram.fsm.state import State, StatesGroup


class RegistrationRenewalStates(StatesGroup):
    """States for stamp transfer process"""

    waiting_confirm_registration_renewal_start = State()
    after_select_mvd = State()
    after_passport = State()
    after_residence_reason_and_location = State()
