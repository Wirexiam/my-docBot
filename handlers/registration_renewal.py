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
    """Старт процесса продления регистрации"""
    await state.set_state(RegistrationRenewalStates.waiting_confirm_registration_renewal_start)
    lang = (await state.get_data()).get("language")
    await state.update_data(from_action="registration_renewal_after_mvd")
    text = (
        f"{_.get_text('registration_renewal_start.title', lang)}\n"
        f"{_.get_text('registration_renewal_start.description', lang)}\n"
        f"{_.get_text('registration_renewal_start.documents_to_prepare', lang)}"
    )
    await callback.message.edit_text(text, reply_markup=get_registration_renewal_start_keyboard(lang))


# ───────────────────────── МВД ─────────────────────────

@registration_renewal_router.callback_query(F.data == "registration_renewal_after_mvd")
async def handle_registration_renewal_after_mvd(callback: CallbackQuery, state: FSMContext):
    """После выбора МВД"""
    await state.set_state(RegistrationRenewalStates.after_select_mvd)
    sd = await state.get_data()
    lang, mvd_adress, session_id = sd.get("language"), sd.get("mvd_adress"), sd.get("session_id")
    data_manager.save_user_data(callback.from_user.id, session_id, {"mvd_adress": mvd_adress})
    await state.update_data(from_action=RegistrationRenewalStates.after_passport,
                            passport_title="registration_renewal_passport_title")
    text = (
        f"{_.get_text('registration_renewal_start_passport.title', lang)}\n"
        f"{_.get_text('registration_renewal_start_passport.description', lang)}"
    )
    await callback.message.edit_text(text, reply_markup=get_registration_renewal_passport_start_keyboard(lang))


# ───────────────────────── Паспорт (ручной ввод) ─────────────────────────

@registration_renewal_router.message(RegistrationRenewalStates.after_passport)
async def handle_registration_renewal_after_passport(message: Message, state: FSMContext):
    """После паспорта → выбор основания"""
    sd = await state.get_data()
    lang, waiting_data, session_id = sd.get("language"), sd.get("waiting_data"), sd.get("session_id")

    if waiting_data:
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(message.from_user.id, session_id, {waiting_data: message.text.strip()})

    await state.update_data(next_states=[LiveAdress.adress],
                            from_action=RegistrationRenewalStates.after_residence_reason_and_location)
    text = _.get_text("registration_renewal_residence_reason.title", lang)
    await message.answer(text=text, reply_markup=get_registration_renewal_residence_reason_keyboard(lang))


# ───────────────────────── Паспорт (OCR мини-сводка → кнопка) ─────────────────────────

@registration_renewal_router.callback_query(F.data == "sp_after_passport")
async def handle_sp_after_passport(callback: CallbackQuery, state: FSMContext):
    """После паспорта по OCR → выбор основания"""
    sd = await state.get_data()
    lang = sd.get("language")
    await state.update_data(next_states=[LiveAdress.adress],
                            from_action=RegistrationRenewalStates.after_residence_reason_and_location)
    text = _.get_text("registration_renewal_residence_reason.title", lang)
    await callback.message.edit_text(text=text, reply_markup=get_registration_renewal_residence_reason_keyboard(lang))


# ───────────────────────── Выбор основания (ребёнок) ─────────────────────────

@registration_renewal_router.callback_query(F.data.startswith("residence_reason_child_"))
async def handle_residence_reason_child(callback: CallbackQuery, state: FSMContext):
    who_for_child = callback.data.split("child_")[1]
    sd = await state.get_data()
    lang = sd.get("language")
    child_data = sd.get("child_data", {})
    child_data["who_for_child"] = who_for_child
    await state.update_data(child_data=child_data, waiting_data="live_adress")

    photo = FSInputFile("static/live_adress_example.png")
    text = f"{_.get_text('live_adress.title', lang)}\n{_.get_text('live_adress.example', lang)}"
    await callback.message.answer_photo(caption=text, photo=photo)

    next_states, from_action = sd.get("next_states", []), sd.get("from_action")
    if next_states:
        await state.update_data(next_states=next_states[1:])
        await state.set_state(next_states[0])
    else:
        await state.set_state(from_action)


# ───────────────────────── После адреса + основания → финалка ─────────────────────────

@registration_renewal_router.message(RegistrationRenewalStates.after_residence_reason_and_location)
async def handle_registration_renewal_after_residence_reason_and_location(message: Message, state: FSMContext):
    """Финальная проверка данных"""
    sd = await state.get_data()
    lang, waiting_data, session_id = sd.get("language"), sd.get("waiting_data"), sd.get("session_id")

    if waiting_data:
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(message.from_user.id, session_id, {waiting_data: message.text.strip()})

    # формируем сводку (короче чем твоя, но все данные на месте)
    passport = sd.get("passport_data", {})
    residence_reason = sd.get("residence_reason")
    text = f"{_.get_text(f'registration_renewal_{residence_reason}_check_data.title', lang)}\n\n"
    text += f"👤 {passport.get('full_name', '—')}\n"
    text += f"🗓 {passport.get('birth_date', '—')}\n"
    text += f"🌍 {passport.get('citizenship', '—')}\n"
    text += f"📄 {passport.get('passport_serial_number', '—')}, {passport.get('passport_issue_date', '—')} {passport.get('passport_issue_place', '—')} до {passport.get('passport_expiry_date', '—')}\n"
    text += f"🏠 {sd.get('live_adress', '—')}\n"

    await message.answer(text, reply_markup=get_registration_renewal_after_residence_reason_and_location_keyboard(lang))


# ───────────────────────── Генерация DOCX ─────────────────────────

@registration_renewal_router.callback_query(F.data == "registration_renewal_patient_check_data_all_true")
async def patent_get_pdf(query: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang, who = sd.get("language"), sd.get("who")

    ready_doc = None
    if who == "patient":
        doc = create_user_doc(sd, "template_for_patient", "pdf_generator", font_name="Arial")
        ready_doc = FSInputFile(doc, filename="Заявление_о_продление_по_патенту.docx")
    elif who == "child":
        doc = create_user_doc(sd, "template_for_patient_child", "pdf_generator", font_name="Arial")
        ready_doc = FSInputFile(doc, filename="Заявление_о_продлении_по_ребенку.docx")
    else:
        doc = create_user_doc(sd, "template_for_patient_marriage_person", "pdf_generator", font_name="Arial")
        ready_doc = FSInputFile(doc, filename="Заявление_о_продлениеи_по_браку.docx")

    text = _.get_text("ready_to_download_doc", lang)
    await query.message.edit_text(text=text)
    await query.message.answer_document(document=ready_doc)
