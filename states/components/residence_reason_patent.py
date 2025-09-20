from aiogram.fsm.state import State, StatesGroup


class ResidenceReasonPatentStates(StatesGroup):
    """
    Состояния для ветки «Продление пребывания — по патенту».

    Хэндлеры ожидают шаги строго в таком порядке:
      1) patient_number  — ввод номера патента
      2) patient_date    — ввод даты выдачи патента
      3) issue_place     — ввод «кем выдан» (патент)

    Ниже имена синхронизированы с хэндлерами.
    Для обратной совместимости оставлены алиасы старых опечатанных имён.
    """

    # Выбор способа ввода (фото / вручную)
    choose_photo_or_manual = State()

    # Ручной ввод патента
    patient_number = State()
    patient_date = State()
    issue_place = State()

    # ── Алиасы для старого кода ──
    patient_numper = patient_number  # опечатка в старом коде
    issue_date = patient_date  # старое имя шага
