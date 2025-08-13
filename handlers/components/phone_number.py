from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.components.phone_number import PhoneNumberStates

from localization import _
from data_manager import SecureDataManager

phone_number_router = Router()
data_manager = SecureDataManager()


@phone_number_router.message(PhoneNumberStates.phone_number_input)
async def handle_phone_number_input(message: Message, state: FSMContext):
    """Обработка ввода номера телефона"""

    # Получение данных состояния
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")

    # Сохранение номера телефона в менеджер данных
    waiting_data = state_data.get("waiting_data", None)

    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: message.text.strip(),
    }
    await state.update_data({waiting_data: message.text.strip()})
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    # Отправка подтверждения пользователю
    text = f"{_.get_text('phone_number.title', lang)}\n{_.get_text('phone_number.example_text', lang)}"
    await message.answer(text=text)
    await state.update_data(waiting_data="phone_number")
    # Переход к следующему состоянию, если есть
    next_states = state_data.get("next_states", [])
    from_action = state_data.get("from_action")
    print(f"Next states: {next_states}, From action: {from_action}")
    if len(next_states) == 1:
        print("Only one next state available, setting to from_action")
        await state.set_state(from_action)
    elif len(next_states) > 0:
        print(f"Next states available: {next_states}")
        next_state = next_states[1:][0]
        await state.update_data(next_states=next_states[1:])
        await state.set_state(next_state)
    else:
        print("No next states found, returning to from_action")
        # If no next states, return to the previous action
        await state.set_state(from_action)
