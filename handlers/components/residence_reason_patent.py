# handlers/components/residence_reason_patent.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from localization import _
from states.components.residence_reason_patent import ResidenceReasonPatentStates
from states.components.live_adress import LiveAdress

residence_reason_patient_router = Router()


# ───────────────────────── старт «По патенту» ─────────────────────────
@residence_reason_patient_router.callback_query(F.data == "residence_reason_patent")
async def start_patient_flow(callback: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    # помечаем основание + инициализируем контейнер
    await state.update_data(
        residence_reason="residence_reason_patent",
        who="patient",
        patient_data=sd.get("patient_data", {}) or {},
    )

    title = _.get_text("residence_reason_manual_patient_messages.patient_number.title", lang)
    example = _.get_text("residence_reason_manual_patient_messages.patient_number.example_text", lang)

    await state.set_state(ResidenceReasonPatentStates.patient_number)
    await callback.message.edit_text(f"{title}\n{example}")


# ───────────────────────── номер патента → дата ─────────────────────────
@residence_reason_patient_router.message(ResidenceReasonPatentStates.patient_number)
async def get_patient_number(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    patient_data = dict(sd.get("patient_data") or {})
    patient_data["patient_number"] = (message.text or "").strip()
    await state.update_data(patient_data=patient_data)

    title = _.get_text("residence_reason_manual_patient_messages.patient_date.title", lang)
    example = _.get_text("residence_reason_manual_patient_messages.patient_date.example_text", lang)

    await state.set_state(ResidenceReasonPatentStates.patient_date)
    await message.answer(f"{title}\n{example}")


# ───────────────────────── дата → КЕМ выдан ─────────────────────────
@residence_reason_patient_router.message(ResidenceReasonPatentStates.patient_date)
async def get_patient_date(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    patient_data = dict(sd.get("patient_data") or {})
    patient_data["patient_date"] = (message.text or "").strip()
    await state.update_data(patient_data=patient_data)

    title = _.get_text("residence_reason_manual_patient_messages.patient_issue_place.title", lang)
    example = _.get_text("residence_reason_manual_patient_messages.patient_issue_place.example_text", lang)

    await state.set_state(ResidenceReasonPatentStates.issue_place)
    await message.answer(f"{title}\n{example}")


# ───────────────────────── КЕМ выдан → адрес проживания ─────────────────────────
@residence_reason_patient_router.message(ResidenceReasonPatentStates.issue_place)
async def get_patient_issue_place(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    patient_data = dict(sd.get("patient_data") or {})
    patient_data["patient_issue_place"] = (message.text or "").strip()

    # сохраняем и фиксируем «кто» — для генерации шаблона
    await state.update_data(patient_data=patient_data, who="patient")

    # просим адрес проживания (общий компонент «адрес» + пример с картинкой)
    await state.update_data(waiting_data="live_adress")
    photo = FSInputFile("static/live_adress_example.png")
    caption = f"{_.get_text('live_adress.title', lang)}\n{_.get_text('live_adress.example', lang)}"
    await message.answer_photo(photo=photo, caption=caption)

    await state.set_state(LiveAdress.adress)


# ───────────────────────── Back-compat: ожидается функция ─────────────────────────
# В некоторых старых модулях (например, handlers/doc_child_stay_extension.py)
# делают импорт: from handlers.components.residence_reason_patent import func_residence_reason_patent
# Делаем алиас на стартовый хэндлер, чтобы импорт прошёл и логика сохранилась.
async def func_residence_reason_patent(callback: CallbackQuery, state: FSMContext):
    """Back-compat wrapper: перенаправляет на актуальный старт 'По патенту'."""
    await start_patient_flow(callback, state)
