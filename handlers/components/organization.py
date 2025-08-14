from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.components.organization import OrganizationStates
from keyboards.components.orgranization import *

from localization import _
from data_manager import SecureDataManager

organization_router = Router()
data_manager = SecureDataManager()


@organization_router.callback_query(F.data == "organization_accept")
async def handle_organization_start(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual passport input."""
    
    print('Оббработчик')

    # Set the state for manual passport handling
    await state.set_state(OrganizationStates.name_organization)

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # passport_title = state_data.get("passport_title", "")
    # passport_description = state_data.get("passport_description", 'passport_manual_full_name.description')

    # Prepare the initial message for manual passport input
    text = f"{_.get_text("name_org_migr_card_arrival.title", lang)}\n\n{_.get_text("name_org_migr_card_arrival.example", lang)}"

    # Update the state with the action context
    await state.set_state(OrganizationStates.inn)
    # Send the initial message to the user
    await callback.message.edit_text(
        text=text, reply_markup=inn_organization(lang)
    )


@organization_router.message(OrganizationStates.inn)
async def request_inn_organization_input(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    organization_data = {}
    name_org = message.text.strip()
    organization_data["name_org"] = name_org
    # # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the full name
    await state.update_data(organization_data=organization_data )
    user_data = {
        "organization_data ": organization_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('inn_org_migr_card_arrival.title', lang)}\n{_.get_text('inn_org_migr_card_arrival.example', lang)}"
    await message.answer(text=text, reply_markup=None)  # No keyboard for this step
    # Move to the next state
    await state.set_state(OrganizationStates.inn)
    
@organization_router.message(OrganizationStates.inn)
async def handle_inn_inp(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    organization_data= await state.get_data()
    organization_data = organization_data.get("organization_data")
    inn = message.text.strip()
    organization_data["inn"] = inn
    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the full name
    await state.update_data(organization_data=organization_data)
    user_data = {
        "organization_data ": organization_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('addres_by_migr_card_arrival.title', lang)}\n{_.get_text('addres_by_migr_card_arrival.example', lang)}"
    await message.answer(text=text, reply_markup=None)

    await state.set_state(OrganizationStates.adress)


@organization_router.message(OrganizationStates.adress)
async def handle_adress_inp(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    organization_data= await state.get_data()
    organization_data = organization_data.get("organization_data")
    adress = message.text.strip()
    organization_data["adress"] = adress
    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the full name
    await state.update_data(organization_data=organization_data)
    user_data = {
        "organization_data ": organization_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('fio_migr_card_arrival.title', lang)}\n{_.get_text('fio_migr_card_arrival.example', lang)}"
    await message.answer(text=text, reply_markup=None)

    await state.set_state(OrganizationStates.full_name_contact_of_organization)


@organization_router.message(OrganizationStates.full_name_contact_of_organization)
async def handle_full_name_contact_of_organization(message: Message, state: FSMContext):
    """Handle the input of the citizenship in manual passport handling."""
    organization_data = await state.get_data()
    organization_data = organization_data.get("organization_data")
    full_name_contact_of_organization = message.text.strip()
    organization_data["full_name_contact_of_organization"] = full_name_contact_of_organization

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the citizenship
    await state.update_data(organization_data=organization_data)
    user_data = {
        "organization_data": organization_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('fio_migr_card_arrival.title', lang)}\n{_.get_text('fio_migr_card_arrival.example', lang)}"
    await message.answer(text=text, reply_markup=None)

    await state.set_state(OrganizationStates.phone_contact_of_organization)


@organization_router.message(OrganizationStates.phone_contact_of_organization)
async def handle_job(message: Message, state: FSMContext):
    """Handle the input of the passport serial number in manual passport handling."""
    organization_data = await state.get_data()
    organization_data = organization_data.get("organization_data")
    phone_contact_of_organization = message.text.strip()
    organization_data["phone_contact_of_organization"] = phone_contact_of_organization

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport serial number
    await state.update_data(organization_data=organization_data)
    user_data = {
        "organization_data": organization_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    await state.update_data(waiting_data="profession")

    text = f"{_.get_text('ur_job.title', lang)}\n{_.get_text('ur_job.example', lang)}"
    await message.answer(text=text, reply_markup=ur_work(lang))

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

