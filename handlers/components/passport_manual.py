from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from localization import _
from data_manager import SecureDataManager

from states.components.passport_manual import PassportManualStates
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from states.stamp_transfer import Stamp_transfer
from states.registration_renewal import RegistrationRenewalStates
from states.work_activity import PatentedWorkActivity  # WA-мост

passport_manual_router = Router()
data_manager = SecureDataManager()


def _storage_key(state_data: dict) -> str:
    mode = state_data.get("passport_input_mode")
    return "old_passport_data" if mode == "old" else "passport_data"


# ───────────────────────── старт ручного ввода ─────────────────────────
@passport_manual_router.callback_query(
    F.data.in_({"passport_manual_start", "passport_old_manual_start", "passport_new_manual_start"})
)
async def handle_passport_manual_start(callback: CallbackQuery, state: FSMContext):
    # определяем режим
    if callback.data.startswith("passport_old_"):
        mode = "old"
    elif callback.data.startswith("passport_new_"):
        mode = "new"
    else:
        mode = "new"

    sd = await state.get_data()
    lang = sd.get("language")

    if mode == "old":
        passport_title_key = "stamp_transfer_passport_old_title"
        await state.update_data(
            passport_input_mode="old",
            old_passport_data={},
            next_states=[Stamp_transfer.after_old_passport],
            from_action=Stamp_transfer.after_old_passport,
        )
    else:
        # Авто-распознавание WA-контекста
        is_wa = sd.get("ocr_flow") == "wa" or sd.get("from_action") == PatentedWorkActivity.passport_data
        if is_wa:
            passport_title_key = "wa_passport_title"
            await state.update_data(
                passport_input_mode="new",
                passport_data={},
                from_action=PatentedWorkActivity.passport_data,
                next_states=sd.get("next_states") or [PatentedWorkActivity.patent_entry],
                ocr_flow="wa",
            )
        else:
            passport_title_key = "stamp_transfer_passport_new_title"
            await state.update_data(
                passport_input_mode="new",
                passport_data={},
                from_action=sd.get("from_action") or Stamp_transfer.after_new_passport,
                next_states=sd.get("next_states"),
            )

    text = f"{_.get_text(passport_title_key, lang)}\n\n{_.get_text('passport_manual_full_name.description', lang)}"
    await state.set_state(PassportManualStates.full_name_input)
    await callback.message.edit_text(text=text)


# ───────────────────────── ФИО → дата рождения ─────────────────────────
@passport_manual_router.message(PassportManualStates.full_name_input)
async def handle_full_name_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["full_name"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    lang = sd.get("language")
    if sd.get("age", False):
        title = _.get_text("passport_manual_kid_birth_date.title", lang)
        example = _.get_text("passport_manual_kid_birth_date.example_text", lang)
    else:
        title = _.get_text("passport_manual_birth_date.title", lang)
        example = _.get_text("passport_manual_birth_date.example_text", lang)

    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.birth_date_input)


# ───────────────────────── дата рождения → гражданство ─────────────────────────
@passport_manual_router.message(PassportManualStates.birth_date_input)
async def handle_birth_date_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["birth_date"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    lang = sd.get("language")
    if sd.get("age", False):
        title = _.get_text("migr_manual_citizenship_kid.title", lang)
        example = _.get_text("migr_manual_citizenship_kid.example_text", lang)
    else:
        title = _.get_text("passport_manual_citizenship.title", lang)
        example = _.get_text("passport_manual_citizenship.example_text", lang)

    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.citizenship_input)


# ───────────────────────── гражданство → серия/номер ─────────────────────────
@passport_manual_router.message(PassportManualStates.citizenship_input)
async def handle_citizenship_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["citizenship"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    lang = sd.get("language")
    await message.answer(f"{_.get_text('passport_manual_serial_input.title', lang)}\n{_.get_text('passport_manual_serial_input.example_text', lang)}")
    await state.set_state(PassportManualStates.passport_serial_number_input)


# ───────────────────────── серия/номер → дата выдачи ─────────────────────────
@passport_manual_router.message(PassportManualStates.passport_serial_number_input)
async def handle_passport_serial_number_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_serial_number"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    lang = sd.get("language")
    await message.answer(f"{_.get_text('passport_manual_issue_date.title', lang)}\n{_.get_text('passport_manual_issue_date.example_text', lang)}")
    await state.set_state(PassportManualStates.passport_issue_date_input)


# ───────────────────────── дата выдачи → срок действия ─────────────────────────
@passport_manual_router.message(PassportManualStates.passport_issue_date_input)
async def handle_passport_issue_date_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_issue_date"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    lang = sd.get("language")
    if sd.get("skip_passport_expiry_date"):
        await state.update_data(skip_passport_expiry_date=False)
        await message.answer(f"{_.get_text('passport_manual_issue_place.title', lang)}\n{_.get_text('passport_manual_issue_place.example_text', lang)}")
        await state.set_state(PassportManualStates.passport_issue_place_input)
        return

    await message.answer(f"{_.get_text('passport_manual_expire_date.title', lang)}\n{_.get_text('passport_manual_expire_date.example_text', lang)}")
    await state.set_state(PassportManualStates.passport_expiry_date_input)


# ───────────────────────── срок действия → кем выдан ─────────────────────────
@passport_manual_router.message(PassportManualStates.passport_expiry_date_input)
async def handle_passport_expiry_date_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_expiry_date"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    lang = sd.get("language")
    await message.answer(f"{_.get_text('passport_manual_issue_place.title', lang)}\n{_.get_text('passport_manual_issue_place.example_text', lang)}")
    await state.set_state(PassportManualStates.passport_issue_place_input)


# ───────────────────────── кем выдан → следующий шаг ─────────────────────────
@passport_manual_router.message(PassportManualStates.passport_issue_place_input)
async def handle_passport_issue_place_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_issue_place"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    from_action = sd.get("from_action")

    # A. Продление регистрации
    if from_action == RegistrationRenewalStates.after_passport:
        lang = sd.get("language")

        def _v(d, k, default="—"):
            v = (d.get(k) or "").strip()
            return v or default

        pd = data
        text = (
            "Проверьте паспортные данные\n\n"
            f"👤 ФИО: {_v(pd,'full_name')}\n"
            f"🗓 Дата рождения: {_v(pd,'birth_date')}\n"
            f"🌍 Гражданство: {_v(pd,'citizenship')}\n"
            f"📄 Номер: {_v(pd,'passport_serial_number')}\n"
            f"🏢 Кем выдан / дата: {_v(pd,'passport_issue_place')} / {_v(pd,'passport_issue_date')}\n"
            f"⏳ Срок действия: {_v(pd,'passport_expiry_date')}\n"
        )
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Всё верно — перейти к выбору основания", callback_data="sp_after_passport")],
                [InlineKeyboardButton(text=_.get_text("buttons.new_edit", lang), callback_data="new_edit")],
            ]
        )
        await message.answer(text, reply_markup=kb)
        return

    # B. Штамп ВНЖ — мост старого паспорта
    if from_action == Stamp_transfer.after_old_passport:
        from handlers.stamp_transfer import handle_old_passport_data
        await state.set_state(Stamp_transfer.after_old_passport)
        await handle_old_passport_data(message, state)
        return

    # C. Work Activity (патент) — мост WA: последний ввод «кем выдан» принимает WA-хэндлер
    if from_action == PatentedWorkActivity.passport_data:
        from handlers.work_activity import handle_passport_data
        await state.set_state(PatentedWorkActivity.passport_data)
        await handle_passport_data(message, state)
        return

    # D. Дефолт — на случай старых веток
    next_states = list(sd.get("next_states") or [LiveAdress.adress, PhoneNumberStates.phone_number_input])
    if next_states:
        await state.update_data(next_states=next_states[1:])
        await state.set_state(next_states[0])
