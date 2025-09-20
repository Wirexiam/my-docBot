from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from states.components.representative import RepresentativeStates

from keyboards.components.representative import kbs_who_guardian

from localization import _
from data_manager import SecureDataManager

representative_router = Router()
data_manager = SecureDataManager()


@representative_router.message(RepresentativeStates.who_representative)
async def handle_live_who_input(message: Message, state: FSMContext):
    """Обработка ввода адреса проживания в РФ"""
    # Получение данных состояния
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    message_data = message.text.strip()

    waiting_data = state_data.get("waiting_data", None)
    data = message.text.strip()
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: message_data,
    }
    await state.update_data({waiting_data: message_data})

    text = f"{_.get_text('representative_who.title', lang)}"
    await message.answer(text=text, reply_markup=kbs_who_guardian(lang))
    await state.set_state(RepresentativeStates.full_name_representative)


@representative_router.callback_query(RepresentativeStates.full_name_representative)
async def handle_live_full_name_input(call: CallbackQuery, state: FSMContext):
    """Обработка ввода адреса проживания в РФ"""
    # Получение данных состояния
    who = call.data
    representative_data = {}
    representative_data["who"] = who
    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the full name
    await state.update_data(representative_data=representative_data)
    user_data = {
        "representative_data": representative_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(call.from_user.id, session_id, user_data)

    text = f"{_.get_text('fio_repr.title', lang)}\n\n{_.get_text('fio_repr.example', lang)}"
    await call.message.edit_text(text=text, reply_markup=None)
    await state.set_state(RepresentativeStates.data_birth_representative)


@representative_router.message(RepresentativeStates.data_birth_representative)
async def handle_live_full_name_input(message: Message, state: FSMContext):
    """Обработка ввода адреса проживания в РФ"""
    # Получение данных состояния
    representative_data = await state.get_data()
    representative_data = representative_data.get("representative_data")
    full_name = message.text.strip()
    representative_data["full_name"] = full_name
    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the full name
    await state.update_data(representative_data=representative_data)
    user_data = {
        "representative_data": representative_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    await state.update_data(waiting_data="birth_date_cert")

    text = f"{_.get_text('representative_birth_date.title', lang)}\n{_.get_text('representative_birth_date.example_text', lang)}"
    await message.answer(text=text, reply_markup=None)
    # await state.set_state(RepresentativeStates.data_birth_representative)
    next_states = state_data.get("next_states", [])
    from_action = state_data.get("from_action")
    if len(next_states) == 1:
        await state.set_state(from_action)
    elif len(next_states) > 0:
        next_state = next_states[1:][0]
        await state.update_data(next_states=next_states[1:])
        await state.set_state(next_state)
    else:
        # If no next states, return to the previous action
        await state.set_state(from_action)


# @live_adress_router.message(LiveAdress.adress)
# async def handle_live_adress_input(message: Message, state: FSMContext):
#     """Обработка ввода адреса проживания в РФ"""
#     # Получение данных состояния
#     state_data = await state.get_data()
#     lang = state_data.get("language", "ru")
#     waiting_data = state_data.get("waiting_data", None)

#     # Сохранение адреса в менеджер данных
#     session_id = state_data.get("session_id")
#     if "." in waiting_data:
#         primary_key = waiting_data.split(".")[0]
#         secondary_key = waiting_data.split(".")[1]

#         primary_key_data = state_data.get(primary_key)
#         primary_key_data[secondary_key] = message.text.strip()

#         await state.update_data({primary_key: primary_key_data})

#     else:
#         user_data = {
#             waiting_data: message.text.strip(),
#         }
#         await state.update_data({waiting_data: message.text.strip()})
#         data_manager.save_user_data(message.from_user.id, session_id, user_data)

#     if state_data.get("live_adress_conf") is None:
#         photo = FSInputFile("static/live_adress_example.png")
#         # Отправка подтверждения пользователю

#         text = f"{_.get_text('live_adress.title', lang)}\n{_.get_text('live_adress.example', lang)}"
#     else:
#         photo = FSInputFile("static/live_adress.png")
#         text = f"{_.get_text('adress_residence_permit', lang)}"

#     await message.answer_photo(caption=text, photo=photo)
#     await state.update_data(waiting_data="live_adress")
#     next_states = state_data.get("next_states", [])
#     from_action = state_data.get("from_action")
#     if len(next_states) == 1:
#         await state.set_state(from_action)
#     elif len(next_states) > 0:
#         next_state = next_states[1:][0]
#         await state.update_data(next_states=next_states[1:])
#         await state.set_state(next_state)
#     else:
#         # If no next states, return to the previous action
#         await state.set_state(from_action)
