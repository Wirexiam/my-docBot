from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.migr_card import MigrCardManualStates

from localization import _
from data_manager import SecureDataManager
from keyboards.migration_card import *

from datetime import datetime, timedelta

migration_manual_router = Router()
data_manager = SecureDataManager()


@migration_manual_router.callback_query(F.data == "migration_manual_start")
async def handle_migr_manual_start(callback: CallbackQuery, state: FSMContext):
    """Handle the start of manual migratuion card input."""

    # Set the state for migr card handling
    # await state.set_state(PassportManualStates.full_name_input)

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    
    # Prepare the initial message for manual passport input
    text = f"{_.get_text('name_migr_card_arrival.title')}\n\n{_.get_text('name_migr_card_arrival.description', lang)}"

    # Update the state with the action context
    await state.set_state(MigrCardManualStates.entry_date_input)
    # Send the initial message to the user
    await callback.message.edit_text(
        text=text, reply_markup=None  # No keyboard for this step
    )


@migration_manual_router.message(MigrCardManualStates.entry_date_input)
async def request_birth_date_input(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    migration_data = {}
    full_name = message.text.strip()
    migration_data["full_name"] = full_name
    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the full name
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('data_migr_card_arrival.title', lang)}\n{_.get_text('data_migr_card_arrival.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)  # No keyboard for this step
    # Move to the next state
    await state.set_state(MigrCardManualStates.citizenship_input)


@migration_manual_router.message(MigrCardManualStates.citizenship_input)
async def handle_entry_date_input(message: Message, state: FSMContext):
    """Handle the input of the birth date in manual passport handling."""
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    entry_date = message.text.strip()
    migration_data["entry_date"] = entry_date

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the birth date
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('passport_manual_citizenship.title', lang)}\n{_.get_text('passport_manual_citizenship.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)

    await state.set_state(MigrCardManualStates.place_point_input)


@migration_manual_router.message(MigrCardManualStates.place_point_input)
async def handle_citizenship_input(message: Message, state: FSMContext):
    """Handle the input of the citizenship in manual passport handling."""
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    citizenship = message.text.strip()
    migration_data["citizenship"] = citizenship

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the citizenship
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('country_point_migr_card_arrival.title', lang)}\n{_.get_text('country_point_migr_card_arrival.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)

    await state.set_state(MigrCardManualStates.card_serial_number_input)


@migration_manual_router.message(MigrCardManualStates.card_serial_number_input)
async def handle_card_serial_number_input(message: Message, state: FSMContext):
    """Handle the input of the passport serial number in manual passport handling."""
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    card_serial_number = message.text.strip()
    migration_data["card_serial_number"] = card_serial_number

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport serial number
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('number_migr_card_arrival.title', lang)}\n{_.get_text('number_migr_card_arrival.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)

    await state.set_state(MigrCardManualStates.pretria_period_input)



@migration_manual_router.message(MigrCardManualStates.pretria_period_input)
async def handle_number_migr_card_arrival_input(message: Message, state: FSMContext):
    """Handle the input of the passport issue date in manual passport handling."""
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    number_migr_card_arrival = message.text.strip()
    migration_data["number_migr_card_arrival"] = number_migr_card_arrival

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport issue date
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('time_migr_card_arrival.title', lang)}\n{_.get_text('time_migr_card_arrival.example', lang)}"
    await message.answer(text=text, reply_markup=kbs_for_no_specified(lang))

    await state.set_state(MigrCardManualStates.goal)
    
@migration_manual_router.callback_query(MigrCardManualStates.goal)
async def handle_number_migr_card_pretria_period_callback(call: CallbackQuery, state: FSMContext):
    """Handle the input of the passport issue date in manual passport handling."""
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    entry_data = datetime.strptime(migration_data["entry_date"], "%d.%m.%Y")
    entry_data_no_specified = entry_data + timedelta(days=90)
    entry_data_str = entry_data_no_specified.strftime("%d.%m.%Y") 
    migration_data["pretria_period"] = entry_data_str

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport expiry date
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(call.from_user.id, session_id, user_data)

    text = f"{_.get_text('goals_migr_card_arrival.title', lang)}"
    await call.message.answer(text=text, reply_markup=kbs_for_goals(lang))

    await state.set_state(MigrCardManualStates.before_select_goal)
     
@migration_manual_router.message(MigrCardManualStates.goal)
async def handle_number_migr_card_pretria_period(message: Message, state: FSMContext):
    """Handle the input of the passport issue date in manual passport handling."""
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    pretria_period = message.text.strip()
    migration_data["pretria_period"] = pretria_period

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport expiry date
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('goals_migr_card_arrival.title', lang)}"
    await message.answer(text=text, reply_markup=kbs_for_goals(lang))

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


@migration_manual_router.callback_query(F.data == "other")
async def handle_passport_expiry_goal_manual(call: CallbackQuery, state: FSMContext):
    """Handle the input of the passport expiry date in manual passport handling."""
    
    # Get the user's language preference from state data
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    state_data = await state.get_data()
    lang = state_data.get("language")
    
    text = f"{_.get_text('goal_migr_card_arrival.title', lang)}\n{_.get_text('goal_migr_card_arrival.example', lang)}"
    await call.message.edit_text(text=text, reply_markup=None)
    
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(call.from_user.id, session_id, user_data)
    
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
    
    
@migration_manual_router.message(MigrCardManualStates.after_select_goal)
async def handle_passport_expiry_goal_manual(message: Message, state: FSMContext):
    """Handle the input of the passport expiry date in manual passport handling."""
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    goal = message.text.strip()
    migration_data["goal"] = goal

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport expiry date
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # await state.update_data(waiting_data="passport_issue_place")
    text = f"{_.get_text('passport_manual_issue_place.title', lang)}\n{_.get_text('passport_manual_issue_place.example_text', lang)}"
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
