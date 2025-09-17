# states/work_activity.py
from aiogram.fsm.state import StatesGroup, State

class PatentedWorkActivity(StatesGroup):
    work_activity_start = State()
    input_department = State()
    passport_data = State()

    # СТАЛО: разнос по ролям
    patent_entry_choice = State()         # экран "загрузить/ввести"
    patent_manual_number = State()        # номер патента
    patent_manual_date = State()          # дата выдачи патента
    patent_manual_issue_place = State()   # кем выдан патент

    medical_policy_start = State()
    medical_policy_emp_adress = State()
    medical_policy_inn = State()
    medical_policy_number = State()
    medical_policy_company = State()
    medical_policy_validity_period = State()
    medical_policy_polis_date = State()

    edit_passport_fields = State()
    edit_patent_fields = State()
    edit_phone_number = State()
