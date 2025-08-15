from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.components.residence_permit import (
    get_residence_permit_photo_or_manual_keyboard,
)
from states.components.residence_permit import ResidencePermitDataStates

from localization import _
from data_manager import SecureDataManager

residence_permit_router = Router()
data_manager = SecureDataManager()


async def func_residence_permit(message: Message, state: FSMContext, text_key=None):
    """Handle the selection of residence reason  input method."""
    if text_key is None:
        text_key = "start_residence_permit"

    # Set the state for choosing photo or manual input
    await state.set_state(ResidencePermitDataStates.choose_photo_or_manual)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message with options for photo or manual input
    text = _.get_text(text_key, lang)
    await message.answer(
        text=text, reply_markup=get_residence_permit_photo_or_manual_keyboard(lang)
    )

@residence_permit_router.callback_query(F.data == "start_residence_permit_manual")
async def handle_start_manual(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual input for residence reason ."""

    # Set the state for manual input
    await state.set_state(ResidencePermitDataStates.serial_number)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Send a message to start manual input
    text = f"{_.get_text("residence_permit_manual_messages.serial_number.title", lang)}\n{_.get_text("residence_permit_manual_messages.serial_number.example_text", lang)}"
    await callback.message.edit_text(text=text)


@residence_permit_router.message(ResidencePermitDataStates.serial_number)
async def get_serial_number(message: Message, state: FSMContext):
    """Handle the input of patient number for residence reason ."""
    serial_number = message.text.strip()
    # Set the state for patient number input
    await state.set_state(ResidencePermitDataStates.issue_date)
    await state.update_data(RP_serial_number=serial_number)
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter their patient number
    text = f"{_.get_text("residence_permit_manual_messages.date.title", lang)}\n{_.get_text("residence_permit_manual_messages.date.example_text", lang)}"
    await message.answer(text=text)


@residence_permit_router.message(ResidencePermitDataStates.issue_date)
async def get_issue_date(message: Message, state: FSMContext):
    """Handle the input of issue date for residence reason ."""

    # Get the patient number from the message
    issue_date = message.text.strip()
    await state.update_data(RP_issue_date=issue_date)

    # Set the state for issue date input
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Prompt the user to enter the issue date
    text = f"{_.get_text("residence_permit_manual_messages.issue_place.title", lang)}\n{_.get_text("residence_permit_manual_messages.issue_place.example_text", lang)}"
    await message.answer(text=text)
    await state.update_data(waiting_data="RP_issue_place")
    next_states = state_data.get("next_states", [])
    from_action = state_data.get("from_action")
    if len(next_states) > 0:
        next_state = next_states[0]
        await state.set_state(next_state)
    else:
        # If no next states, return to the previous action
        await state.set_state(from_action)
