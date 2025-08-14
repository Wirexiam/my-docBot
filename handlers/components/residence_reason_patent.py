from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.components.residence_reason_patent import (
    get_residence_reason_photo_or_manual_keyboard,
)
from states.components.residence_reason_patent import ResidenceReasonPatentStates

from localization import _
from data_manager import SecureDataManager

residence_reason_patient_router = Router()
data_manager = SecureDataManager()


@residence_reason_patient_router.callback_query(F.data == "residence_reason_patent")
async def handle_residence_reason_patent(callback: CallbackQuery, state: FSMContext):
    """Handle the selection of residence reason patent input method."""

    # Set the state for choosing photo or manual input
    await state.set_state(ResidenceReasonPatentStates.choose_photo_or_manual)
    await state.update_data(residence_reason="residence_reason_patent")
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message with options for photo or manual input
    text = _.get_text("start_residence_reason.description", lang)
    await callback.message.edit_text(
        text=text, reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )


async def func_residence_reason_patent(message: Message, state: FSMContext, text_key):
    """Handle the selection of residence reason patent input method."""
    if text_key is None:
        text_key = "start_residence_reason.description"

    # Set the state for choosing photo or manual input
    await state.set_state(ResidenceReasonPatentStates.choose_photo_or_manual)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message with options for photo or manual input
    text = _.get_text(text_key, lang)
    await message.answer(
        text=text, reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )


@residence_reason_patient_router.callback_query(
    F.data == "start_residence_reason_patent_manual"
)
async def handle_start_manual(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual input for residence reason patent."""

    # Set the state for manual input
    await state.set_state(ResidenceReasonPatentStates.patient_numper)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message to start manual input
    text = f"{_.get_text("residence_reason_manual_patient_messages.patient_number.title", lang)}\n{_.get_text("residence_reason_manual_patient_messages.patient_number.example_text", lang)}"
    await callback.message.edit_text(text=text)


@residence_reason_patient_router.message(ResidenceReasonPatentStates.patient_numper)
async def get_patient_number(message: Message, state: FSMContext):
    """Handle the input of patient number for residence reason patent."""
    patient_number = message.text.strip()
    # Set the state for patient number input
    await state.set_state(ResidenceReasonPatentStates.issue_date)
    await state.update_data(patient_number=patient_number)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter their patient number
    text = f"{_.get_text("residence_reason_manual_patient_messages.patient_date.title", lang)}\n{_.get_text("residence_reason_manual_patient_messages.patient_date.example_text", lang)}"
    await message.answer(text=text)


@residence_reason_patient_router.message(ResidenceReasonPatentStates.issue_date)
async def get_issue_date(message: Message, state: FSMContext):
    """Handle the input of issue date for residence reason patent."""

    # Get the patient number from the message
    patient_date = message.text.strip()
    await state.update_data(patient_date=patient_date)

    # Set the state for issue date input
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter the issue date
    text = f"{_.get_text("residence_reason_manual_patient_messages.patient_issue_place.title", lang)}\n{_.get_text("residence_reason_manual_patient_messages.patient_issue_place.example_text", lang)}"
    await message.answer(text=text)
    await state.update_data(waiting_data="patient_issue_place")
    next_states = state_data.get("next_states", [])
    from_action = state_data.get("from_action")
    if len(next_states) > 0:
        next_state = next_states[0]
        await state.set_state(next_state)
    else:
        # If no next states, return to the previous action
        await state.set_state(from_action)
