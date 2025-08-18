from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext


from keyboards.components.residence_reason_child import (
    get_residence_reason_photo_or_manual_keyboard,
    get_residence_reason_who_for_child_keyboard,
)
from states.components.residence_reason_child import ResidenceReasonChildStates


from localization import _
from data_manager import SecureDataManager


residence_reason_child_router = Router()
data_manager = SecureDataManager()


@residence_reason_child_router.callback_query(F.data == "residence_reason_child")
async def handle_residence_reason_patent(callback: CallbackQuery, state: FSMContext):
    """Handle the selection of residence reason patent input method."""

    # Set the state for choosing photo or manual input
    await state.set_state(ResidenceReasonChildStates.choose_photo_or_manual)
    await state.update_data(residence_reason="residence_reason_child")

    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message with options for photo or manual input
    text = _.get_text("start_residence_reason.description", lang)
    await callback.message.edit_text(
        text=text, reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )


@residence_reason_child_router.callback_query(
    F.data == "start_residence_reason_child_manual"
)
async def handle_start_manual(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual input for residence reason child."""

    # Set the state for manual input
    await state.set_state(ResidenceReasonChildStates.child_fio)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message with options for who the residence reason is for child
    text = f"{_.get_text("residence_reason_manual_child_messages.child_fio.title", lang)}\n"
    text += f"\n{_.get_text('residence_reason_manual_child_messages.child_fio.description', lang)}\n\n"
    text += f"{_.get_text('residence_reason_manual_child_messages.child_fio.name_text', lang)}\n"
    text += f"{_.get_text('residence_reason_manual_child_messages.child_fio.example_text', lang)}"

    await callback.message.edit_text(text=text)


@residence_reason_child_router.message(ResidenceReasonChildStates.child_fio)
async def get_child_fio(message: Message, state: FSMContext):
    """Handle the input of child's full name for residence reason child."""
    child_fio = message.text.strip()
    child_data = {"child_fio": child_fio}
    await state.update_data(child_data=child_data)

    # Set the state for child's birth date input
    await state.set_state(ResidenceReasonChildStates.child_birth_date)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter child's birth date
    text = f"{_.get_text('residence_reason_manual_child_messages.child_birth_date.title', lang)}\n"
    text += f"{_.get_text('residence_reason_manual_child_messages.child_birth_date.example_text', lang)}"
    await message.answer(text=text)


@residence_reason_child_router.message(ResidenceReasonChildStates.child_birth_date)
async def get_child_birth_date(message: Message, state: FSMContext):
    """Handle the input of child's birth date for residence reason child."""

    # Set the state for child's citizenship input
    await state.set_state(ResidenceReasonChildStates.child_citizenship)
    state_data = await state.get_data()
    lang = state_data.get("language")

    child_data = state_data.get("child_data", {})
    child_data["child_birth_date"] = message.text.strip()
    await state.update_data(child_data=child_data)
    # Prompt the user to enter child's citizenship
    text = f"{_.get_text('residence_reason_manual_child_messages.child_citizenship.title', lang)}\n"
    text += f"{_.get_text('residence_reason_manual_child_messages.child_citizenship.example_text', lang)}"
    await message.answer(text=text)


@residence_reason_child_router.message(ResidenceReasonChildStates.child_citizenship)
async def get_child_citizenship(message: Message, state: FSMContext):
    """Handle the input of child's citizenship for residence reason child."""

    # Set the state for child's certificate number input
    await state.set_state(ResidenceReasonChildStates.child_certificate_number)
    state_data = await state.get_data()
    lang = state_data.get("language")

    child_data = state_data.get("child_data", {})
    child_data["child_citizenship"] = message.text.strip()
    await state.update_data(child_data=child_data)
    # Prompt the user to enter child's certificate number
    text = f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_number.title', lang)}\n"
    text += f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_number.example_text', lang)}"

    await message.answer(text=text)


@residence_reason_child_router.message(
    ResidenceReasonChildStates.child_certificate_number
)
async def get_child_certificate_number(message: Message, state: FSMContext):
    """Handle the input of child's certificate number for residence reason child."""

    # Set the state for child's certificate issue place input
    await state.set_state(ResidenceReasonChildStates.child_certificate_issue_place)
    state_data = await state.get_data()
    lang = state_data.get("language")

    child_data = state_data.get("child_data", {})
    child_data["child_certificate_number"] = message.text.strip()
    await state.update_data(child_data=child_data)
    # Prompt the user to enter child's certificate issue place
    text = f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_issue_place.title', lang)}\n"
    text += f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_issue_place.example_text', lang)}"

    await message.answer(text=text)


@residence_reason_child_router.message(
    ResidenceReasonChildStates.child_certificate_issue_place
)
async def get_child_certificate_issue_place(message: Message, state: FSMContext):
    """Handle the input of child's certificate issue place for residence reason child."""
    # Set the state for choosing who the residence reason is for child
    await state.set_state(ResidenceReasonChildStates.who_for_child)
    state_data = await state.get_data()
    lang = state_data.get("language")
    child_data = state_data.get("child_data", {})
    child_data["child_certificate_issue_place"] = message.text.strip()
    await state.update_data(child_data=child_data)
    # Send a message with options for who the residence reason is for child
    text = _.get_text(
        "residence_reason_manual_child_messages.who_for_child.description", lang
    )
    await message.answer(
        text=text, reply_markup=get_residence_reason_who_for_child_keyboard(lang)
    )
