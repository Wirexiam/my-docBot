from aiogram.fsm.state import State, StatesGroup

class PatentedWorkActivity(StatesGroup):
    work_activity_start = State()
    input_department = State()

    passport_check = State()

    passport_data = State()
    patent_entry = State()

    medical_policy_start = State()
    medical_policy_emp_adress = State()
    medical_policy_inn = State()
    medical_policy_number = State()
    medical_policy_company = State()
    medical_policy_validity_period = State()
    medical_policy_polis_date = State()

    edit_medical_policy = State()

    edit_passport_fields = State()
    edit_patent_fields = State()
    edit_phone_number = State()