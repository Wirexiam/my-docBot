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
    """Запросить фото СТАРОГО паспорта"""
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(PassportPhotoStates.waiting_old_passport_photo)
    title = _.get_text("ocr.passport.send_photo.title", lang)
    hint = _.get_text("ocr.passport.send_photo.hint", lang)
    await callback.message.edit_text(f"{title}\n\n{hint}")


@passport_photo_router.callback_query(F.data == "passport_new_photo_start")
async def start_new(callback: CallbackQuery, state: FSMContext):
    """Запросить фото НОВОГО паспорта"""
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(PassportPhotoStates.waiting_new_passport_photo)
    title = _.get_text("ocr.passport.send_photo.title", lang)
    hint = _.get_text("ocr.passport.send_photo.hint", lang)
    await callback.message.edit_text(f"{title}\n\n{hint}")


# ───────────────────── приём фото (поддержка обоих состояний) ─────────────────────

@passport_photo_router.message(PassportPhotoStates.waiting_old_passport_photo, F.photo)
@passport_photo_router.message(PassportPhotoStates.waiting_new_passport_photo, F.photo)
async def on_passport_photo(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")
    is_old = (await state.get_state()) == PassportPhotoStates.waiting_old_passport_photo.state

    # сохраняем файл
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

        # ── НОРМАЛИЗАЦИЯ ПОЛЕЙ ОТ OCR ─────────────────────────────────────
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
            "full_name",
            "birth_date",
            "citizenship",
            "passport_serial_number",
            "passport_issue_date",
            "passport_expiry_date",
            "passport_issue_place",
        ]
        for f in required_fields:
            p.setdefault(f, "")

        p = {k: v for k, v in p.items() if isinstance(v, str) and v.strip()} | {f: p.get(f, "") for f in required_fields}

        key = "old_passport_data" if is_old else "passport_data"
        await state.update_data(**{key: p})
        data_manager.save_user_data(message.from_user.id, session_id, {key: p})

        preview_tpl = _.get_text("ocr.passport.success.preview", lang)
        preview = preview_tpl.format(
            full_name=p.get("full_name", "—"),
            birth_date=p.get("birth_date", "—"),
            citizenship=p.get("citizenship", "—"),
            doc_id=p.get("passport_serial_number", p.get("doc_id", "—")),
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


# ─────────────────────────── кнопки предпросмотра: СТАРЫЙ ───────────────────────────

@passport_photo_router.callback_query(F.data == "old_retry")
async def old_retry(cb: CallbackQuery, state: FSMContext):
    await state.set_state(PassportPhotoStates.waiting_old_passport_photo)
    await cb.message.edit_text("🖼 Пришлите другое фото СТАРОГО паспорта.")


@passport_photo_router.callback_query(F.data == "old_ok")
async def old_ok(cb: CallbackQuery, state: FSMContext):
    """
    Подтверждён старый паспорт → переносим passport_data -> old_passport_data (если нужно)
    и предлагаем загрузить НОВЫЙ паспорт (по фото/вручную), без запроса 'кем выдан'.
    """
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
    # По фото — сразу предлагаем загрузить
    await start_new(cb, state)


@passport_photo_router.callback_query(F.data == "goto_new_by_photo")
async def goto_new_by_photo(cb: CallbackQuery, state: FSMContext):
    await start_new(cb, state)


@passport_photo_router.callback_query(F.data == "goto_new_manual")
async def goto_new_manual(cb: CallbackQuery, state: FSMContext):
    """
    Мост в РУЧНОЙ ввод нового паспорта:
    - выставляем нужные ключи в state
    - программно вызываем старт ручного ввода с колбэком 'passport_new_manual_start'
    """
    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        passport_title="stamp_transfer_passport_new_title",
        next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
    )
    # локальный импорт, чтобы не ловить циклические зависимости
    from handlers.components.passport_manual import handle_passport_manual_start
    fake_cb = cb.model_copy(update={"data": "passport_new_manual_start"})
    await handle_passport_manual_start(fake_cb, state)


# ─────────────────────────── кнопки предпросмотра: НОВЫЙ ───────────────────────────

@passport_photo_router.callback_query(F.data == "new_retry")
async def new_retry(cb: CallbackQuery, state: FSMContext):
    await state.set_state(PassportPhotoStates.waiting_new_passport_photo)
    await cb.message.edit_text("🖼 Пришлите другое фото НОВОГО паспорта.")


@passport_photo_router.callback_query(F.data == "new_ok")
async def new_ok(cb: CallbackQuery, state: FSMContext):
    """
    Подтверждён НОВЫЙ паспорт → показываем мини-сводку паспортных данных.
    - Штамп ВНЖ (DRN): кнопка "перейти к ВНЖ".
    - Работа по патенту (WA): кнопка "перейти к патенту".
    - По умолчанию: "адрес/телефон".
    """
    data = await state.get_data()
    lang = data.get("language")

    from_action = data.get("from_action") or Stamp_transfer.after_new_passport
    ocr_flow = data.get("ocr_flow")  # "drn", "wa" или None
    await state.set_state(from_action)

    sd = await state.get_data()
    new_pd = sd.get("passport_data") or {}
    old_pd = sd.get("old_passport_data") or {}

    def _val(d, k, default="—"):
        v = (d.get(k) or "").strip()
        return v if v else default

    # --- текст мини-сводки ---
    text = (
        "Проверьте паспортные данные\n\n"
        f"👤 ФИО: {_val(new_pd, 'full_name')}\n"
        f"🗓 Дата рождения: {_val(new_pd, 'birth_date')}\n"
        f"🌍 Гражданство: {_val(new_pd, 'citizenship')}\n"
        f"📄 Номер: {_val(new_pd, 'passport_serial_number')}\n"
        f"🏢 Кем выдан / дата: {_val(new_pd, 'passport_issue_place')} / {_val(new_pd, 'passport_issue_date')}\n"
        f"⏳ Срок действия: {_val(new_pd, 'passport_expiry_date')}\n\n"
    )

    if old_pd:
        text += (
            f"📄 Старый паспорт: {_val(old_pd, 'passport_serial_number')} "
            f"({_val(old_pd, 'passport_issue_place')} / {_val(old_pd, 'passport_issue_date')})"
        )

    # --- клавиатура по сценарию ---
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



@passport_photo_router.callback_query(F.data.in_({"old_edit", "new_edit"}))
async def start_edit_bridge(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if cb.data == "old_edit":
        await state.update_data(
            change_data_from_check="old_preview",
            from_action=Stamp_transfer.after_old_passport,
            return_after_edit="old_preview",
        )
    else:
        await state.update_data(
            change_data_from_check="stamp_transfer_after_new_passport",
            from_action=Stamp_transfer.after_new_passport,
            return_after_edit="stamp_transfer_after_new_passport",
        )

    # локальный импорт, чтобы избежать циклических зависимостей
    from handlers.components.changing_data import handle_change_data

    fake_cb = cb.model_copy(update={"data": "change_data_dummy"})
    await handle_change_data(fake_cb, state)
