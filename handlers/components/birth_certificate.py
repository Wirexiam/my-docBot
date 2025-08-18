from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.components.cert_child import CertificateChildStates

from localization import _
from data_manager import SecureDataManager

birth_certificate_router = Router()
data_manager = SecureDataManager()


@birth_certificate_router.callback_query(F.data == "birth_certificate_manual")
async def handle_passport_manual_start(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual passport input."""

    # Set the state for manual passport handling
    await state.set_state(CertificateChildStates.choose_photo_or_manual)

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")


    # Prepare the initial message for manual passport input
    text = f"{_.get_text("name_migr_card_cert.title", lang)}\n{_.get_text("name_migr_card_cert.description", lang)}\n\n{_.get_text("name_migr_card_cert.fio_kid", lang)}\n{_.get_text("name_migr_card_cert.example", lang)}"

    # Send the initial message to the user
    await callback.message.edit_text(
        text=text, reply_markup=None  # No keyboard for this step
    )
    await state.set_state(CertificateChildStates.child_fio)


@birth_certificate_router.message(CertificateChildStates.child_fio)
async def request_birth_date_input(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    child_fio = message.text.strip()
    child_cert_info = {}
    child_cert_info["full_name"] = child_fio
    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the full name
    await state.update_data(child_cert_info=child_cert_info)
    user_data = {
        "child_cert_info": child_cert_info,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # Get the user's language preference from state data
    # Update the state with the full name
    text = f"{_.get_text('passport_manual_birth_date.title', lang)}\n{_.get_text('passport_manual_birth_date.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)  # No keyboard for this step
    # Move to the next state
    await state.set_state(CertificateChildStates.child_birth_date)


@birth_certificate_router.message(CertificateChildStates.child_birth_date)
async def handle_birth_date_input(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    child_birth_date = message.text.strip()
    child_cert_info = await state.get_data()
    child_cert_info = child_cert_info.get("child_cert_info")
    child_cert_info["birth_date"] = child_birth_date

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the birth date
    await state.update_data(child_cert_info=child_cert_info)
    user_data = {
        "child_cert_info": child_cert_info,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # Get the user's language preference from state data

    # Update the state with the birth date

    text = f"{_.get_text('passport_manual_citizenship.title', lang)}\n{_.get_text('passport_manual_citizenship.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)


    await state.set_state(CertificateChildStates.child_citizenship)


@birth_certificate_router.message(CertificateChildStates.child_citizenship)
async def handle_citizenship_input(message: Message, state: FSMContext):
    """Handle the input of the citizenship in manual passport handling."""
    child_citizenship = message.text.strip()
    child_cert_info = await state.get_data()
    child_cert_info = child_cert_info.get("child_cert_info")
    child_cert_info["child_citizenship"] = child_citizenship

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the birth date
    await state.update_data(child_cert_info=child_cert_info)
    user_data = {
        "child_cert_info": child_cert_info,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    # Get the user's language preference from state data

    text = f"{_.get_text('birth_cert_numb.title', lang)}\n{_.get_text('birth_cert_numb.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)

    await state.set_state(CertificateChildStates.child_certificate_number)
    
@birth_certificate_router.message(CertificateChildStates.child_certificate_number)
async def handle_citizenship_input(message: Message, state: FSMContext):
    """Handle the input of the citizenship in manual passport handling."""
    child_certificate_number = message.text.strip()
    child_cert_info = await state.get_data()
    child_cert_info = child_cert_info.get("child_cert_info")
    child_cert_info["child_certificate_number"] = child_certificate_number

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the birth date
    await state.update_data(child_cert_info=child_cert_info)
    user_data = {
        "child_cert_info": child_cert_info,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # Update the state with the citizenship

    text = f"{_.get_text('cert_issue_place.title', lang)}\n{_.get_text('cert_issue_place.example_text', lang)}"

    await state.update_data(waiting_data="child_certificate_issue_place")
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
        # If no next states, return to the previous action
        await state.set_state(from_action)
    print(f"Next state set to: {next_state if next_states else from_action}")

