from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from localization import _
from states.components.residence_reason_marriage import ResidenceReasonMarriageStates
from states.components.live_adress import LiveAdress

residence_reason_marriage_router = Router()


# ───────────────────────── старт «По браку» ─────────────────────────
@residence_reason_marriage_router.callback_query(F.data == "residence_reason_marriage")
async def start_marriage_flow(callback: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    await state.update_data(
        residence_reason="residence_reason_marriage",
        who="marriage",
        marriage_data=sd.get("marriage_data", {}) or {},
    )

    title = _.get_text("residence_reason_manual_marriage_messages.spouse_fio.title", lang)
    example = _.get_text("residence_reason_manual_marriage_messages.spouse_fio.example_text", lang)

    await state.set_state(ResidenceReasonMarriageStates.spouse_fio)
    await callback.message.edit_text(f"{title}\n{example}")


# ───────────────────────── ФИО супруга → дата рождения ─────────────────────────
@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.spouse_fio)
async def get_spouse_fio(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    marriage_data = dict(sd.get("marriage_data") or {})
    marriage_data["spouse_fio"] = (message.text or "").strip()
    await state.update_data(marriage_data=marriage_data)

    title = _.get_text("residence_reason_manual_marriage_messages.spouse_birth_date.title", lang)
    example = _.get_text("residence_reason_manual_marriage_messages.spouse_birth_date.example_text", lang)

    await state.set_state(ResidenceReasonMarriageStates.spouse_birth_date)
    await message.answer(f"{title}\n{example}")


# ───────────────────────── дата рождения → гражданство супруга ─────────────────────────
@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.spouse_birth_date)
async def get_spouse_birth_date(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    marriage_data = dict(sd.get("marriage_data") or {})
    marriage_data["spouse_birth_date"] = (message.text or "").strip()
    await state.update_data(marriage_data=marriage_data)

    title = _.get_text("residence_reason_manual_marriage_messages.marriage_citizenship.title", lang)
    example = _.get_text("residence_reason_manual_marriage_messages.marriage_citizenship.example_text", lang)

    await state.set_state(ResidenceReasonMarriageStates.marriage_citizenship)
    await message.answer(f"{title}\n{example}")


# ───────────────────────── гражданство супруга → № свидетельства ─────────────────────────
@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.marriage_citizenship)
async def get_marriage_citizenship(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    marriage_data = dict(sd.get("marriage_data") or {})
    marriage_data["marriage_citizenship"] = (message.text or "").strip()
    await state.update_data(marriage_data=marriage_data)

    title = _.get_text("residence_reason_manual_marriage_messages.marriage_number.title", lang)
    example = _.get_text("residence_reason_manual_marriage_messages.marriage_number.example_text", lang)

    await state.set_state(ResidenceReasonMarriageStates.marriage_number)
    await message.answer(f"{title}\n{example}")


# ───────────────────────── № свидетельства → дата выдачи ─────────────────────────
@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.marriage_number)
async def get_marriage_number(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    marriage_data = dict(sd.get("marriage_data") or {})
    marriage_data["marriage_number"] = (message.text or "").strip()
    await state.update_data(marriage_data=marriage_data)

    title = _.get_text("residence_reason_manual_marriage_messages.issue_date.title", lang)
    example = _.get_text("residence_reason_manual_marriage_messages.issue_date.example_text", lang)

    await state.set_state(ResidenceReasonMarriageStates.issue_date)
    await message.answer(f"{title}\n{example}")


# ───────────────────────── дата выдачи → КЕМ выдано ─────────────────────────
@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.issue_date)
async def get_issue_date(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    marriage_data = dict(sd.get("marriage_data") or {})
    marriage_data["issue_date"] = (message.text or "").strip()
    await state.update_data(marriage_data=marriage_data)

    title = _.get_text("residence_reason_manual_marriage_messages.marriage_issue_place.title", lang)
    example = _.get_text("residence_reason_manual_marriage_messages.marriage_issue_place.example_text", lang)

    await state.set_state(ResidenceReasonMarriageStates.issue_place)
    await message.answer(f"{title}\n{example}")


# ───────────────────────── КЕМ выдано → адрес проживания ─────────────────────────
@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.issue_place)
async def get_marriage_issue_place(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    marriage_data = dict(sd.get("marriage_data") or {})
    marriage_data["marriage_issue_place"] = (message.text or "").strip()

    await state.update_data(marriage_data=marriage_data, who="marriage", waiting_data="live_adress")

    photo = FSInputFile("static/live_adress_example.png")
    caption = f"{_.get_text('live_adress.title', lang)}\n{_.get_text('live_adress.example', lang)}"
    await message.answer_photo(photo=photo, caption=caption)

    await state.set_state(LiveAdress.adress)
