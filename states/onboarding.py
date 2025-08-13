from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Состояния для первичной настройки"""

    waiting_consent = State()
    waiting_language = State()
    completed = State()
