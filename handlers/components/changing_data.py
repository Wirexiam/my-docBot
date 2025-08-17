from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.changing_data import start_changing_data_keyboard

from localization import _
from data_manager import SecureDataManager

changing_data_router = Router()
data_manager = SecureDataManager()

data_blacklist = [
    "from_action",
    "language",
    "next_states",
    "session_id",
    "waiting_data",
    "passport_title",
    "change_data_from",
    "change_data_from_check",
]


@changing_data_router.callback_query(F.data.startswith("change_data_"))
async def handle_change_data(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки изменения данных"""

    # Получение текущего состояния и языка
    state_data = await state.get_data()
    await state.update_data(change_data_from=callback.data)
    lang = state_data.get("language", "ru")
    keyboard_data = []

    for data_key in state_data:
        if data_key in data_blacklist:
            continue
        data = state_data[data_key]
        if type(data) == str:
            btn_text = f"change_{data_key}_btn"
            keyboard_data.append(
                {
                    "btn_text": btn_text,
                    "callback_text": f"change_value_{data_key}",
                }
            )
        if type(data) == dict:
            btn_text = f"change_{data_key}_dict_btn"
            keyboard_data.append(
                {
                    "btn_text": btn_text,
                    "callback_text": f"change_dict_{data_key}",
                }
            )
    text = _.get_text("what_change_before_gen", lang)
    pprint(keyboard_data)
    change_data_from_check = state_data.get("change_data_from_check", "main_menu")
    await callback.message.edit_text(
        text=text,
        reply_markup=start_changing_data_keyboard(
            change_data_from_check, lang, buttons=keyboard_data
        ),
    )


@changing_data_router.callback_query(F.data.startswith("change_dict_"))
async def handle_change_dict_data(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    return_to = state_data.get("change_data_from")
    dict_key = callback.data.split("change_dict_")[1]
    state_data = state_data.get(dict_key, {})
    lang = state_data.get("language", "ru")
    keyboard_data = []
    old_dict_key = dict_key
    for data_key in state_data:
        if data_key in data_blacklist:
            continue
        data = state_data[data_key]
        if type(data) == str:
            btn_text = f"change_{data_key}_btn"
            keyboard_data.append(
                {
                    "btn_text": btn_text,
                    "callback_text": f"change_value_{old_dict_key}.{data_key}",
                }
            )
    text = _.get_text("what_change_before_gen", lang)
    await callback.message.edit_text(
        text=text,
        reply_markup=start_changing_data_keyboard(
            return_to,
            lang,
            buttons=keyboard_data,
        ),
    )


@changing_data_router.callback_query(F.data.startswith("change_value_"))
async def handle_change_value_data(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    dict_key = callback.data.split("change_value_")[1]
    lang = state_data.get("language", "ru")

    await state.update_data({"waiting_data": dict_key})
    from_action = state_data.get("from_action", None)
    if from_action is not None:
        await state.set_state(from_action)
    text = _.get_text(callback.data, lang)
    await callback.message.edit_text(text=text)
