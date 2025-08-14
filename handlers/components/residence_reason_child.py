from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.components.residence_reason_marriage import (
    get_residence_reason_photo_or_manual_keyboard,
)
from states.components.residence_reason_marriage import ResidenceReasonMarriageStates

from localization import _
from data_manager import SecureDataManager

residence_reason_marriage_router = Router()
data_manager = SecureDataManager()


@residence_reason_marriage_router.callback_query(F.data == "residence_reason_marriage")
async def handle_residence_reason_marriage(callback: CallbackQuery, state: FSMContext):
    """Handle the selection of residence reason patent input method."""

    # Set the state for choosing photo or manual input
    await state.set_state(ResidenceReasonMarriageStates.choose_photo_or_manual)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message with options for photo or manual input
    text = _.get_text("start_residence_reason.description", lang)
    await callback.message.edit_text(
        text=text, reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )


@residence_reason_marriage_router.callback_query(
    F.data == "start_residence_reason_marriage_manual"
)
async def handle_start_manual(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual input for residence reason marriage."""

    # Set the state for manual input
    await state.set_state(ResidenceReasonMarriageStates.spouse_fio)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message to start manual input
    text = f"{_.get_text('residence_reason_manual_marriage_messages.full_name.title', lang)}\n\n{_.get_text('residence_reason_manual_marriage_messages.full_name.description', lang)}\n{_.get_text('residence_reason_manual_marriage_messages.full_name.example_text', lang)}"
    await callback.message.edit_text(text=text)


@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.spouse_fio)
async def get_spouse_fio(message: Message, state: FSMContext):
    """Handle the input of spouse full name for residence reason marriage."""
    spouse_fio = message.text.strip()
    # Set the state for spouse full name input
    await state.set_state(ResidenceReasonMarriageStates.issue_date)
    await state.update_data(spouse_fio=spouse_fio)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter their spouse's birth date
    text = f"{_.get_text("residence_reason_manual_marriage_messages.marriage_date.title", lang)}\n{_.get_text("residence_reason_manual_marriage_messages.marriage_date.example_text", lang)}"
    await message.answer(text=text)


@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.issue_date)
async def get_issue_date(message: Message, state: FSMContext):
    """Handle the input of issue date for residence reason marriage."""
    issue_date = message.text.strip()
    # Set the state for issue date input
    await state.set_state(ResidenceReasonMarriageStates.marriage_number)
    await state.update_data(issue_date=issue_date)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter their marriage number
    text = f"{_.get_text('residence_reason_manual_marriage_messages.marriage_certificate.title', lang)}\n{_.get_text('residence_reason_manual_marriage_messages.marriage_certificate.example_text', lang)}"
    await message.answer(text=text)


@residence_reason_marriage_router.message(ResidenceReasonMarriageStates.marriage_number)
async def get_marriage_number(message: Message, state: FSMContext):
    """Handle the input of marriage number for residence reason marriage."""
    marriage_number = message.text.strip()
    # Set the state for marriage number input
    await state.set_state(ResidenceReasonMarriageStates.issue_place)
    await state.update_data(marriage_number=marriage_number)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter the place of issue
    text = f"{_.get_text('residence_reason_manual_marriage_messages.marriage_issue_place.title', lang)}\n{_.get_text('residence_reason_manual_marriage_messages.marriage_issue_place.example_text', lang)}"
    await message.answer(text=text)
    await state.update_data(waiting_data="marriage_issue_place")
    next_states = state_data.get("next_states", [])
    from_action = state_data.get("from_action")
    if len(next_states) > 0:
        next_state = next_states[0]
        await state.set_state(next_state)
    else:
        # If no next states, return to the previous action
        await state.set_state(from_action)
