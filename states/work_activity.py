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