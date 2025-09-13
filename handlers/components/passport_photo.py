from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from data_manager import SecureDataManager
from ocr.service import PassbotOcrService, OcrError
from localization import _
from states.components.passport_photo import PassportPhotoStates
from states.stamp_transfer import Stamp_transfer
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates

passport_photo_router = Router()
data_manager = SecureDataManager()
ocr_service = PassbotOcrService()


# ─────────────────────────── вспомогательные клавиатуры ───────────────────────────

def _kb_old_preview() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё верно", callback_data="old_ok")],
        [InlineKeyboardButton(text="✏️ Изменить одно из полей", callback_data="old_edit")],
        [InlineKeyboardButton(text="🖼 Загрузить другое фото", callback_data="old_retry")],
        [InlineKeyboardButton(text="➡️ Перейти к новому паспорту (по фото)", callback_data="goto_new_by_photo")],
        [InlineKeyboardButton(text="⌨️ Новый паспорт — ввести вручную", callback_data="goto_new_manual")],
    ])


def _kb_new_preview() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё верно", callback_data="new_ok")],
        [InlineKeyboardButton(text="✏️ Изменить одно из полей", callback_data="new_edit")],
        [InlineKeyboardButton(text="🖼 Загрузить другое фото", callback_data="new_retry")],
    ])


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

        # Куда кладём результат
        key = "old_passport_data" if is_old else "passport_data"
        await state.update_data(**{key: result.passport_data})
        data_manager.save_user_data(message.from_user.id, session_id, {key: result.passport_data})

        # предпросмотр
        p = result.passport_data
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
        kb = _kb_old_preview() if is_old else _kb_new_preview()
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

@passport_photo_router.callback_query(F.data == "old_edit")
async def old_edit(cb: CallbackQuery, state: FSMContext):
    # здесь можно открыть твой уже существующий ручной редактор полей
    await cb.message.edit_text("✏️ Какое поле нужно исправить? Выберите в меню редактирования.")

@passport_photo_router.callback_query(F.data == "old_ok")
async def old_ok(cb: CallbackQuery, state: FSMContext):
    """
    Подтверждён старый паспорт → переносим passport_data -> old_passport_data (если нужно)
    и предлагаем загрузить НОВЫЙ паспорт (по фото/вручную), без запроса 'кем выдан'.
    """
    data = await state.get_data()
    session_id = data.get("session_id")
    lang = data.get("language")

    # если почему-то старые данные лежат в 'passport_data' — переносим в old_
    pd = data.get("passport_data") or data.get("old_passport_data") or {}
    await state.update_data(old_passport_data=pd, passport_data={})
    data_manager.save_user_data(cb.from_user.id, session_id, {"old_passport_data": pd})

    # готовим шаг нового паспорта
    await state.update_data(from_action=Stamp_transfer.after_new_passport,
                            passport_title="stamp_transfer_passport_new_title",
                            next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input])

    await cb.message.edit_text(
        _.get_text("stamp_transfer_start_new_passport.title", lang) + "\n\n" +
        _.get_text("stamp_transfer_start_new_passport.description", lang)
    )
    # показываем клавиатуру выбора способа ввода нового паспорта — её даёт твой stamp_transfer.py
    # отсюда просто шлём колбэк, чтобы отрисовать нужную клавиатуру там, где она используется
    await start_new(cb, state)



@passport_photo_router.callback_query(F.data == "goto_new_by_photo")
async def goto_new_by_photo(cb: CallbackQuery, state: FSMContext):
    await start_new(cb, state)

@passport_photo_router.callback_query(F.data == "goto_new_manual")
async def goto_new_manual(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("⌨️ Введите данные нового паспорта вручную (следуйте подсказкам).")


# ─────────────────────────── кнопки предпросмотра: НОВЫЙ ───────────────────────────

@passport_photo_router.callback_query(F.data == "new_retry")
async def new_retry(cb: CallbackQuery, state: FSMContext):
    await state.set_state(PassportPhotoStates.waiting_new_passport_photo)
    await cb.message.edit_text("🖼 Пришлите другое фото НОВОГО паспорта.")

@passport_photo_router.callback_query(F.data == "new_edit")
async def new_edit(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("✏️ Какое поле нужно исправить? Выберите в меню редактирования.")

@passport_photo_router.callback_query(F.data == "new_ok")
async def new_ok(cb: CallbackQuery, state: FSMContext):
    """
    Подтверждён новый паспорт → переводим пользователя к следующему шагу
    (обычно: ввод адреса, затем ввод телефона).
    """
    data = await state.get_data()
    lang = data.get("language")
    # куда возвращаться по сценарию stamp_transfer
    from_action = data.get("from_action") or Stamp_transfer.after_new_passport
    # список шагов после паспортов (мы его сохраняли ранее при переходе со старого паспорта)
    next_states = data.get("next_states") or [LiveAdress.adress, PhoneNumberStates.phone_number_input]

    # 1) ставим "корневое" состояние сценария после паспортов
    await state.set_state(from_action)
    await cb.message.edit_text("✅ Паспортные данные сохранены. Продолжаем оформление.")

    # Обрежем очередь: удалим первый шаг, чтобы в хэндлере адреса не остался self
    first_next = next_states[0] if next_states else None
    rest = next_states[1:] if next_states else []
    await state.update_data(next_states=rest)

    if first_next:
        await state.update_data(waiting_data="live_adress")
        await state.set_state(first_next)

        prompt = _.get_text("live_adress.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📝 Укажите адрес проживания в РФ в одной строке: город, улица, дом, корпус/строение (если есть), квартира."
        await cb.message.answer(prompt)
