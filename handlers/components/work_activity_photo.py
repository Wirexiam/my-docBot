from typing import Dict

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from data_manager import SecureDataManager
from localization import _
from states.components.work_activity_photo import WorkActivityPhotoStates
from states.work_activity import PatentedWorkActivity
from ocr.service import PassbotOcrService, OcrError

work_activity_ocr_router = Router()
data_manager = SecureDataManager()
ocr_service = PassbotOcrService()


def _normalize_ocr(raw: Dict) -> Dict:
    """
    Приводим mixed-результат OCR (паспорт+патент) к:
      - passport_preview_kwargs: ключи ровно под твой шаблон ocr.passport.success.preview
      - patient_data: ключи текущей ветки (patient_*)
    """
    d = dict(raw or {})

    # --- паспорт под твой шаблон превью ---
    passport_preview_kwargs = {
        "full_name":   d.get("full_name") or d.get("fullName") or "",
        "birth_date":  d.get("birth_date") or d.get("birthDate") or "",
        "citizenship": d.get("citizenship") or "",
        # doc_id / issued_by / issue_date / expiry_date — как в твоём шаблоне
        "doc_id":      d.get("passport_serial_number") or d.get("doc_id") or "",
        "issued_by":   d.get("passport_issue_place")  or d.get("issued_by") or "",
        "issue_date":  d.get("passport_issue_date")   or d.get("issue_date") or "",
        "expiry_date": d.get("passport_expiry_date")  or d.get("expiry_date") or "",
    }
    for k, v in passport_preview_kwargs.items():
        if isinstance(v, str):
            passport_preview_kwargs[k] = v.strip()

    # --- патент в терминах текущей ветки (patient_*) ---
    patient_data = {
        "patient_number":      d.get("patient_number") or d.get("patent_number") or d.get("patentNo") or "",
        "patient_date":        d.get("patient_date")   or d.get("patent_issue_date") or d.get("patentIssueDate") or "",
        "patient_issue_place": d.get("patient_issue_place") or d.get("issued_by_patent") or d.get("patent_issue_place") or "",
    }
    for k, v in patient_data.items():
        if isinstance(v, str):
            patient_data[k] = v.strip()

    return passport_preview_kwargs, patient_data


def _preview_text(lang: str, passport_preview_kwargs: Dict, patient_data: Dict) -> str:
    """
    Собираем превью:
    - первая часть — РОВНО по твоему шаблону ocr.passport.success.preview
    - затем 3 строки по патенту (без новых ключей в ru.json)
    """
    passport_block = _.get_text("ocr.passport.success.preview", lang).format(**passport_preview_kwargs)
    pat = patient_data
    v = lambda k: (pat.get(k) or "—")
    patent_block = (
        f"\n\n🧾 Патент №: {v('patient_number')}\n"
        f"📅 Дата выдачи патента: {v('patient_date')}\n"
        f"🏢 Кем выдан патент: {v('patient_issue_place')}"
    )
    return f"{_.get_text('ocr.passport.success.title', lang)}\n\n{passport_block}{patent_block}"


def _preview_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё верно — продолжить", callback_data="wa_ocr_ok")],
        [InlineKeyboardButton(text="✏️ Изменить вручную", callback_data="wa_ocr_edit")],
        [InlineKeyboardButton(text="🔁 Загрузить другое фото", callback_data="wa_ocr_retry")],
    ])


# ───────────────────── Старт OCR ─────────────────────

@work_activity_ocr_router.callback_query(F.data == "wa_ocr_start")
async def wa_ocr_start(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    await state.set_state(WorkActivityPhotoStates.waiting_passport_or_patent_photo)
    title = _.get_text("ocr.passport.send_photo.title", lang)
    hint  = _.get_text("ocr.passport.send_photo.hint", lang)
    await cb.message.edit_text(f"{title}\n\n{hint}")


# Совместимость: если в клавиатуре уже есть 'passport_photo_start', перехватим и его
@work_activity_ocr_router.callback_query(F.data == "passport_photo_start")
async def wa_ocr_start_compat(cb: CallbackQuery, state: FSMContext):
    await wa_ocr_start(cb, state)


# ───────────────────── Приём фото ─────────────────────

@work_activity_ocr_router.message(WorkActivityPhotoStates.waiting_passport_or_patent_photo, F.photo)
async def wa_on_photo(msg: Message, state: FSMContext):
    sd   = await state.get_data()
    lang = sd.get("language")
    sess = sd.get("session_id")

    progress = await msg.answer(_.get_text("ocr.passport.progress", lang))

    # Скачать и сохранить фото в пользовательскую сессию
    f = await msg.bot.get_file(msg.photo[-1].file_id)
    fb = await msg.bot.download_file(f.file_path)
    img_path = data_manager.save_file(msg.from_user.id, sess, fb.read(), filename="work_activity.jpg")

    try:
        # Твой OCR: либо спец-метод для патента, либо общий, объединяющий паспорт+патент
        result = await ocr_service.process_work_activity(img_path)

        merged = {}
        if getattr(result, "passport_data", None):
            merged.update(result.passport_data)
        if getattr(result, "patent_data", None):
            merged.update(result.patent_data)

        passport_kwargs, patient_data = _normalize_ocr(merged)

        # Не перетираем ручной ввод — вливаем ТОЛЬКО пустые поля
        passport_data = sd.get("passport_data") or {}
        if not passport_data.get("full_name") and passport_kwargs.get("full_name"):
            passport_data["full_name"] = passport_kwargs["full_name"]
        if not passport_data.get("birth_date") and passport_kwargs.get("birth_date"):
            passport_data["birth_date"] = passport_kwargs["birth_date"]
        if not passport_data.get("citizenship") and passport_kwargs.get("citizenship"):
            passport_data["citizenship"] = passport_kwargs["citizenship"]
        if not passport_data.get("passport_serial_number") and passport_kwargs.get("doc_id"):
            passport_data["passport_serial_number"] = passport_kwargs["doc_id"]
        if not passport_data.get("passport_issue_place") and passport_kwargs.get("issued_by"):
            passport_data["passport_issue_place"] = passport_kwargs["issued_by"]
        if not passport_data.get("passport_issue_date") and passport_kwargs.get("issue_date"):
            passport_data["passport_issue_date"] = passport_kwargs["issue_date"]
        if not passport_data.get("passport_expiry_date") and passport_kwargs.get("expiry_date"):
            passport_data["passport_expiry_date"] = passport_kwargs["expiry_date"]

        current_patient = sd.get("patient_data") or {}
        for k, v in patient_data.items():
            if v and not current_patient.get(k):
                current_patient[k] = v

        await state.update_data(passport_data=passport_data, patient_data=current_patient)
        data_manager.save_user_data(
            msg.from_user.id, sess,
            {"passport_data": passport_data, "patient_data": current_patient}
        )

        await state.set_state(WorkActivityPhotoStates.preview)
        await progress.edit_text(
            _preview_text(lang, passport_kwargs, current_patient),
            reply_markup=_preview_kb()
        )

    except OcrError as e:
        fail_title = _.get_text("ocr.passport.fail.title", lang)
        fail_hint  = _.get_text("ocr.passport.fail.hint", lang)
        await progress.edit_text(f"{fail_title}\n\n{fail_hint}\n\n{e.user_message}")


# ───────────────────── Кнопки предпросмотра ─────────────────────

@work_activity_ocr_router.callback_query(F.data == "wa_ocr_retry")
async def wa_ocr_retry(cb: CallbackQuery, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    await state.set_state(WorkActivityPhotoStates.waiting_passport_or_patent_photo)
    await cb.message.edit_text(_.get_text("ocr.passport.send_photo.hint", lang))

@work_activity_ocr_router.callback_query(F.data == "wa_ocr_edit")
async def wa_ocr_edit(cb: CallbackQuery, state: FSMContext):
    """
    Мост в уже существующие ручные редакторы ветки (НЕ меняем ручной ввод).
    Можно перевести пользователя на первый актуальный шаг твоей ветки.
    """
    await state.set_state(PatentedWorkActivity.passport_serial_input)
    await cb.message.edit_text("✏️ Данные занесены. При необходимости отредактируйте вручную.")

@work_activity_ocr_router.callback_query(F.data == "wa_ocr_ok")
async def wa_ocr_ok(cb: CallbackQuery, state: FSMContext):
    """
    Подтверждение OCR → продолжаем штатный поток ветки
    (например, к блоку ДМС/страховки или следующему шагу после паспорта/патента).
    """
    await state.set_state(PatentedWorkActivity.medical_policy_start)
    await cb.message.edit_text("✅ Всё верно. Продолжим заполнение…")
