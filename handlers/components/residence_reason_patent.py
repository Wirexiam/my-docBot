from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from localization import _
from states.components.residence_reason_patent import ResidenceReasonPatentStates
from states.work_activity import PatentedWorkActivity  # следующий узел WA после патента

residence_reason_patient_router = Router()


# ───────────────────── кнопки выбора способа (из клавиатуры WA) ─────────────────────
@residence_reason_patient_router.callback_query(
    F.data == "start_residence_reason_byphoto"
)
async def handle_res_patent_byphoto(callback: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    note = (
        f"{_.get_text('start_residence_reason.photo_soon.title', lang)}\n\n"
        f"{_.get_text('start_residence_reason.photo_soon.description', lang)}"
        if hasattr(_, "has_key")
        and _.has_key("start_residence_reason.photo_soon.title")
        else "📸 Распознавание патента по фото будет доступно позже. Перейдём к вводу данных вручную."
    )
    await callback.message.edit_text(note)
    await start_patient_flow(callback, state)


@residence_reason_patient_router.callback_query(
    F.data == "start_residence_reason_patent_manual"
)
async def handle_res_patent_manual(callback: CallbackQuery, state: FSMContext):
    await start_patient_flow(callback, state)


# ───────────────────── старт «По патенту» (ручной ввод) ─────────────────────
@residence_reason_patient_router.callback_query(F.data == "residence_reason_patent")
async def start_patient_flow(callback: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    await state.update_data(
        residence_reason="residence_reason_patent",
        who="patient",
        patient_data=sd.get("patient_data", {}) or {},
    )

    title = _.get_text(
        "residence_reason_manual_patient_messages.patient_number.title", lang
    )
    example = _.get_text(
        "residence_reason_manual_patient_messages.patient_number.example_text", lang
    )

    await state.set_state(ResidenceReasonPatentStates.patient_number)
    await callback.message.edit_text(f"{title}\n{example}")


# ───────────────────── номер патента → дата ─────────────────────
@residence_reason_patient_router.message(ResidenceReasonPatentStates.patient_number)
async def get_patient_number(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    patient_data = dict(sd.get("patient_data") or {})
    patient_data["patient_number"] = (message.text or "").strip()
    await state.update_data(patient_data=patient_data)

    title = _.get_text(
        "residence_reason_manual_patient_messages.patient_date.title", lang
    )
    example = _.get_text(
        "residence_reason_manual_patient_messages.patient_date.example_text", lang
    )

    await state.set_state(ResidenceReasonPatentStates.patient_date)
    await message.answer(f"{title}\n{example}")


# ───────────────────── дата → КЕМ выдан ─────────────────────
@residence_reason_patient_router.message(ResidenceReasonPatentStates.patient_date)
async def get_patient_date(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")

    patient_data = dict(sd.get("patient_data") or {})
    patient_data["patient_date"] = (message.text or "").strip()
    await state.update_data(patient_data=patient_data)

    title = _.get_text(
        "residence_reason_manual_patient_messages.patient_issue_place.title", lang
    )
    example = _.get_text(
        "residence_reason_manual_patient_messages.patient_issue_place.example_text",
        lang,
    )

    await state.set_state(ResidenceReasonPatentStates.issue_place)
    await message.answer(f"{title}\n{example}")


# ───────────────────── КЕМ выдан → ПРЯМО в WA (без адреса проживания) ─────────────────────
@residence_reason_patient_router.message(ResidenceReasonPatentStates.issue_place)
async def get_patient_issue_place(message: Message, state: FSMContext):
    """
    Финальный шаг патента. Адрес проживания в WA-флоу НЕ требуется.
    Сразу передаём управление в WA: PatentedWorkActivity.medical_policy_start (профессия).
    """
    sd = await state.get_data()
    lang = sd.get("language")

    patient_data = dict(sd.get("patient_data") or {})
    patient_data["patient_issue_place"] = (message.text or "").strip()

    await state.update_data(
        patient_data=patient_data,
        who="patient",
        residence_reason="residence_reason_patent",
        from_action=PatentedWorkActivity.medical_policy_start,  # страховка от перескоков
    )

    text = (
        f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.title', lang)}\n\n"
        f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.description', lang)}\n\n"
        f"{_.get_text('wa_patent.wa_patent_medical_policy.name_work.example', lang)}"
    )
    await state.set_state(PatentedWorkActivity.medical_policy_start)
    await message.answer(text=text)


# ───────────────────── Back-compat: алиас ─────────────────────
async def func_residence_reason_patent(callback: CallbackQuery, state: FSMContext):
    await start_patient_flow(callback, state)
