from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.components.passport_manual import PassportManualStates

from localization import _
from data_manager import SecureDataManager

passport_manual_router = Router()
data_manager = SecureDataManager()


@passport_manual_router.callback_query(
    F.data.in_({"passport_manual_start", "passport_old_manual_start", "passport_new_manual_start"})
)
async def handle_passport_manual_start(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual passport input."""
    # 0) Определяем префикс по типу колбэка (old/new), если передан
    prefix = "old" if callback.data.startswith("passport_old_") else (
        "new" if callback.data.startswith("passport_new_") else None
    )

    # 1) Ставим начальное состояние ручного ввода (как и раньше)
    await state.set_state(PassportManualStates.full_name_input)

    # 2) Достаём язык/тексты
    state_data = await state.get_data()
    lang = state_data.get("language")
    passport_title = state_data.get("passport_title", "")

    # Если префикс определён из колбэка — переопределим заголовок,
    # чтобы сразу показать "Старый" или "Новый" паспорт
    if prefix == "old":
        passport_title = "stamp_transfer_passport_old_title"
    elif prefix == "new":
        passport_title = "stamp_transfer_passport_new_title"

    passport_description = state_data.get("passport_description", "passport_manual_full_name.description")

    # 3) Отправляем вступительный текст
    text = f"{_.get_text(passport_title, lang)}\n\n{_.get_text(passport_description, lang)}"

    # 4) Как и прежде: мгновенно переводим FSM на следующий шаг,
    # а введённое пользователем следующее сообщение трактуем как ФИО
    await state.set_state(PassportManualStates.birth_date_input)
    await callback.message.edit_text(text=text, reply_markup=None)


@passport_manual_router.message(PassportManualStates.birth_date_input)
async def request_birth_date_input(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    passport_data = {}
    full_name = message.text.strip()
    passport_data["full_name"] = full_name

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(passport_data=passport_data)
    user_data = {"passport_data": passport_data}
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = (
        f"{_.get_text('passport_manual_birth_date.title', lang)}\n"
        f"{_.get_text('passport_manual_birth_date.example_text', lang)}"
    )
    if state_data.get("age", False):
        text = (
            f"{_.get_text('passport_manual_kid_birth_date.title', lang)}\n"
            f"{_.get_text('passport_manual_birth_date.example_text', lang)}"
        )

    await message.answer(text=text, reply_markup=None)
    await state.set_state(PassportManualStates.citizenship_input)


@passport_manual_router.message(PassportManualStates.citizenship_input)
async def handle_birth_date_input(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    passport_data_all = await state.get_data()
    passport_data = passport_data_all.get("passport_data")
    birth_date = message.text.strip()
    passport_data["birth_date"] = birth_date

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(passport_data=passport_data)
    user_data = {"passport_data": passport_data}
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = (
        f"{_.get_text('passport_manual_citizenship.title', lang)}\n"
        f"{_.get_text('passport_manual_citizenship.example_text', lang)}"
    )
    if state_data.get("age", False):
        text = (
            f"{_.get_text('migr_manual_citizenship_kid.title', lang)}\n"
            f"{_.get_text('migr_manual_citizenship_kid.example_text', lang)}"
        )

    await message.answer(text=text, reply_markup=None)
    await state.set_state(PassportManualStates.passport_serial_number_input)


@passport_manual_router.message(PassportManualStates.passport_serial_number_input)
async def handle_citizenship_input(message: Message, state: FSMContext):
    """Handle the input of the citizenship in manual passport handling."""
    passport_data_all = await state.get_data()
    passport_data = passport_data_all.get("passport_data")
    citizenship = message.text.strip()
    passport_data["citizenship"] = citizenship

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(passport_data=passport_data)
    user_data = {"passport_data": passport_data}
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = (
        f"{_.get_text('passport_manual_serial_input.title', lang)}\n"
        f"{_.get_text('passport_manual_serial_input.example_text', lang)}"
    )
    await message.answer(text=text, reply_markup=None)
    await state.set_state(PassportManualStates.passport_issue_date_input)


@passport_manual_router.message(PassportManualStates.passport_issue_date_input)
async def handle_passport_serial_number_input(message: Message, state: FSMContext):
    """Handle the input of the passport serial number in manual passport handling."""
    passport_data_all = await state.get_data()
    passport_data = passport_data_all.get("passport_data")
    passport_serial_number = message.text.strip()
    passport_data["passport_serial_number"] = passport_serial_number

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(passport_data=passport_data)
    user_data = {"passport_data": passport_data}
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = (
        f"{_.get_text('passport_manual_issue_date.title', lang)}\n"
        f"{_.get_text('passport_manual_issue_date.example_text', lang)}"
    )
    await message.answer(text=text, reply_markup=None)
    await state.set_state(PassportManualStates.passport_expiry_date_input)


@passport_manual_router.message(PassportManualStates.passport_expiry_date_input)
async def handle_passport_issue_date_input(message: Message, state: FSMContext):
    """Handle the input of the passport issue date in manual passport handling."""
    passport_data_all = await state.get_data()
    passport_data = passport_data_all.get("passport_data")
    passport_issue_date = message.text.strip()
    passport_data["passport_issue_date"] = passport_issue_date

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(passport_data=passport_data)
    user_data = {"passport_data": passport_data}
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    if state_data.get("skip_passport_expiry_date"):
        await handle_passport_expiry_date_input(message, state)
    else:
        text = (
            f"{_.get_text('passport_manual_expire_date.title', lang)}\n"
            f"{_.get_text('passport_manual_expire_date.example_text', lang)}"
        )
        await message.answer(text=text, reply_markup=None)
        await state.set_state(PassportManualStates.passport_issue_place_input)


@passport_manual_router.message(PassportManualStates.passport_issue_place_input)
async def handle_passport_expiry_date_input(message: Message, state: FSMContext):
    """Handle the input of the passport expiry date in manual passport handling."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    if state_data.get("skip_passport_expiry_date"):
        await state.update_data(skip_passport_expiry_date=False)
    else:
        passport_data_all = await state.get_data()
        passport_data = passport_data_all.get("passport_data")
        passport_expiry_date = message.text.strip()
        passport_data["passport_expiry_date"] = passport_expiry_date

        await state.update_data(passport_data=passport_data)
        user_data = {"passport_data": passport_data}
        session_id = state_data.get("session_id")
        data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await state.update_data(waiting_data="passport_data.passport_issue_place")
    text = (
        f"{_.get_text('passport_manual_issue_place.title', lang)}\n"
        f"{_.get_text('passport_manual_issue_place.example_text', lang)}"
    )
    await message.answer(text=text, reply_markup=None)

    next_states = state_data.get("next_states", [])
    from_action = state_data.get("from_action")
    print(f"Next states: {next_states}, From action: {from_action}")

    if len(next_states) == 1:
        print("Only one next state available, setting to from_action")
        await state.set_state(from_action)
    elif len(next_states) > 0:
        print(f"Next states available: {next_states}")
        next_state = next_states[0]
        await state.set_state(next_state)
    else:
        print("No next states found, returning to from_action")
        await state.set_state(from_action)

    print(f"Next state set to: {next_state if next_states else from_action}")
