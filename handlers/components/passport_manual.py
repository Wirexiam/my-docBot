from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from localization import _
from data_manager import SecureDataManager

from states.components.passport_manual import PassportManualStates
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from states.stamp_transfer import Stamp_transfer

passport_manual_router = Router()
data_manager = SecureDataManager()


# ───────────────────────────── старт ручного ввода ─────────────────────────────

@passport_manual_router.callback_query(
    F.data.in_({"passport_manual_start", "passport_old_manual_start", "passport_new_manual_start"})
)
async def handle_passport_manual_start(callback: CallbackQuery, state: FSMContext):
    """
    Старт ручного ввода. Показываем заголовок + первый промпт (ФИО).
    """
    # Определяем «старый/новый» для заголовка и очереди следующих шагов
    prefix = (
        "old" if callback.data.startswith("passport_old_")
        else "new" if callback.data.startswith("passport_new_")
        else None
    )

    state_data = await state.get_data()
    lang = state_data.get("language")

    if prefix == "old":
        passport_title_key = "stamp_transfer_passport_old_title"
    elif prefix == "new":
        passport_title_key = "stamp_transfer_passport_new_title"
        # После нового паспорта переходим к адресу → телефону
        await state.update_data(
            from_action=Stamp_transfer.after_new_passport,
            next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
        )
    else:
        # универсальный кейс (если вызывается вне «перестановки штампа»)
        passport_title_key = "wa_passport_title"

    # Первый промпт — ФИО
    description_key = "passport_manual_full_name.description"
    text = f"{_.get_text(passport_title_key, lang)}\n\n{_.get_text(description_key, lang)}"

    await state.set_state(PassportManualStates.full_name_input)
    await callback.message.edit_text(text=text, reply_markup=None)


# ───────────────────────────── ФИО → дата рождения ─────────────────────────────

@passport_manual_router.message(PassportManualStates.full_name_input)
async def handle_full_name_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    full_name = (message.text or "").strip()
    passport_data = dict(state_data.get("passport_data") or {})
    passport_data["full_name"] = full_name

    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    # Просим дату рождения
    if state_data.get("age", False):
        title = _.get_text('passport_manual_kid_birth_date.title', lang)
        example = _.get_text('passport_manual_kid_birth_date.example_text', lang)
    else:
        title = _.get_text('passport_manual_birth_date.title', lang)
        example = _.get_text('passport_manual_birth_date.example_text', lang)

    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.birth_date_input)


# ───────────────────────── дата рождения → гражданство ─────────────────────────

@passport_manual_router.message(PassportManualStates.birth_date_input)
async def handle_birth_date_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    birth_date = (message.text or "").strip()
    passport_data = dict(state_data.get("passport_data") or {})
    passport_data["birth_date"] = birth_date

    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    # Просим гражданство
    if state_data.get("age", False):
        title = _.get_text('migr_manual_citizenship_kid.title', lang)
        example = _.get_text('migr_manual_citizenship_kid.example_text', lang)
    else:
        title = _.get_text('passport_manual_citizenship.title', lang)
        example = _.get_text('passport_manual_citizenship.example_text', lang)

    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.citizenship_input)


# ───────────────────────── гражданство → серия/номер ──────────────────────────

@passport_manual_router.message(PassportManualStates.citizenship_input)
async def handle_citizenship_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    citizenship = (message.text or "").strip()
    passport_data = dict(state_data.get("passport_data") or {})
    passport_data["citizenship"] = citizenship

    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    # Просим серию/номер
    title = _.get_text('passport_manual_serial_input.title', lang)
    example = _.get_text('passport_manual_serial_input.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_serial_number_input)


# ───────────────────── серия/номер → дата выдачи ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_serial_number_input)
async def handle_passport_serial_number_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    serial = (message.text or "").strip()
    passport_data = dict(state_data.get("passport_data") or {})
    passport_data["passport_serial_number"] = serial

    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    # Просим дату выдачи
    title = _.get_text('passport_manual_issue_date.title', lang)
    example = _.get_text('passport_manual_issue_date.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_issue_date_input)


# ───────────────────── дата выдачи → срок действия (или скип) ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_issue_date_input)
async def handle_passport_issue_date_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    issue_date = (message.text or "").strip()
    passport_data = dict(state_data.get("passport_data") or {})
    passport_data["passport_issue_date"] = issue_date

    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    # Если выставлен флаг «пропустить срок действия», идём сразу к "кем выдан"
    if state_data.get("skip_passport_expiry_date"):
        await state.update_data(skip_passport_expiry_date=False)
        title = _.get_text('passport_manual_issue_place.title', lang)
        example = _.get_text('passport_manual_issue_place.example_text', lang)
        await message.answer(f"{title}\n{example}")
        await state.set_state(PassportManualStates.passport_issue_place_input)
        return

    # Иначе спрашиваем срок действия
    title = _.get_text('passport_manual_expire_date.title', lang)
    example = _.get_text('passport_manual_expire_date.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_expiry_date_input)


# ───────────────────── срок действия → кем выдан ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_expiry_date_input)
async def handle_passport_expiry_date_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    expiry_date = (message.text or "").strip()
    passport_data = dict(state_data.get("passport_data") or {})
    passport_data["passport_expiry_date"] = expiry_date

    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    # Спрашиваем «кем выдан»
    title = _.get_text('passport_manual_issue_place.title', lang)
    example = _.get_text('passport_manual_issue_place.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_issue_place_input)


# ───────────────────── кем выдан → адрес → телефон ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_issue_place_input)
async def handle_passport_issue_place_input(message: Message, state: FSMContext):
    """
    Принимаем «кем выдан», сохраняем и переводим на ввод адреса (а дальше — телефон).
    """
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    issued_by = (message.text or "").strip()
    passport_data = dict(state_data.get("passport_data") or {})
    passport_data["passport_issue_place"] = issued_by

    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    # Готовим очередь следующих шагов: адрес → телефон (если не задана ранее)
    next_states = list(state_data.get("next_states") or [])
    if not next_states:
        next_states = [LiveAdress.adress, PhoneNumberStates.phone_number_input]

    # Обновляем очередь и ставим ожидание адреса
    await state.update_data(next_states=next_states[1:], waiting_data="live_adress")
    await state.set_state(LiveAdress.adress)

    # Подсказка по адресу
    title = _.get_text("live_adress.title", lang)
    if title.startswith("[Missing:"):
        title = "📝 Укажите адрес проживания в РФ в одной строке."
    example = _.get_text("live_adress.example", lang)
    if example.startswith("[Missing:"):
        example = "Формат: город, улица, дом, корпус/строение (если есть), квартира."
    await message.answer(f"{title}\n{example}")
