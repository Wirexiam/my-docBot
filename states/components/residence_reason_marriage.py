from aiogram.fsm.state import State, StatesGroup


class ResidenceReasonMarriageStates(StatesGroup):
    """
    Состояния для ветки «Продление пребывания — по браку».

    Хэндлеры ожидают шаги:
      1) spouse_fio           — ФИО супруга
      2) spouse_birth_date    — дата рождения супруга
      3) marriage_citizenship — гражданство супруга
      4) marriage_number      — номер свидетельства о браке
      5) issue_date           — дата выдачи свидетельства
      6) issue_place          — кем выдано свидетельство
    """

    choose_photo_or_manual = State()

    spouse_fio = State()
    spouse_birth_date = State()
    marriage_citizenship = State()
    marriage_number = State()
    issue_date = State()
    issue_place = State()
