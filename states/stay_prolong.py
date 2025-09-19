from aiogram.fsm.state import StatesGroup, State


class StayProlong(StatesGroup):
    # вход и паспорт
    start = State()
    after_passport = State()
    select_basis = State()

    # брак
    marriage_spouse_full_name = State()
    marriage_spouse_birth_date = State()
    marriage_spouse_citizenship = State()
    marriage_cert_number = State()
    marriage_cert_date = State()
    marriage_cert_issued_by = State()

    # ребёнок
    child_full_name = State()
    child_birth_date = State()
    child_citizenship = State()
    child_cert_number = State()
    child_cert_date = State()
    child_cert_issued_by = State()

    # патент
    patent_number = State()
    patent_issue_date = State()
    patent_issued_by = State()
    patent_profession = State()
    patent_employer_address = State()
    patent_inn = State()
    # опционально ДМС
    patent_dms_number = State()
    patent_dms_company = State()
    patent_dms_period = State()

    # общие поля
    address = State()
    phone = State()

    # финальная сводка/генерация
    confirm = State()
