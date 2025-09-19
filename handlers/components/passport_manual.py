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


def _storage_key(state_data: dict) -> str:
    """Куда сохранять: в old_passport_data (для старого) или passport_data (для нового/обычного)."""
    mode = state_data.get("passport_input_mode")
    return "old_passport_data" if mode == "old" else "passport_data"


# ───────────────────────────── старт ручного ввода ─────────────────────────────

@passport_manual_router.callback_query(
    F.data.in_({"passport_manual_start", "passport_old_manual_start", "passport_new_manual_start"})
)
async def handle_passport_manual_start(callback: CallbackQuery, state: FSMContext):
    """
    Старт ручного ввода. Показываем заголовок + первый промпт (ФИО).
    Запоминаем режим ввода: old/new (влияет на ключ сохранения данных).
    """
    # Определяем режим (старый/новый)
    if callback.data.startswith("passport_old_"):
        mode = "old"
    elif callback.data.startswith("passport_new_"):
        mode = "new"
    else:
        mode = "new"  # по умолчанию считаем как новый (обычный кейс)

    state_data = await state.get_data()
    lang = state_data.get("language")

    if mode == "old":
        passport_title_key = "stamp_transfer_passport_old_title"
        # просто фиксируем режим старого паспорта
        await state.update_data(
            passport_input_mode="old"
        )
    elif mode == "new":
        passport_title_key = "stamp_transfer_passport_new_title"
        # После нового паспорта при перестановке штампа → адрес → телефон
        # Плюс гарантированно чистим контейнер под новый паспорт
        await state.update_data(
            from_action=Stamp_transfer.after_new_passport,
            next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
            passport_input_mode="new",
            passport_data={}
        )
    else:
        passport_title_key = "wa_passport_title"
        await state.update_data(passport_input_mode="new")

    description_key = "passport_manual_full_name.description"
    text = f"{_.get_text(passport_title_key, lang)}\n\n{_.get_text(description_key, lang)}"

    await state.set_state(PassportManualStates.full_name_input)
    await callback.message.edit_text(text=text, reply_markup=None)


# ───────────────────────────── ФИО → дата рождения ─────────────────────────────

@passport_manual_router.message(PassportManualStates.full_name_input)
async def handle_full_name_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["full_name"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    # Просим дату рождения
    if sd.get("age", False):
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
    sd = await state.get_data()
    lang = sd.get("language")
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["birth_date"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    # Просим гражданство
    if sd.get("age", False):
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
    sd = await state.get_data()
    lang = sd.get("language")
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["citizenship"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    title = _.get_text('passport_manual_serial_input.title', lang)
    example = _.get_text('passport_manual_serial_input.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_serial_number_input)


# ───────────────────── серия/номер → дата выдачи ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_serial_number_input)
async def handle_passport_serial_number_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_serial_number"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    title = _.get_text('passport_manual_issue_date.title', lang)
    example = _.get_text('passport_manual_issue_date.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_issue_date_input)


# ───────────────────── дата выдачи → срок действия (или скип) ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_issue_date_input)
async def handle_passport_issue_date_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_issue_date"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    if sd.get("skip_passport_expiry_date"):
        await state.update_data(skip_passport_expiry_date=False)
        title = _.get_text('passport_manual_issue_place.title', lang)
        example = _.get_text('passport_manual_issue_place.example_text', lang)
        await message.answer(f"{title}\n{example}")
        await state.set_state(PassportManualStates.passport_issue_place_input)
        return

    title = _.get_text('passport_manual_expire_date.title', lang)
    example = _.get_text('passport_manual_expire_date.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_expiry_date_input)


# ───────────────────── срок действия → кем выдан ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_expiry_date_input)
async def handle_passport_expiry_date_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_expiry_date"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    title = _.get_text('passport_manual_issue_place.title', lang)
    example = _.get_text('passport_manual_issue_place.example_text', lang)
    await message.answer(f"{title}\n{example}")
    await state.set_state(PassportManualStates.passport_issue_place_input)


# ───────────────────── кем выдан → дальше по очереди ─────────────────────

@passport_manual_router.message(PassportManualStates.passport_issue_place_input)
async def handle_passport_issue_place_input(message: Message, state: FSMContext):
    sd = await state.get_data()
    lang = sd.get("language")
    session_id = sd.get("session_id")
    key = _storage_key(sd)

    data = dict(sd.get(key) or {})
    data["passport_issue_place"] = (message.text or "").strip()

    await state.update_data(**{key: data})
    data_manager.save_user_data(message.from_user.id, session_id, {key: data})

    # Если очередь следующих шагов не задана — по умолчанию адрес → телефон
    next_states = list(sd.get("next_states") or [LiveAdress.adress, PhoneNumberStates.phone_number_input])

    # Ставим ожидание адреса, переключаемся на первый шаг очереди
    await state.update_data(next_states=next_states[1:], waiting_data="live_adress")
    await state.set_state(next_states[0])

    # Подсказка по адресу
    title = _.get_text("live_adress.title", lang)
    if title.startswith("[Missing:"):
        title = "📝 Укажите адрес проживания в РФ в одной строке."
    example = _.get_text("live_adress.example", lang)
    if example.startswith("[Missing:"):
        example = "Формат: город, улица, дом, корпус/строение (если есть), квартира."
    await message.answer(f"{title}\n{example}")
