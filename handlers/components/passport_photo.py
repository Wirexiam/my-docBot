from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from keyboards.passport_preview import old_preview_kb, new_preview_kb
from data_manager import SecureDataManager
from ocr.service import PassbotOcrService, OcrError
from localization import _
from states.components.passport_photo import PassportPhotoStates
from states.stamp_transfer import Stamp_transfer
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from states.doc_residence_notification import DocResidenceNotificationStates
from states.work_activity import PatentedWorkActivity

passport_photo_router = Router()
data_manager = SecureDataManager()
ocr_service = PassbotOcrService()


# ───────────────────────────── стартовые кнопки ─────────────────────────────

@passport_photo_router.callback_query(F.data == "passport_old_photo_start")
async def start_old(callback: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("language")
    await state.set_state(PassportPhotoStates.waiting_old_passport_photo)
    title = _.get_text("ocr.passport.send_photo.title", lang)
    hint = _.get_text("ocr.passport.send_photo.hint", lang)
    await callback.message.edit_text(f"{title}\n\n{hint}")


@passport_photo_router.callback_query(F.data == "passport_new_photo_start")
async def start_new(callback: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("language")
    await state.set_state(PassportPhotoStates.waiting_new_passport_photo)
    title = _.get_text("ocr.passport.send_photo.title", lang)
    hint = _.get_text("ocr.passport.send_photo.hint", lang)
    await callback.message.edit_text(f"{title}\n\n{hint}")


# ───────────────────── приём фото (старый/новый) ─────────────────────

@passport_photo_router.message(PassportPhotoStates.waiting_old_passport_photo, F.photo)
@passport_photo_router.message(PassportPhotoStates.waiting_new_passport_photo, F.photo)
async def on_passport_photo(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")
    is_old = (await state.get_state()) == PassportPhotoStates.waiting_old_passport_photo.state

    f = await message.bot.get_file(message.photo[-1].file_id)
    file_bytes = await message.bot.download_file(f.file_path)
    img_path = data_manager.save_file(
        message.from_user.id,
        session_id,
        file_bytes.read(),
        filename=("old_passport.jpg" if is_old else "new_passport.jpg"),
    )

    note_msg = await message.answer(_.get_text("ocr.passport.progress", lang))

    try:
        result = await ocr_service.process_passport(img_path)

        # нормализация полей
        p = dict(result.passport_data)
        aliases = {
            "doc_id": "passport_serial_number",
            "issued_by": "passport_issue_place",
            "issue_date": "passport_issue_date",
            "expiry_date": "passport_expiry_date",
            "fullName": "full_name",
            "birthDate": "birth_date",
        }
        for src, dst in aliases.items():
            if src in p and dst not in p:
                p[dst] = p.pop(src)

        required_fields = [
            "full_name", "birth_date", "citizenship",
            "passport_serial_number", "passport_issue_date",
            "passport_expiry_date", "passport_issue_place"
        ]
        for f in required_fields:
            p.setdefault(f, "")

        # ⚠️ зеркалим ключ под WA-рендеринг (в WA используется 'passport_issued')
        p["passport_issued"] = p.get("passport_issue_place", "")

        key = "old_passport_data" if is_old else "passport_data"
        await state.update_data(**{key: p})
        data_manager.save_user_data(message.from_user.id, session_id, {key: p})

        preview_tpl = _.get_text("ocr.passport.success.preview", lang)
        preview = preview_tpl.format(
            full_name=p.get("full_name", "—"),
            birth_date=p.get("birth_date", "—"),
            citizenship=p.get("citizenship", "—"),
            doc_id=p.get("passport_serial_number", "—"),
            issued_by=p.get("passport_issue_place", "—"),
            issue_date=p.get("passport_issue_date", "—"),
            expiry_date=p.get("passport_expiry_date", "—"),
        )

        title = _.get_text("ocr.passport.success.title", lang)
        kb = old_preview_kb() if is_old else new_preview_kb()
        await note_msg.edit_text(f"{title}\n\n{preview}", reply_markup=kb)

    except OcrError as e:
        fail_title = _.get_text("ocr.passport.fail.title", lang)
        fail_hint = _.get_text("ocr.passport.fail.hint", lang)
        await note_msg.edit_text(f"{fail_title}\n\n{fail_hint}\n\n{e.user_message}")


# ─────────────────────────── кнопки предпросмотра ───────────────────────────

@passport_photo_router.callback_query(F.data == "old_ok")
async def old_ok(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    lang = data.get("language")

    pd = data.get("passport_data") or data.get("old_passport_data") or {}
    await state.update_data(old_passport_data=pd, passport_data={})
    data_manager.save_user_data(cb.from_user.id, session_id, {"old_passport_data": pd})

    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        passport_title="stamp_transfer_passport_new_title",
        next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
    )

    await cb.message.edit_text(
        _.get_text("stamp_transfer_start_new_passport.title", lang) + "\n\n" +
        _.get_text("stamp_transfer_start_new_passport.description", lang)
    )
    await start_new(cb, state)


@passport_photo_router.callback_query(F.data == "goto_new_manual")
async def goto_new_manual(cb: CallbackQuery, state: FSMContext):
    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        passport_title="stamp_transfer_passport_new_title",
        next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
    )
    from handlers.components.passport_manual import handle_passport_manual_start
    fake_cb = cb.model_copy(update={"data": "passport_new_manual_start"})
    await handle_passport_manual_start(fake_cb, state)


@passport_photo_router.callback_query(F.data == "new_ok")
async def new_ok(cb: CallbackQuery, state: FSMContext):
    """Подтверждение OCR нового паспорта → сводка по сценарию"""
    data = await state.get_data()
    lang = data.get("language")
    from_action = data.get("from_action") or Stamp_transfer.after_new_passport
    ocr_flow = data.get("ocr_flow")

    await state.set_state(from_action)

    new_pd = data.get("passport_data") or {}
    old_pd = data.get("old_passport_data") or {}

    def _val(d, k, default="—"):
        v = (d.get(k) or "").strip()
        return v if v else default

    text = (
        "Проверьте паспортные данные\n\n"
        f"👤 ФИО: {_val(new_pd, 'full_name')}\n"
        f"🗓 Дата рождения: {_val(new_pd, 'birth_date')}\n"
        f"🌍 Гражданство: {_val(new_pd, 'citizenship')}\n"
        f"📄 Номер: {_val(new_pd, 'passport_serial_number')}\n"
        f"🏢 Кем выдан / дата: {_val(new_pd, 'passport_issue_place')} / {_val(new_pd, 'passport_issue_date')}\n"
        f"⏳ Срок действия: {_val(new_pd, 'passport_expiry_date')}\n"
    )
    if old_pd:
        text += (
            f"\n📄 Старый паспорт: {_val(old_pd, 'passport_serial_number')} "
            f"({_val(old_pd, 'passport_issue_place')} / {_val(old_pd, 'passport_issue_date')})"
        )

    if ocr_flow == "drn" and from_action == DocResidenceNotificationStates.after_passport:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно — перейти к ВНЖ", callback_data="drn_after_passport")],
            [InlineKeyboardButton(text=_.get_text("buttons.new_edit", lang), callback_data="new_edit")],
            [InlineKeyboardButton(text=_.get_text("buttons.new_retry", lang), callback_data="new_retry")],
        ])
    elif ocr_flow == "wa" and from_action == PatentedWorkActivity.passport_data:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно — перейти к патенту", callback_data="wa_after_passport")],
            [InlineKeyboardButton(text=_.get_text("buttons.new_edit", lang), callback_data="new_edit")],
            [InlineKeyboardButton(text=_.get_text("buttons.new_retry", lang), callback_data="new_retry")],
        ])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_.get_text("buttons.goto_adress_phone", lang), callback_data="goto_adress_phone")],
            [InlineKeyboardButton(text=_.get_text("buttons.new_edit", lang), callback_data="new_edit")],
            [InlineKeyboardButton(text=_.get_text("buttons.new_retry", lang), callback_data="new_retry")],
        ])

    await cb.message.edit_text(text, reply_markup=kb)
