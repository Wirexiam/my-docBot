from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from pdf_generator.gen_pdf import create_user_doc
from states.registration_renewal import RegistrationRenewalStates
from states.components.live_adress import LiveAdress
from keyboards.registration_renewal import (
    get_registration_renewal_start_keyboard,
    get_registration_renewal_passport_start_keyboard,
    get_registration_renewal_residence_reason_keyboard,
    get_registration_renewal_after_residence_reason_and_location_keyboard,
)
from localization import _
from data_manager import SecureDataManager

registration_renewal_router = Router()
data_manager = SecureDataManager()


# ───────────────────────── старт ─────────────────────────
@registration_renewal_router.callback_query(F.data == "registration_renewal")
async def handle_registration_renewal_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(
        RegistrationRenewalStates.waiting_confirm_registration_renewal_start
    )
    sd = await state.get_data()
    lang = sd.get("language")
    await state.update_data(from_action="registration_renewal_after_mvd")
    text = (
        f"{_.get_text('registration_renewal_start.title', lang)}\n"
        f"{_.get_text('registration_renewal_start.description', lang)}\n"
        f"{_.get_text('registration_renewal_start.documents_to_prepare', lang)}"
    )
    await callback.message.edit_text(
        text=text, reply_markup=get_registration_renewal_start_keyboard(lang)
    )


# ───────────────────────── МВД ─────────────────────────
@registration_renewal_router.callback_query(F.data == "registration_renewal_after_mvd")
async def handle_registration_renewal_after_mvd(
    callback: CallbackQuery, state: FSMContext
):
    await state.set_state(RegistrationRenewalStates.after_select_mvd)
    sd = await state.get_data()
    lang = sd["language"]
    mvd_adress = sd.get("mvd_adress")
    session_id = sd.get("session_id")
    data_manager.save_user_data(
        callback.from_user.id, session_id, {"mvd_adress": mvd_adress}
    )

    # ВАЖНО: отделяемся от штампа
    await state.update_data(
        ocr_flow="sp",
        from_action=RegistrationRenewalStates.after_passport,
        passport_title="registration_renewal_passport_title",
        next_states=[],  # не тянуть чужие next_states
    )

    text = (
        f"{_.get_text('registration_renewal_start_passport.title', lang)}\n"
        f"{_.get_text('registration_renewal_start_passport.description', lang)}"
    )
    await callback.message.edit_text(
        text=text, reply_markup=get_registration_renewal_passport_start_keyboard(lang)
    )


# ───────────────────────── Паспорт (ручной) ─────────────────────────
@registration_renewal_router.message(RegistrationRenewalStates.after_passport)
async def handle_registration_renewal_after_passport(
    message: Message, state: FSMContext
):
    sd = await state.get_data()
    lang = sd.get("language")
    waiting_data = sd.get("waiting_data")
    session_id = sd.get("session_id")

    if waiting_data:
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(
            message.from_user.id, session_id, {waiting_data: message.text.strip()}
        )

    await state.update_data(
        next_states=[LiveAdress.adress],
        from_action=RegistrationRenewalStates.after_residence_reason_and_location,
    )
    text = _.get_text("registration_renewal_residence_reason.title", lang)
    await message.answer(
        text=text, reply_markup=get_registration_renewal_residence_reason_keyboard(lang)
    )


# ───────────────────────── Паспорт (OCR мини-сводка → кнопка) ─────────────────────────
@registration_renewal_router.callback_query(F.data == "sp_after_passport")
async def handle_sp_after_passport(callback: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    await state.update_data(
        next_states=[LiveAdress.adress],
        from_action=RegistrationRenewalStates.after_residence_reason_and_location,
        residence_reason=None,
        who=None,
    )
    await callback.message.edit_text(
        text=_.get_text("registration_renewal_residence_reason.title", lang),
        reply_markup=get_registration_renewal_residence_reason_keyboard(lang),
    )


# ───────────────────────── После адреса + основания → финалка ─────────────────────────
@registration_renewal_router.message(
    RegistrationRenewalStates.after_residence_reason_and_location
)
async def handle_registration_renewal_after_residence_reason_and_location(
    message: Message, state: FSMContext
):
    sd = await state.get_data()
    lang = sd.get("language")
    waiting_data = sd.get("waiting_data")
    session_id = sd.get("session_id")

    if waiting_data:
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(
            message.from_user.id, session_id, {waiting_data: message.text.strip()}
        )

    await state.update_data(
        from_action=RegistrationRenewalStates.after_residence_reason_and_location,
        change_data_from_check="registrationrenewalstates_after_residence_reason_and_location",
    )

    passport = sd.get("passport_data", {}) or {}
    pn = passport.get("passport_serial_number", "Не найдено")
    pid = passport.get("passport_issue_date", "Не найдено")
    pip = passport.get("passport_issue_place", "Не найдено")
    ped = passport.get("passport_expiry_date", "Не найдено")
    residence_reason = sd.get("residence_reason", "Не найдено")

    # формируем текст по резону (как у тебя было, только с безопасными кавычками)
    if residence_reason == "residence_reason_patent":
        patient = sd.get("patient_data", {}) or {}
        await state.update_data(who="patient")
        text = (
            f"{_.get_text('registration_renewal_patient_check_data.title', lang)}\n\n"
            f"{_.get_text('registration_renewal_patient_check_data.full_name', lang)}{passport.get('full_name','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.birth_date', lang)}{passport.get('birth_date','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.citizenship', lang)}{passport.get('citizenship','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{pn}"
            f"{_.get_text('registration_renewal_patient_check_data.issue_date', lang)}{pid} {pip}"
            f"{_.get_text('registration_renewal_patient_check_data.expiry_date', lang)}{ped}\n"
            f"{_.get_text('registration_renewal_patient_check_data.adress', lang)}{sd.get('live_adress','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.residence_reason', lang)}\n"
            f"{_.get_text('registration_renewal_patient_check_data.patient_number', lang)}{patient.get('patient_number','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.patient_date', lang)}{patient.get('patient_date','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.patient_issue_place', lang)}{patient.get('patient_issue_place','Не найдено')}\n\n"
        )
    elif residence_reason == "residence_reason_marriage":
        marriage = sd.get("marriage_data", {}) or {}
        await state.update_data(who="marriage")
        text = (
            f"{_.get_text('registration_renewal_marriage_check_data.title', lang)}\n\n"
            f"{_.get_text('registration_renewal_marriage_check_data.full_name', lang)}{passport.get('full_name','Не найдено')}\n"
            f"{_.get_text('registration_renewal_marriage_check_data.birth_date', lang)}{passport.get('birth_date','Не найдено')}\n"
            f"{_.get_text('registration_renewal_marriage_check_data.citizenship', lang)}{passport.get('citizenship','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{pn}"
            f"{_.get_text('registration_renewal_patient_check_data.issue_date', lang)}{pid} {pip}"
            f"{_.get_text('registration_renewal_patient_check_data.expiry_date', lang)}{ped}\n"
            f"{_.get_text('registration_renewal_marriage_check_data.adress', lang)}{sd.get('live_adress','Не найдено')}\n"
            f"{_.get_text('registration_renewal_marriage_check_data.residence_reason', lang)}\n"
            f"{_.get_text('registration_renewal_marriage_check_data.spouse_fio', lang)}{marriage.get('spouse_fio','Не найдено')}\n"
            f"{_.get_text('registration_renewal_marriage_check_data.marriage_citizenship', lang)}{marriage.get('marriage_citizenship','Не найдено')}\n"
            f"{_.get_text('registration_renewal_marriage_check_data.marriage_certificate_number', lang)}{marriage.get('marriage_number','Не найдено')}"
            f"{_.get_text('registration_renewal_marriage_check_data.issue_place', lang)}\n{marriage.get('issue_date','Не найдено')} {marriage.get('marriage_issue_place','Не найдено')}"
        )
    else:  # residence_reason_child
        child = sd.get("child_data", {}) or {}
        await state.update_data(who="child")
        text = (
            f"{_.get_text('registration_renewal_child_check_data.title', lang)}\n\n"
            f"{_.get_text('registration_renewal_child_check_data.full_name', lang)}{passport.get('full_name','Не найдено')}\n"
            f"{_.get_text('registration_renewal_child_check_data.birth_date', lang)}{passport.get('birth_date','Не найдено')}\n"
            f"{_.get_text('registration_renewal_child_check_data.citizenship', lang)}{passport.get('citizenship','Не найдено')}\n"
            f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{pn}"
            f"{_.get_text('registration_renewal_patient_check_data.issue_date', lang)}{pid} {pip}"
            f"{_.get_text('registration_renewal_patient_check_data.expiry_date', lang)}{ped}\n"
            f"{_.get_text('registration_renewal_child_check_data.adress', lang)}{sd.get('live_adress','Не найдено')}\n"
            f"{_.get_text('registration_renewal_child_check_data.residence_reason', lang)}\n"
            f"{_.get_text('registration_renewal_child_check_data.child_fio', lang)}{child.get('child_fio','Не найдено')}\n"
            f"{_.get_text('registration_renewal_child_check_data.child_birth_date', lang)}{child.get('child_birth_date','Не найдено')}\n"
            f"{_.get_text('registration_renewal_child_check_data.child_citizenship', lang)}{child.get('child_citizenship','Не найдено')}\n"
            f"{_.get_text('registration_renewal_child_check_data.child_certificate_number', lang)}{child.get('child_certificate_number','Не найдено')}"
            f"{_.get_text('registration_renewal_child_check_data.issue_place', lang)}\n{child.get('child_certificate_issue_place','Не найдено')}\n"
        )

    text += f"\n{_.get_text('stamp_check_datas_info.mvd_adress', lang)}{sd.get('mvd_adress', 'Не найдено')}"
    await message.answer(
        text=text,
        reply_markup=get_registration_renewal_after_residence_reason_and_location_keyboard(
            lang
        ),
    )


# ───────────────────────── Генерация DOCX ─────────────────────────
@registration_renewal_router.callback_query(
    F.data == "registration_renewal_patient_check_data_all_true"
)
async def patent_get_pdf(query: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    who = sd.get("who")
    ready_doc = None

    if who == "patient":
        data = {
            "live_adress": sd.get("live_adress", ""),
            "mvd_adress": sd.get("mvd_adress", ""),
            "fio": sd.get("passport_data", {}).get("full_name", ""),
            "birth_data": sd.get("passport_data", {}).get("birth_date", ""),
            "citizenship": sd.get("passport_data", {}).get("citizenship", ""),
            "serial_number": sd.get("passport_data", {}).get(
                "passport_serial_number", ""
            ),
            "passport_issue_date": sd.get("passport_data", {}).get(
                "passport_issue_date", ""
            ),
            "passport_issue_place": sd.get("passport_data", {}).get(
                "passport_issue_place", ""
            ),
            "passport_expiry_date": sd.get("passport_data", {}).get(
                "passport_expiry_date", ""
            ),
            "patient_serial_number": sd.get("patient_data", {}).get(
                "patient_number", ""
            ),
            "patient_issue_place": sd.get("patient_data", {}).get(
                "patient_issue_place", ""
            ),
            "patient_date": sd.get("patient_data", {}).get("patient_date", ""),
            "phone_parent": sd.get("phone_number", ""),
        }
        doc = create_user_doc(
            context=data,
            template_name="template_for_patient",
            user_path="pdf_generator",
            font_name="Arial",
        )
        ready_doc = FSInputFile(doc, filename="Заявление_о_продление_по_патенту.docx")

    elif who == "child":
        who_for = (sd.get("child_data", {}) or {}).get("who_for_child", "")
        parent = (
            "отец"
            if who_for == "father"
            else ("мать" if who_for == "mother" else "опекун")
        )
        data = {
            "child_fio": sd.get("child_data", {}).get("child_fio", ""),
            "child_ship": sd.get("child_data", {}).get("child_citizenship", ""),
            "child_date_birth": sd.get("child_data", {}).get("child_birth_date", ""),
            "child_certificate_number": sd.get("child_data", {}).get(
                "child_certificate_number", ""
            ),
            "child_certificate_issue_place": sd.get("child_data", {}).get(
                "child_certificate_issue_place", ""
            ),
            "parent": parent,
            "live_adress": sd.get("live_adress", ""),
            "mvd_adress": sd.get("mvd_adress", ""),
            "fio": sd.get("passport_data", {}).get("full_name", ""),
            "birth_data": sd.get("passport_data", {}).get("birth_date", ""),
            "citizenship": sd.get("passport_data", {}).get("citizenship", ""),
            "serial_number": sd.get("passport_data", {}).get(
                "passport_serial_number", ""
            ),
            "passport_issue_date": sd.get("passport_data", {}).get(
                "passport_issue_date", ""
            ),
            "passport_issue_place": sd.get("passport_data", {}).get(
                "passport_issue_place", ""
            ),
            "passport_expiry_date": sd.get("passport_data", {}).get(
                "passport_expiry_date", ""
            ),
            "phone_parent": sd.get("phone_number", ""),
        }
        doc = create_user_doc(
            context=data,
            template_name="template_for_patient_child",
            user_path="pdf_generator",
            font_name="Arial",
        )
        ready_doc = FSInputFile(doc, filename="Заявление_о_продлении_по_ребенку.docx")

    else:  # marriage
        data = {
            "marry_fio": sd.get("marriage_data", {}).get("spouse_fio", ""),
            "marry_issue_date": sd.get("marriage_data", {}).get("issue_date", ""),
            "data_get_marriage_doc": sd.get("marriage_data", {}).get("issue_data", ""),
            "marriage_number": sd.get("marriage_data", {}).get("marriage_number", ""),
            "marriage_issue_place": sd.get("marriage_data", {}).get(
                "marriage_issue_place", ""
            ),
            "live_adress": sd.get("live_adress", ""),
            "mvd_adress": sd.get("mvd_adress", ""),
            "fio": sd.get("passport_data", {}).get("full_name", ""),
            "birth_data": sd.get("passport_data", {}).get("birth_date", ""),
            "citizenship": sd.get("passport_data", {}).get("citizenship", ""),
            "serial_number": sd.get("passport_data", {}).get(
                "passport_serial_number", ""
            ),
            "passport_issue_date": sd.get("passport_data", {}).get(
                "passport_issue_date", ""
            ),
            "passport_issue_place": sd.get("passport_data", {}).get(
                "passport_issue_place", ""
            ),
            "passport_expiry_date": sd.get("passport_data", {}).get(
                "passport_expiry_date", ""
            ),
            "phone_parent": sd.get("phone_number", ""),
        }
        doc = create_user_doc(
            context=data,
            template_name="template_for_patient_marriage_person",
            user_path="pdf_generator",
            font_name="Arial",
        )
        ready_doc = FSInputFile(doc, filename="Заявление_о_продлениеи_по_браку.docx")

    text = f"{_.get_text('ready_to_download_doc', lang)}\n"
    await query.message.edit_text(text=text)
    await query.message.answer_document(document=ready_doc)
