from pprint import pprint
import re

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from pdf_generator.gen_pdf import create_user_doc
from localization import _
from data_manager import SecureDataManager
from handlers.components.passport_manual import *  # твои уже готовые компоненты
from handlers.components.phone_number import handle_phone_number_input

from states.work_activity import PatentedWorkActivity
from states.components.phone_number import PhoneNumberStates

from keyboards.work_activity import (
    kbs_patent_work_activity_start,
    kbs_wa_validation_department_name,
    kbs_wa_passport_entry,
    kbs_policy_data_confirmation,
    kbs_edit_wa_data,
    kbs_sub_editor_policy,
    kbs_sub_editor_passport,
    kbs_sub_editor_patient,
)
from keyboards.components.residence_reason_patent import (
    get_residence_reason_photo_or_manual_keyboard,
)

work_activity_router = Router()
data_manager = SecureDataManager()


# ─────────────────────────── Старт и ввод отдела ───────────────────────────

@work_activity_router.callback_query(F.data == "doc_work_activity")
async def wa_start(callback: CallbackQuery, state: FSMContext):
    """Стартовый экран блока «Трудовая деятельность по патенту»."""
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(PatentedWorkActivity.work_activity_start)

    text = (
        f"{_.get_text('work_activity_start.title', lang)}\n"
        f"{_.get_text('work_activity_start.description', lang)}\n"
        f"{_.get_text('work_activity_start.documents_to_prepare', lang)}"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_patent_work_activity_start(lang)
    )


@work_activity_router.callback_query(F.data == "start_work_act")
async def full_name_of_the_department(callback: CallbackQuery, state: FSMContext):
    """Запрашиваем полное название отдела/организации (куда идёт уведомление)."""
    lang = (await state.get_data()).get("language")
    await state.set_state(PatentedWorkActivity.input_department)

    text = (
        f"{_.get_text('work_activity_department_name.title', lang)}\n\n"
        f"{_.get_text('work_activity_department_name.example_text', lang)}"
    )
    await callback.message.edit_text(text=text)


@work_activity_router.message(PatentedWorkActivity.input_department)
async def handler_full_name_of_the_department(message: Message, state: FSMContext):
    """Сохраняем название отдела и предлагаем подтвердить."""
    msg = message.text.strip()

    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    user_data = {"department_full_name": msg}
    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = (
        f"{_.get_text('work_activity_department_user_input.title', lang)}\n\n"
        f"{_.get_text('work_activity_department_user_input.title_dep', lang)} {msg}\n\n"
        f"{_.get_text('work_activity_department_user_input.description', lang)}"
    )
    await message.answer(
        text=text,
        reply_markup=kbs_wa_validation_department_name(lang)
    )


# ───────────────────── Запрос паспорта (фото/вручную) ──────────────────────

@work_activity_router.callback_query(F.data == "correct_department_name")
async def handler_passport_check(callback: CallbackQuery, state: FSMContext):
    """Подтверждён отдел → просим паспорт (фото/вручную)."""
    lang = (await state.get_data()).get("language")

    # Коммуникация с паспортным фото-компонентом:
    await state.update_data(
        from_action=PatentedWorkActivity.passport_data,  # если понадобится ручной «кем выдан»
        passport_title="wa_passport_title",
        ocr_flow="wa",  # метка потока
        waiting_data=None,
        change_id=None,
        is_now_edit=False,
    )

    text = (
        f"{_.get_text('work_activity_passport_req.title', lang)}\n\n"
        f"{_.get_text('work_activity_passport_req.description', lang)}"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_wa_passport_entry(lang)  # первая кнопка должна слать 'passport_new_photo_start'
    )


@work_activity_router.callback_query(F.data == "wa_after_passport")
async def wa_after_passport(cb: CallbackQuery, state: FSMContext):
    """
    Паспорт подтверждён (OCR/ручной) → либо сразу в ДМС (если патент уже готов),
    либо показываем выбор способа для патента.
    """
    sd = await state.get_data()
    lang = sd.get("language")

    # если патент уже введён (или все 3 ключевых поля присутствуют) — идём в ДМС
    if sd.get("patent_ready") or (
        sd.get("patient_number") and sd.get("patient_date") and sd.get("patient_issue_place")
    ):
        await state.set_state(PatentedWorkActivity.medical_policy_start)
        await cb.message.edit_text(
            text=(
                f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.title', lang)}\n\n"
                f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.description', lang)}\n\n"
                f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.example', lang)}"
            )
        )
        return

    # иначе — экран выбора способа для патента
    await state.set_state(PatentedWorkActivity.patent_entry_choice)
    text = (
        f"{_.get_text('wa_patent.wa_patent_start.title', lang)}\n"
        f"{_.get_text('wa_patent.wa_patent_start.description', lang)}"
    )
    await cb.message.edit_text(
        text=text,
        reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )

@work_activity_router.message(PatentedWorkActivity.passport_data)
async def handle_passport_data(message: Message, state: FSMContext):
    """
    Доввод по паспорту (ручное «кем выдан»). Если патент уже готов — сразу ДМС,
    иначе — экран выбора способа для патента.
    """
    # обновляем "кем выдан" в passport_data
    sd = await state.get_data()
    passport_data = (sd.get("passport_data") or {}).copy()
    passport_data["passport_issued"] = message.text.strip()
    await state.update_data(passport_data=passport_data)

    # свежие данные и язык
    sd = await state.get_data()
    lang = sd.get("language")

    # если патент уже введён (или все поля есть) — в ДМС
    if sd.get("patent_ready") or (
        sd.get("patient_number") and sd.get("patient_date") and sd.get("patient_issue_place")
    ):
        await state.set_state(PatentedWorkActivity.medical_policy_start)
        await message.answer(
            text=(
                f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.title', lang)}\n\n"
                f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.description', lang)}\n\n"
                f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.example', lang)}"
            )
        )
        return

    # иначе — показываем выбор способа для патента
    await state.set_state(PatentedWorkActivity.patent_entry_choice)
    text = (
        f"{_.get_text('wa_patent.wa_patent_start.title', lang)}\n"
        f"{_.get_text('wa_patent.wa_patent_start.description', lang)}"
    )
    await message.answer(
        text=text,
        reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )

# ─────────────────────── Патент: выбор/ручной ввод ─────────────────────────

@work_activity_router.callback_query(F.data.in_({"wa_patent_manual_start", "patent_manual_start"}))
async def patent_manual_start(cb: CallbackQuery, state: FSMContext):
    """Переходим на ручной ввод: номер патента."""
    lang = (await state.get_data()).get("language")
    await state.set_state(PatentedWorkActivity.patent_manual_number)
    await cb.message.edit_text(
        text=f"{_.get_text('wa_patent.manual.number.title', lang)}\n{_.get_text('wa_patent.manual.number.example', lang)}"
    )


@work_activity_router.message(PatentedWorkActivity.patent_entry_choice)
async def be_lenient_if_user_types_number_here(message: Message, state: FSMContext):
    """
    Пользователь мог случайно прислать номер патента прямо на экране выбора.
    Будем дружелюбны: считаем это номером и двигаемся как при manual_number.
    """
    txt = (message.text or "").strip()
    if not txt:
        return
    await state.update_data(patient_number=txt)
    lang = (await state.get_data()).get("language")
    await state.set_state(PatentedWorkActivity.patent_manual_date)
    await message.answer(
        text=f"{_.get_text('wa_patent.manual.date.title', lang)}\n{_.get_text('wa_patent.manual.date.example', lang)}"
    )


@work_activity_router.message(PatentedWorkActivity.patent_manual_number)
async def patent_manual_number(message: Message, state: FSMContext):
    """Шаг 1 ручного патента: номер → спрашиваем дату."""
    await state.update_data(patient_number=message.text.strip())
    lang = (await state.get_data()).get("language")
    await state.set_state(PatentedWorkActivity.patent_manual_date)
    await message.answer(
        text=f"{_.get_text('wa_patent.manual.date.title', lang)}\n{_.get_text('wa_patent.manual.date.example', lang)}"
    )


@work_activity_router.message(PatentedWorkActivity.patent_manual_date)
async def patent_manual_date(message: Message, state: FSMContext):
    """Шаг 2 ручного патента: дата → спрашиваем «кем выдан»."""
    await state.update_data(patient_date=message.text.strip())
    lang = (await state.get_data()).get("language")
    await state.set_state(PatentedWorkActivity.patent_manual_issue_place)
    await message.answer(
        text=f"{_.get_text('wa_patent.manual.issued_by.title', lang)}\n{_.get_text('wa_patent.manual.issued_by.example', lang)}"
    )


@work_activity_router.message(PatentedWorkActivity.patent_manual_issue_place)
async def patent_manual_issue_place(message: Message, state: FSMContext):
    """
    Шаг 3 ручного патента: «кем выдан».
    Сохраняем patient_data, помечаем патент как готовый и переходим в блок ДМС.
    """
    # сохраняем "кем выдан"
    await state.update_data(patient_issue_place=message.text.strip())

    # читаем текущее состояние
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    # собираем и сохраняем patient_data целиком
    patient_data = {
        "patient_number": state_data.get("patient_number"),
        "patient_date": state_data.get("patient_date"),
        "patient_issue_place": state_data.get("patient_issue_place"),
    }
    data_manager.save_user_data(message.from_user.id, session_id, {"patient_data": patient_data})
    await state.update_data(patient_data=patient_data)

    # помечаем, что патент полностью введён
    await state.update_data(patent_ready=True)

    # переходим к блоку ДМС
    await state.set_state(PatentedWorkActivity.medical_policy_start)
    await message.answer(
        text=(
            f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.title', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.description', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.example', lang)}"
        )
    )


@work_activity_router.callback_query(F.data.in_({"wa_patent_photo_start", "patent_photo_start"}))
async def patent_photo_start(cb: CallbackQuery, state: FSMContext):
    """
    Пользователь выбрал загрузку фото патента.
    Здесь только подсказываем, что делать дальше.
    Сам OCR/обработчик фото патента — в твоих соответствующих роутерах.
    После успешного OCR (когда известны patient_*), переводи в medical_policy_start.
    """
    lang = (await state.get_data()).get("language")
    await cb.message.edit_text(
        text=_.get_text("wa_patent.photo.hint", lang)  # строку добавь в словарь локализации
    )
    # Подсказка: когда фото-обработчик закончит,
    # сделай что-то вроде:
    # await state.update_data(patient_number=..., patient_date=..., patient_issue_place=...)
    # await state.set_state(PatentedWorkActivity.medical_policy_start)
    # await message.answer(... как в patent_manual_issue_place ...)


# ───────────────────────────── Блок ДМС (как было) ─────────────────────────

@work_activity_router.message(PatentedWorkActivity.medical_policy_start)
async def get_name_work(message: Message, state: FSMContext):
    """Название профессии → далее адрес работодателя."""
    work_name = message.text.strip()
    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(work_name=work_name)

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = (
        f"{_.get_text('wa_patent.wa_patent_medical_policy.employer_address.title', lang)}\n"
        f"{_.get_text('wa_patent.wa_patent_medical_policy.employer_address.example', lang)}"
    )

    await state.set_state(PatentedWorkActivity.medical_policy_emp_adress)
    await message.answer(text=text)


@work_activity_router.message(PatentedWorkActivity.medical_policy_emp_adress)
async def get_INN(message: Message, state: FSMContext):
    """Адрес работодателя → ИНН."""
    emp_adress = message.text.strip()
    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(emp_adress=emp_adress)

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = (
        f"{_.get_text('wa_patent.wa_patent_medical_policy.INN.title', lang)}\n\n"
        f"{_.get_text('wa_patent.wa_patent_medical_policy.INN.format', lang)}\n\n"
        f"{_.get_text('wa_patent.wa_patent_medical_policy.INN.example', lang)}"
    )

    await state.set_state(PatentedWorkActivity.medical_policy_inn)
    await message.answer(text=text)


@work_activity_router.message(PatentedWorkActivity.medical_policy_inn)
async def get_number_phone(message: Message, state: FSMContext):
    """ИНН → номер телефона."""
    inn = message.text.strip()
    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(inn=inn)

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    await state.set_state(PatentedWorkActivity.medical_policy_number)
    await message.answer(
        text=f"{_.get_text('phone_number.title', lang)}\n{_.get_text('phone_number.example_text', lang)}"
    )


@work_activity_router.message(PatentedWorkActivity.medical_policy_number)
async def get_medical_policy_number(message: Message, state: FSMContext):
    """Телефон → номер ДМС."""
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    phone_number = message.text.strip()

    user_data = {"phone_number": phone_number}
    await state.update_data(phone_number=phone_number)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = (
        f"{_.get_text('wa_patent.wa_patent_medical_policy_number.title', lang)}\n\n"
        f"{_.get_text('wa_patent.wa_patent_medical_policy_number.description', lang)}\n"
        f"{_.get_text('wa_patent.wa_patent_medical_policy_number.example', lang)}"
    )

    await state.set_state(PatentedWorkActivity.medical_policy_company)
    await message.answer(text=text)


@work_activity_router.message(PatentedWorkActivity.medical_policy_company)
async def get_insurance_company(message: Message, state: FSMContext):
    """Номер ДМС → страховая компания."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    policy_number = message.text.strip()
    await state.update_data(policy_number=policy_number)

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = (
        f"{_.get_text('wa_patent.wa_patent_insurance_company.title', lang)}\n"
        f"{_.get_text('wa_patent.wa_patent_insurance_company.example', lang)}"
    )

    await state.set_state(PatentedWorkActivity.medical_policy_validity_period)
    await message.answer(text=text)


@work_activity_router.message(PatentedWorkActivity.medical_policy_validity_period)
async def get_medical_policy_validity_period(message: Message, state: FSMContext):
    """Страховая компания → срок действия ДМС."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    medical_policy_company = message.text.strip()
    await state.update_data(medical_policy_company=medical_policy_company)

    if state_data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await get_medical_policy_polis_date(message, state)
        return

    text = (
        f"{_.get_text('wa_patent.wa_polis_date.title', lang)}\n\n"
        f"{_.get_text('wa_patent.wa_polis_date.description', lang)}"
    )

    await state.set_state(PatentedWorkActivity.medical_policy_polis_date)
    await message.answer(text=text)


@work_activity_router.message(PatentedWorkActivity.medical_policy_polis_date)
async def get_medical_policy_polis_date(message: Message, state: FSMContext):
    """Срок действия ДМС → показываем сводку и клавиатуру подтверждения/редактирования."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    passport = state_data.get("passport_data", {})

    current_state = await state.get_state()
    if current_state == PatentedWorkActivity.medical_policy_polis_date.state:
        medical_policy_polis_date = message.text.strip()
        await state.update_data(medical_policy_polis_date=medical_policy_polis_date)
        state_data = await state.get_data()

    patient_data = state_data.get("patient_data", {})
    pprint(state_data)

    issuer = passport.get('passport_issue_place') or passport.get('passport_issued')
    pn = patient_data.get('patient_number') or state_data.get('patient_number')
    pd = patient_data.get('patient_date') or state_data.get('patient_date')
    pip = patient_data.get('patient_issue_place') or state_data.get('patient_issue_place')

    text = (
        f"{_.get_text('wa_patent.edit_wa_data.title', lang)}\n\n"
        f"{_.get_text('wa_patent.edit_wa_data.full_name', lang)}: {passport.get('full_name')}\n"
        f"{_.get_text('wa_patent.edit_wa_data.passport', lang)}: "
        f"{passport.get('passport_serial_number')}, {passport.get('passport_issue_date')}, {issuer}, {passport.get('passport_expiry_date')}\n"
        f"{_.get_text('wa_patent.edit_wa_data.patent', lang)}: {pn}, {pd}, {pip}\n"
        f"{_.get_text('wa_patent.edit_wa_data.work_adress', lang)}: {state_data.get('emp_adress')}\n"
        f"{_.get_text('wa_patent.edit_wa_data.profession', lang)}: {state_data.get('work_name')}\n"
        f"{_.get_text('wa_patent.edit_wa_data.inn', lang)}: {state_data.get('inn')}\n"
        f"{_.get_text('wa_patent.edit_wa_data.policy', lang)}: {state_data.get('policy_number')}, {state_data.get('medical_policy_company')}, {state_data.get('medical_policy_polis_date')}\n"
        f"{_.get_text('wa_patent.edit_wa_data.phone_number', lang)}: {state_data.get('phone_number')}"
    )
    await message.answer(
        text=text,
        reply_markup=kbs_policy_data_confirmation(lang)
    )


# ─────────────────────────── Утилиты и генерация ───────────────────────────

def to_uppercase(data: dict) -> dict:
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = to_uppercase(value)
        elif isinstance(value, str):
            result[key] = value.upper()
        else:
            result[key] = value
    return result


def split_series_number(doc: str):
    doc = doc.strip()

    # 1) Если только цифры → номер
    if doc.isdigit():
        return {"серия": "", "номер": doc}

    # 2) Есть "-" или "/"
    if "-" in doc or "/" in doc:
        match = re.match(r"^(.*?)[-/](.+)$", doc)
        if match:
            series, number = match.groups()
            return {"серия": series, "номер": number}

    # 3) Всё остальное → в номер
    return {"серия": "", "номер": doc}


@work_activity_router.callback_query(F.data == "accept_wa_patent_data")
async def handle_all_true_in_wa(callback: CallbackQuery, state: FSMContext):
    """Подтверждение → сохраняем, генерим DOCX и отправляем пользователю."""
    state_data = await state.get_data()
    session_id = state_data.get("session_id")
    lang = state_data.get("language")

    # Разрезаем строки под макет
    mvd_adress = state_data.get("department_full_name") or ""
    mvd_adress_1 = mvd_adress[:31]
    mvd_adress_2 = mvd_adress[31:31*2]
    mvd_adress_3 = mvd_adress[31*2:31*3]

    passport_data = state_data.get("passport_data", {}) or {}
    full_name = passport_data.get("full_name", "")
    parts = full_name.split() if full_name else []
    name = parts[1] if len(parts) > 1 else ""
    first_name = parts[0] if len(parts) > 0 else ""
    father_name = parts[2] if len(parts) > 2 else ""

    birth_date = passport_data.get("birth_date", "") or ""
    bd = birth_date.split(".") if birth_date else []
    birth_date_day = bd[0] if len(bd) > 0 else ""
    birth_date_month = bd[1] if len(bd) > 1 else ""
    birth_date_year = bd[2] if len(bd) > 2 else ""

    pid = passport_data.get("passport_issue_date", "") or ""
    pidp = pid.split(".") if pid else []
    passport_issue_date_day = pidp[0] if len(pidp) > 0 else ""
    passport_issue_date_month = pidp[1] if len(pidp) > 1 else ""
    passport_issue_date_year = pidp[2] if len(pidp) > 2 else ""

    passport_issue_place = (
            passport_data.get("passport_issue_place")
            or passport_data.get("passport_issued")
            or ""
    )
    passport_issue_place_1 = passport_issue_place[:25]
    passport_issue_place_2 = passport_issue_place[25:25 * 2 + 1]

    patient_data = state_data.get("patient_data", {}) or {}
    pn = (patient_data.get("patient_number") or "")
    patent_series = pn[:2]
    patent_numbers = pn[2:].replace("-", "").replace(" ", "")

    pdate = patient_data.get("patient_date") or ""
    pdp = pdate.split(".") if pdate else []
    patent_issue_date_day = pdp[0] if len(pdp) > 0 else ""
    patent_issue_date_month = pdp[1] if len(pdp) > 1 else ""
    patent_issue_date_year = pdp[2] if len(pdp) > 2 else ""

    job_name = state_data.get("work_name", "") or ""
    job_name_1 = job_name[:31]
    job_name_2 = job_name[31:31*2]
    job_name_3 = job_name[31*2:31*3]

    work_adress = state_data.get("emp_adress", "") or ""
    work_adress_1 = work_adress[:31]
    work_adress_2 = work_adress[31:31*2]

    med_data_name = state_data.get("medical_policy_company", "") or ""
    med_data_name_1 = med_data_name[:32]
    med_data_name_2 = med_data_name[32:32*2]
    med_data_name_3 = med_data_name[32*2:32*3]

    med_policy_date = state_data.get("medical_policy_polis_date", "") or ""
    med_data_issue_date_day = med_data_issue_date_month = med_data_issue_date_year = ""
    if " по " in med_policy_date:
        start, _end = med_policy_date.split(" по ", 1)  # не трогаем alias локализации
        start = start.replace("с ", "").strip()
        s = start.split(".")
        med_data_issue_date_day = s[0] if len(s) > 0 else ""
        med_data_issue_date_month = s[1] if len(s) > 1 else ""
        med_data_issue_date_year = s[2] if len(s) > 2 else ""

    med_policy_series_number = state_data.get("policy_number", "") or ""
    med_policy_sn = split_series_number(med_policy_series_number)
    med_data_series = med_policy_sn.get("серия", "")
    med_data_numbers = med_policy_sn.get("номер", "")

    # Сохраняем короткую сводку
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
        user_id=callback.from_user.id,
        session_id=session_id,
        data=user_data
    )

    # Контекст для DOCX
    data = {
        "char_mvd_adress_short_1": mvd_adress_1,
        "char_mvd_adress_short_2": mvd_adress_2,
        "char_mvd_adress_short_3": mvd_adress_3,
        "char_first_name": first_name,
        "char_name": name,
        "char_father_name": father_name,
        "char_cityzenship": passport_data.get("citizenship", ""),
        "char_birth_date_day": birth_date_day,
        "char_birth_date_month": birth_date_month,
        "char_birth_date_year": birth_date_year,
        "char_passport_series": (passport_data.get("passport_serial_number", "") or "")[:2],
        "char_passport_numbers": (passport_data.get("passport_serial_number", "") or "")[2:],
        "char_passport_issue_date_day": passport_issue_date_day,
        "char_passport_issue_date_month": passport_issue_date_month,
        "char_passport_issue_date_year": passport_issue_date_year,
        "char_passport_issue_place_short_1": passport_issue_place_1,
        "char_passport_issue_place_short_2": passport_issue_place_2,
        "char_patent_series": patent_series,
        "char_patent_numbers": patent_numbers,
        "char_patent_issue_date_day": patent_issue_date_day,
        "char_patent_issue_date_month": patent_issue_date_month,
        "char_patent_issue_date_year": patent_issue_date_year,
        "char_job_name_short_1": job_name_1,
        "char_job_name_short_2": job_name_2,
        "char_job_name_short_3": job_name_3,
        "char_work_adress_short_1": work_adress_1,
        "char_work_adress_short_2": work_adress_2,
        "char_inn": state_data.get("inn", ""),
        "char_med_data_name_short_1": med_data_name_1,
        "char_med_data_name_short_2": med_data_name_2,
        "char_med_data_name_short_3": med_data_name_3,
        "char_med_data_series": med_data_series,
        "char_med_data_numbers": med_data_numbers,
        "char_med_data_issue_date_day": med_data_issue_date_day,
        "char_med_data_issue_date_month": med_data_issue_date_month,
        "char_med_data_issue_date_year": med_data_issue_date_year,
        "char_phone": state_data.get("phone_number", ""),
    }
    data = to_uppercase(data)

    doc = create_user_doc(
        context=data,
        template_name='working_notification',
        user_path='pdf_generator',
        font_name="Times New Roman"
    )
    ready_doc = FSInputFile(doc, filename='Уведомление о трудовой деятельности по патенту.docx')

    await state.clear()

    text = f"{_.get_text('ready_to_download_doc', lang)}\n"
    await callback.message.edit_text(text=text)
    await callback.message.answer_document(document=ready_doc)


# ─────────────────────────── Редактор данных (UI) ──────────────────────────

@work_activity_router.callback_query(F.data == "edit_wa_patent_data")
async def edit_wa_data(query: CallbackQuery, state: FSMContext):
    """Главный редактор: показываем, что можно поправить."""
    lang = (await state.get_data()).get("language")
    text = f"{_.get_text('wa_patent.wa_data_editor.title', lang)}"
    await query.message.edit_text(text=text, reply_markup=kbs_edit_wa_data(lang))


@work_activity_router.callback_query(F.data.startswith("wa_edit_"))
async def wa_editor(query: CallbackQuery, state: FSMContext):
    """Переходы в подредакторы (паспорт/патент/полис/поля)."""
    param_to_edit = query.data[len("wa_edit_"):]
    lang = (await state.get_data()).get("language")

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
        text = (
            f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.title', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.description', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.example', lang)}"
        )
        await query.message.edit_text(text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_start)

    elif param_to_edit == "work_adress":
        text = (
            f"{_.get_text('wa_patent.wa_patent_medical_policy.employer_address.title', lang)}\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy.employer_address.example', lang)}"
        )
        await query.message.edit_text(text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_emp_adress)

    elif param_to_edit == "inn":
        text = (
            f"{_.get_text('wa_patent.wa_patent_medical_policy.INN.title', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy.INN.format', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy.INN.example', lang)}"
        )
        await query.message.edit_text(text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_inn)

    elif param_to_edit == "policy":
        text = f"{_.get_text('wa_patent.wa_data_editor.sub_editor_data.policy.title', lang)}"
        await query.message.edit_text(text=text, reply_markup=kbs_sub_editor_policy(lang))

    elif param_to_edit == "phone_number":
        await state.set_state(PatentedWorkActivity.edit_phone_number)
        text = _.get_text("wa_patent.wa_data_editor.sub_editor_data.phone_number.title", lang)
        await query.message.edit_text(text)

    else:
        await get_medical_policy_polis_date(query.message, state)


@work_activity_router.message(PatentedWorkActivity.edit_phone_number)
async def phone_number_editor(message: Message, state: FSMContext):
    """Редактирование телефона через главный редактор."""
    phone_number = message.text.strip()
    await state.update_data(phone_number=phone_number)
    await get_medical_policy_polis_date(message, state)


@work_activity_router.callback_query(F.data.startswith("edit_policy_"))
async def medical_policy_editor(query: CallbackQuery, state: FSMContext):
    """Подредактор полиса ДМС."""
    param_to_edit = query.data[len("edit_policy_"):]
    lang = (await state.get_data()).get("language")

    if param_to_edit == "number":
        text = (
            f"{_.get_text('wa_patent.wa_patent_medical_policy_number.title', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy_number.description', lang)}\n"
            f"{_.get_text('wa_patent.wa_patent_medical_policy_number.example', lang)}"
        )
        await query.message.edit_text(text=text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_company)

    if param_to_edit == "company":
        text = (
            f"{_.get_text('wa_patent.wa_patent_insurance_company.title', lang)}\n"
            f"{_.get_text('wa_patent.wa_patent_insurance_company.example', lang)}"
        )
        await query.message.edit_text(text=text)
        await state.update_data(edit_mode=True)
        await state.set_state(PatentedWorkActivity.medical_policy_validity_period)

    if param_to_edit == "dateof":
        text = (
            f"{_.get_text('wa_patent.wa_polis_date.title', lang)}\n\n"
            f"{_.get_text('wa_patent.wa_polis_date.description', lang)}"
        )
        await query.message.edit_text(text=text)
        await state.set_state(PatentedWorkActivity.medical_policy_polis_date)


@work_activity_router.callback_query(F.data.startswith("edit_passport_"))
async def edit_passport_data_fields(query: CallbackQuery, state: FSMContext):
    """Подредактор полей паспорта."""
    param_to_edit = query.data[len("edit_passport_"):]
    lang = (await state.get_data()).get("language")

    if param_to_edit == "full_name":
        text = f"{_.get_text('passport_manual_full_name.description', lang)}"
        await query.message.edit_text(text=text)
        await state.update_data(edit_passport_field=param_to_edit)

    elif param_to_edit in ["passport_serial_number", "passport_issue_date", "passport_issued", "passport_expiry_date"]:
        text = _.get_text(f"wa_patent.wa_data_editor.sub_editor_data.passport.{param_to_edit}", lang)
        await state.update_data(edit_passport_field=param_to_edit)
        await query.message.edit_text(text=text)

    await state.set_state(PatentedWorkActivity.edit_passport_fields)


@work_activity_router.message(PatentedWorkActivity.edit_passport_fields)
async def edit_passport_fields(message: Message, state: FSMContext):
    """Принимает новое значение поля паспорта и возвращает на сводку."""
    state_data = await state.get_data()
    field = state_data.get("edit_passport_field")
    passport = state_data.get("passport_data", {}) or {}
    passport[field] = message.text.strip()
    await state.update_data(passport_data=passport, edit_passport_field=None)
    await get_medical_policy_polis_date(message, state)


@work_activity_router.callback_query(F.data.startswith("edit_patent_"))
async def edit_patent_data_fields(query: CallbackQuery, state: FSMContext):
    """Подредактор полей патента."""
    param_to_edit = query.data[len("edit_patent_"):]
    lang = (await state.get_data()).get("language")

    if param_to_edit in ["patient_number", "patient_date", "patient_issue_place"]:
        text = _.get_text(f"wa_patent.wa_data_editor.sub_editor_data.patent.{param_to_edit}", lang)
        await query.message.edit_text(text=text)
        await state.set_state(PatentedWorkActivity.edit_patent_fields)
        await state.update_data(edit_patent_fields=param_to_edit)


@work_activity_router.message(PatentedWorkActivity.edit_patent_fields)
async def edit_patent_fields_message(message: Message, state: FSMContext):
    """Принимает новое значение поля патента и возвращает на сводку."""
    state_data = await state.get_data()
    field = state_data.get("edit_patent_fields")
    await state.update_data({field: message.text.strip()}, edit_patent_fields=None)
    await get_medical_policy_polis_date(message, state)
