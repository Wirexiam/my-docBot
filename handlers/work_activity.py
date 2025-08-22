from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from localization import _
from data_manager import SecureDataManager
from handlers.components.passport_manual import *
from handlers.components.phone_number import handle_phone_number_input

from states.work_activity import PatentedWorkActivity
from states.components.phone_number import PhoneNumberStates

from keyboards.work_activity import (
    kbs_patent_work_activity_start, kbs_wa_validation_department_name, kbs_wa_passport_entry,
    kbs_policy_data_confirmation, kbs_edit_wa_data, kbs_sub_editor_policy, kbs_sub_editor_passport,
    kbs_sub_editor_patient
)
from keyboards.components.residence_reason_patent import get_residence_reason_photo_or_manual_keyboard


work_activity_router = Router()
data_manager = SecureDataManager()


@work_activity_router.callback_query(F.data == "doc_work_activity")
async def wa_start(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки о трудовой деятельности по патенту"""

    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(PatentedWorkActivity.work_activity_start)

    text = f"{_.get_text("work_activity_start.title", lang)}\n{_.get_text("work_activity_start.description", lang)}\n{_.get_text("work_activity_start.documents_to_prepare", lang)}"

    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_patent_work_activity_start(lang)
    )


@work_activity_router.callback_query(F.data == "start_work_act")
async def full_name_of_the_department(callback: CallbackQuery, state: FSMContext):
    """Запрашиваем у пользователя полное название отдела"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.set_state(PatentedWorkActivity.input_department)

    text = f"{_.get_text("work_activity_department_name.title", lang)}\n\n{_.get_text("work_activity_department_name.example_text", lang)}"

    await callback.message.edit_text(
        text=text
    )


@work_activity_router.message(PatentedWorkActivity.input_department)
async def handler_full_name_of_the_department(message: Message, state: FSMContext):
    """Получаеем ответ полного названия отдела"""

    msg = message.text

    state_data = await state.get_data()
    lang = state_data.get("language")

    session_id = state_data.get("session_id")

    # await state.set_state(PatentedWorkActivity.passport_check)
    user_data = {
        "department_full_name": msg,
    }

    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text("work_activity_department_user_input.title", lang)}\n\n{_.get_text("work_activity_department_user_input.title_dep", lang)} {msg}\n\n{_.get_text("work_activity_department_user_input.description", lang)}"

    await message.answer(
        text=text,
        reply_markup=kbs_wa_validation_department_name(lang)
    )


@work_activity_router.callback_query(F.data == "correct_department_name")
async def handler_passport_check(callback: CallbackQuery, state: FSMContext):
    """Получаем положительный ответ от пользователя и запращиваем данные паспорта"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    text = f"{_.get_text("work_activity_passport_req.title", lang)}\n\n{_.get_text("work_activity_passport_req.description", lang)}"

    await state.update_data(from_action=PatentedWorkActivity.passport_data,
                         passport_title="wa_passport_title")

    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_wa_passport_entry(lang)
    )

    # await handle_passport_manual_start(callback, state)


@work_activity_router.message(PatentedWorkActivity.passport_data)
async def handle_passport_data(message: Message, state: FSMContext):
    """Получаем данные ввода паспорта. Предлагаем пользователю ввести данные патента"""

    passport_issued = message.text.strip()

    passport_data = (await state.get_data()).get("passport_data", {})
    passport_data["passport_issued"] = passport_issued
    await state.update_data(passport_data=passport_data)

    state_data = await state.get_data()
    lang = state_data.get("language")

    session_id = state_data.get("session_id")

    passport_data = state_data.get("passport_data")
    if passport_data:
        await state.update_data(from_action=(PatentedWorkActivity.patent_entry))
    
    text = f"{_.get_text("wa_patent.wa_patent_start.title", lang)}\n{_.get_text("wa_patent.wa_patent_start.description", lang)}"

    await message.answer(
        text=text,
        reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )


@work_activity_router.message(PatentedWorkActivity.patent_entry)
async def handle_patient_data(message: Message, state: FSMContext):
    """Сохраняем данные патента и запрашиваем данные ДМС"""

    issue_place = message.text.strip()
    await state.update_data(patient_issue_place=issue_place)

    state_data = await state.get_data()
    lang = state_data.get("language")

    session_id = state_data.get("session_id")

    patient_data = {
        "patient_number": state_data.get("patient_number"),
        "patient_date": state_data.get("patient_date"),
        "patient_issue_place": state_data.get("patient_issue_place"),
    }

    data_manager.save_user_data(message.from_user.id, session_id, {"patient_data": patient_data})

    text = f"{_.get_text("wa_patent.wa_patent_medical_policy.name_work.title", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.name_work.description", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.name_work.example", lang)}"

    await state.set_state(PatentedWorkActivity.medical_policy_start)

    await message.answer(
        text=text
    )


@work_activity_router.message(PatentedWorkActivity.medical_policy_start)
async def get_name_work(message: Message, state: FSMContext):
    """Сохраняем название профессии, запрашиваем адрес работодателя"""
    work_name = message.text.strip()

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(
        work_name=work_name
    )

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = f"{_.get_text("wa_patent.wa_patent_medical_policy.employer_address.title", lang)}\n{_.get_text("wa_patent.wa_patent_medical_policy.employer_address.example", lang)}"

    await state.set_state(PatentedWorkActivity.medical_policy_emp_adress)

    await message.answer(
        text=text
    )


@work_activity_router.message(PatentedWorkActivity.medical_policy_emp_adress)
async def get_INN(message: Message, state: FSMContext):
    """Сохраняем Адрес работодателя, запрашиваем ИНН"""

    emp_adress = message.text.strip()

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(
        emp_adress=emp_adress
    )

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return


    text = f"{_.get_text("wa_patent.wa_patent_medical_policy.INN.title", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.INN.format", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.INN.example", lang)}"

    await state.set_state(PatentedWorkActivity.medical_policy_inn)

    await message.answer(
        text=text
    )


@work_activity_router.message(PatentedWorkActivity.medical_policy_inn)
async def get_number_phone(message: Message, state: FSMContext):
    """Сохраняем ИНН, запрашиваем номер телефона"""
    inn = message.text.strip()

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(
        inn=inn
    )

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    await state.set_state(PatentedWorkActivity.medical_policy_number)

    await message.answer(
        text = f"{_.get_text('phone_number.title', lang)}\n{_.get_text('phone_number.example_text', lang)}"
    )



@work_activity_router.message(PatentedWorkActivity.medical_policy_number)
async def get_medical_policy_number(message: Message, state: FSMContext):
    """Сохраняем phone number и запрашиваем номер ДМС"""

    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    phone_number = message.text.strip()

    user_data = {
        "phone_number": phone_number
    }
    await state.update_data(
        phone_number=phone_number
    )

    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = f"{_.get_text("wa_patent.wa_patent_medical_policy_number.title",lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy_number.description", lang)}\n{_.get_text("wa_patent.wa_patent_medical_policy_number.example", lang)}"


    await state.set_state(PatentedWorkActivity.medical_policy_company)
    await message.answer(
        text=text
    )

@work_activity_router.message(PatentedWorkActivity.medical_policy_company)
async def get_insurance_company(message: Message, state: FSMContext):
    """Сохраняем ДМС номер и запрашиваем название страховой компании"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    policy_number = message.text.strip()

    await state.update_data(
        policy_number=policy_number
    )

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = f"{_.get_text("wa_patent.wa_patent_insurance_company.title", lang)}\n{_.get_text("wa_patent.wa_patent_insurance_company.example", lang)}"

    await state.set_state(PatentedWorkActivity.medical_policy_validity_period)
    await message.answer(
        text=text
    )


@work_activity_router.message(PatentedWorkActivity.medical_policy_validity_period)
async def get_medical_policy_validity_period(message: Message, state: FSMContext):
    """Сохраняем имя страховой компании, запрашиваем срок действия полиса ДМС"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    medical_policy_company = message.text.strip()

    await state.update_data(
        medical_policy_company=medical_policy_company
    )

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return
    
    text = f"{_.get_text("wa_patent.wa_polis_date.title", lang)}\n\n{_.get_text("wa_patent.wa_polis_date.description", lang)}"

    await state.set_state(PatentedWorkActivity.medical_policy_polis_date)

    await message.answer(
        text=text
    )

@work_activity_router.message(PatentedWorkActivity.medical_policy_polis_date)
async def get_medical_policy_polis_date(message: Message, state: FSMContext):
    """Сохраняем срок действия полиса и подтверждаем валидность данных"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    passport = state_data.get("passport_data", {})

    current_state = await state.get_state()
    if current_state == PatentedWorkActivity.medical_policy_polis_date.state:
        medical_policy_polis_date = message.text.strip()
        await state.update_data(
            medical_policy_polis_date=medical_policy_polis_date
        )
        state_data = await state.get_data()


    text = (
        f"{_.get_text("wa_patent.edit_wa_data.title", lang)}\n\n"
        f"{_.get_text("wa_patent.edit_wa_data.full_name", lang)}: {passport.get('full_name')}\n"
        f"{_.get_text("wa_patent.edit_wa_data.passport", lang)}: {passport.get('passport_serial_number')}, {passport.get('passport_issue_date')}, {passport.get('passport_issued')}, {passport.get('passport_expiry_date')}\n"
        f"{_.get_text("wa_patent.edit_wa_data.patent", lang)}: {state_data.get('patient_number')}, {state_data.get('patient_date')}, {state_data.get('patient_issue_place')}\n"
        f"{_.get_text("wa_patent.edit_wa_data.work_adress", lang)}: {state_data.get('emp_adress')}\n"
        f"{_.get_text("wa_patent.edit_wa_data.profession", lang)}: {state_data.get('work_name')}\n"
        f"{_.get_text("wa_patent.edit_wa_data.inn", lang)}: {state_data.get('inn')}\n"
        f"{_.get_text("wa_patent.edit_wa_data.policy", lang)}: {state_data.get('policy_number')}, {state_data.get('medical_policy_company')}, {state_data.get('medical_policy_polis_date')}\n"
        f"{_.get_text("wa_patent.edit_wa_data.phone_number", lang)}: {state_data.get('phone_number')}"
    )

    await message.answer(
        text=text,
        reply_markup=kbs_policy_data_confirmation(lang)
    )


@work_activity_router.callback_query(F.data == "edit_wa_patent_data")
async def edit_wa_data(query: CallbackQuery, state: FSMContext):
    """
    Главный редактор. 
    Выводим пользователю инфу которую можно отредактировать
    
    """
    state_data = await state.get_data()
    lang = state_data.get("language")

    text = f"{_.get_text("wa_patent.wa_data_editor.title", lang)}"

    await query.message.edit_text(
        text=text,
        reply_markup=kbs_edit_wa_data(lang)
    )


@work_activity_router.callback_query(F.data.startswith("wa_edit_"))
async def wa_editor(query: CallbackQuery, state: FSMContext):
    """Тут мы получаем параметр который нужно отредактировать и выводим инструкции"""

    param_to_edit = query.data[len("wa_edit_"):]

    state_data = await state.get_data()
    lang = state_data.get("language")


    if param_to_edit == "back_to_data":
        await get_medical_policy_polis_date(query.message, state)

    elif param_to_edit == "passport":
        await query.message.edit_text(
            text=_.get_text("wa_patent.wa_data_editor.sub_editor_data.passport.title", lang),
            reply_markup=kbs_sub_editor_passport(lang)
        )

    elif param_to_edit == "patent":
        await query.message.edit_text(
            text=_.get_text("wa_patent.wa_data_editor.sub_editor_data.patent.title", lang),
            reply_markup=kbs_sub_editor_patient(lang)
        )
    elif param_to_edit == "profession":
        text = f"{_.get_text("wa_patent.wa_patent_medical_policy.name_work.title", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.name_work.description", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.name_work.example", lang)}"
        await query.message.edit_text(text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_start)
    elif param_to_edit == "work_adress":
        text = f"{_.get_text("wa_patent.wa_patent_medical_policy.employer_address.title", lang)}\n{_.get_text("wa_patent.wa_patent_medical_policy.employer_address.example", lang)}"
        await query.message.edit_text(text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_emp_adress)
    elif param_to_edit == "inn":
        text = f"{_.get_text("wa_patent.wa_patent_medical_policy.INN.title", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.INN.format", lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy.INN.example", lang)}"
        await query.message.edit_text(text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_inn)
    elif param_to_edit == "policy":
        text = f"{_.get_text("wa_patent.wa_data_editor.sub_editor_data.policy.title", lang)}"
        await query.message.edit_text(
            text=text,
            reply_markup=kbs_sub_editor_policy(lang)
        )
    elif param_to_edit == "phone_number":
        await state.set_state(PatentedWorkActivity.edit_phone_number)
        
        text = _.get_text("wa_patent.wa_data_editor.sub_editor_data.phone_number.title", lang)
        await query.message.edit_text(
            text=text
        )
    else:
        await get_medical_policy_polis_date(query.message, state)



@work_activity_router.message(PatentedWorkActivity.edit_phone_number)
async def phone_number_editor(message: Message, state: FSMContext):
    """Редактирование номера телефона"""

    state_data = await state.get_data()
    phone_number = message.text.strip()

    await state.update_data(phone_number=phone_number)
    await get_medical_policy_polis_date(message, state)



@work_activity_router.callback_query(F.data.startswith("edit_policy_"))
async def medical_policy_editor(query: CallbackQuery, state: FSMContext):
    """Ловим поле для редактирования по ДМС"""

    param_to_edit = query.data[len("edit_policy_"):]

    state_data = await state.get_data()
    lang = state_data.get("language")

    if param_to_edit == "number":
        #Номер страхового полиса
        text = f"{_.get_text("wa_patent.wa_patent_medical_policy_number.title",lang)}\n\n{_.get_text("wa_patent.wa_patent_medical_policy_number.description", lang)}\n{_.get_text("wa_patent.wa_patent_medical_policy_number.example", lang)}"
        await query.message.edit_text(
            text=text
        )
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_company)

    if param_to_edit == "company":
        #Название страховой компании
        text = f"{_.get_text("wa_patent.wa_patent_insurance_company.title", lang)}\n{_.get_text("wa_patent.wa_patent_insurance_company.example", lang)}"
        await query.message.edit_text(
            text=text
        )
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_validity_period)
    
    if param_to_edit == "dateof":
        #Срок действия полиса
        text = f"{_.get_text("wa_patent.wa_polis_date.title", lang)}\n\n{_.get_text("wa_patent.wa_polis_date.description", lang)}"
        await query.message.edit_text(
            text=text
        )
        await state.set_state(PatentedWorkActivity.medical_policy_polis_date)

    
@work_activity_router.callback_query(F.data.startswith("edit_passport_"))
async def edit_passport_data_fields(query: CallbackQuery, state: FSMContext):
    """Получаем параметр паспорта который нужно отредактировать"""


    param_to_edit = query.data[len("edit_passport_"):]


    state_data = await state.get_data()
    lang = state_data.get("language")

    if param_to_edit == "full_name":
        text = f"{_.get_text("passport_manual_full_name.description", lang)}"
        await query.message.edit_text(
            text=text
        )
        await state.update_data(
            edit_passport_field=param_to_edit
        )
    
    elif param_to_edit in ["passport_serial_number", "passport_issue_date", "passport_issued", "passport_expiry_date"]:
        text = _.get_text(f"wa_patent.wa_data_editor.sub_editor_data.passport.{param_to_edit}", lang)
        await state.update_data(
            edit_passport_field=param_to_edit
        )
        await query.message.edit_text(
            text=text
        )

    await state.set_state(PatentedWorkActivity.edit_passport_fields)


@work_activity_router.message(PatentedWorkActivity.edit_passport_fields)
async def edit_passport_fields(message: Message, state: FSMContext):
    """Хендлер принимает параметр паспорта и редактирует его"""

    state_data = await state.get_data()

    field = state_data.get("edit_passport_field")
    passport = state_data.get("passport_data", {})
    passport[field] = message.text.strip()
    await state.update_data(passport=passport)

    await state.update_data(edit_passport_field=None)

    await get_medical_policy_polis_date(message, state)


@work_activity_router.callback_query(F.data.startswith("edit_patent_"))
async def edit_patent_data_fields(query: CallbackQuery, state: FSMContext):

    state_data = await state.get_data()
    lang = state_data.get("language")

    param_to_edit = query.data[len("edit_patent_"):]

    if param_to_edit in ["patient_number", "patient_date", "patient_issue_place"]:

        text = _.get_text(f"wa_patent.wa_data_editor.sub_editor_data.patent.{param_to_edit}", lang)
        await query.message.edit_text(
            text=text
        )
        await state.set_state(PatentedWorkActivity.edit_patent_fields)
        await state.update_data(edit_patent_fields=param_to_edit)
    

@work_activity_router.message(PatentedWorkActivity.edit_patent_fields)
async def edit_passport_fields(message: Message, state: FSMContext):
    """Хендлер принимает параметр патента и редактирует его"""

    state_data = await state.get_data()
    field = state_data.get("edit_patent_fields")

    await state.update_data({field: message.text.strip()})
    await state.update_data(edit_patent_fields=None)

    await get_medical_policy_polis_date(message, state)


@work_activity_router.callback_query(F.data == "accept_wa_patent_data")
async def accept_wa_patent_data(query: CallbackQuery, state: FSMContext):
    """
        Сохраняет данные пользователя.

        Формат сохраняемых данных:
        {
            "language": str,  # Язык (например, "ru")
            "department_full_name": str,  # Полное название отдела/организации
            "passport_data": {
                "full_name": str,  # ФИО
                "birth_date": str,  # Дата рождения
                "citizenship": str,  # Гражданство
                "passport_serial_number": str,  # Серия и номер документа
                "passport_issue_date": str,  # Дата выдачи документа
                "passport_expiry_date": str  # Срок действия паспорта
            },
            "patient_data": {
                "patient_number": str,  # Номер патента
                "patient_date": str,  # Дата выдачи патента
                "patient_issue_place": str  # Кем выдан патент
            },
            "phone_number": str,  # Актуальный номер телефона
            "medical_policy": {
                "policy_number": str,  # Номер ДМС
                "medical_policy_company": str,  # Страховая компания
                "medical_policy_polis_date": str  # Срок действия ДМС
            },
            "inn": str,  # ИНН
            "work_data": {
                "emp_adress": str,  # Юридический адрес работодателя
                "work_name": str  # Должность/профессия
            }
        }

        Args:
            query (CallbackQuery): Объект callback-запроса от Telegram.
            state (FSMContext): Контекст состояния пользователя.
    """


    state_data = await state.get_data()
    session_id = state_data.get("session_id")

    user_data = {
        "medical_policy": {
            "policy_number": state_data.get("policy_number"),
            "medical_policy_company": state_data.get("medical_policy_company"),
            "medical_policy_polis_date": state_data.get("medical_policy_polis_date"),
        },
        "inn": state_data.get("inn"),
        "phone_number": state_data.get("phone_number"),
        "work_data": {
            "emp_adress": state_data.get("emp_adress"),
            "work_name": state_data.get("work_name"),
        }
    }

    data_manager.save_user_data(
        user_id=query.from_user.id,
        session_id=session_id,
        data=user_data
    )

    data_manager.load_user_data(query.from_user.id, session_id)

