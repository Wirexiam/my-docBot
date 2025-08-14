from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from states.components.home_migr_data import HomeMigrData

from keyboards.components.home_migr_data import kbs_have_doc

from states.arrival import Arrival_transfer

from localization import _
from data_manager import SecureDataManager

home_migr_data = Router()
data_manager = SecureDataManager()


@home_migr_data.message(HomeMigrData.adress)
async def handle_adress_migr_input(message: Message, state: FSMContext):
    """Обработка ввода адреса проживания в РФ"""
    # Получение данных состояния
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    waiting_data = state_data.get("waiting_data", None)

    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: message.text.strip(),
    }
    await state.update_data({waiting_data: message.text.strip()})
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    photo = FSInputFile("static/live_adress_example.png")
    # Отправка подтверждения пользователю

    text = f"{_.get_text('live_adress.title', lang)}\n{_.get_text('live_adress.example', lang)}"

    await message.answer_photo(caption=text, photo=photo)
    await state.set_state(HomeMigrData.havedoc)
    # await state.update_data(waiting_data="adress")
    # next_states = state_data.get("next_states", [])
    # from_action = state_data.get("from_action")
    # if len(next_states) == 1:
    #     await state.set_state(from_action)
    # elif len(next_states) > 0:
    #     next_state = next_states[1:][0]
    #     await state.update_data(next_states=next_states[1:])
    #     await state.set_state(next_state)
    # else:
    #     # If no next states, return to the previous action
    #     await state.set_state(from_action)
    
@home_migr_data.message(HomeMigrData.havedoc)
async def handle_adress_migr_input(message: Message, state: FSMContext):
    """Обработка ввода адреса проживания в РФ"""
    # Получение данных состояния
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    migration_data['live_adress'] = message.text.strip()
    
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # Отправка подтверждения пользователю

    text = f"{_.get_text('doc_migr_card_arrival.title', lang)}\n{_.get_text('doc_migr_card_arrival.example', lang)}"

    await message.answer(text, reply_markup=kbs_have_doc(lang))
    await state.set_state(Arrival_transfer.after_about_home)
     
@home_migr_data.callback_query(F.data == "havedoc")
async def handle_access_doc(call: CallbackQuery, state: FSMContext):
    """Обработка ввода адреса проживания в РФ"""
    # Получение данных состояния
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")

    text = f"{_.get_text('doc_details_migr_card_arrival.title', lang)}\n{_.get_text('doc_details_migr_card_arrival.example', lang)}"
    
    await call.message.answer(text=text, reply_markup=None)
    # await state.set_state(Arrival_transfer.after_about_home)
    
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
