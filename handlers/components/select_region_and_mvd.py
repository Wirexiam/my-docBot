from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext


from keyboards.components.select_region_and_mvd import get_select_region_keyboard
from states.components.select_region_and_mvd import SelectRegionStates
from localization import _
from data_manager import SecureDataManager

select_region_router = Router()
data_manager = SecureDataManager()


@select_region_router.callback_query(F.data == "select_region_and_mvd")
async def handle_select_region_and_mvd(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки выбора региона и МВД"""

    # Установка состояния для выбора региона и МВД
    await state.set_state(SelectRegionStates.start_msg)
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Отправка сообщения с инструкциями

    text = f"{_.get_text('region_start_msg.title', lang)}\n\n{_.get_text('region_start_msg.description', lang)}"
    await callback.message.edit_text(
        text=text,
    )
    await state.set_state(SelectRegionStates.getting_text)


@select_region_router.message(SelectRegionStates.getting_text)
async def handle_getting_text_and_confirm(message: Message, state: FSMContext):
    """Обработка текста и подтверждения выбора региона и МВД"""
    # Получение текста сообщения
    text = message.text.strip()

    state_data = await state.get_data()
    lang = state_data.get("language")
    from_action = state_data.get("from_action")
    await state.update_data(mvd_adress=text)

    text_to_send = f"{_.get_text('region_start_msg_confirm.title', lang)}\n\n{_.get_text('region_start_msg_confirm.example_text', lang)}{text}\n\n{_.get_text('region_start_msg_confirm.description', lang)}"
    await message.answer(
        text=text_to_send,
        reply_markup=get_select_region_keyboard(lang, from_action),
    )
