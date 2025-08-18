from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.changing_data import start_changing_data_keyboard
from handlers.doc_residence_notification import (
    get_income_last_year_msg,
    get_travel_outside_Ru_msg,
    get_worked_last_year_msg,
)
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
    "RP_issue_date",
    "RP_issue_place",
    "RP_serial_number",
    "date",
    "dismissal_date",
    "hiring_date",
    "is_working",
    "job_title",
    "live_adress_conf",
    "place",
    "sema_components",
    "work_adress",
    "change_id",
    "org_name",
    "is_now_edit",
    "form_NDFL",
    "income",
    "residence_reason",
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
        elif type(data) == dict:
            btn_text = f"change_{data_key}_dict_btn"
            keyboard_data.append(
                {
                    "btn_text": btn_text,
                    "callback_text": f"change_dict_{data_key}",
                }
            )
        elif type(data) == list:
            btn_text = f"change_{data_key}_list_btn"
            keyboard_data.append(
                {
                    "btn_text": btn_text,
                    "callback_text": f"change_list_{data_key}",
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


@changing_data_router.callback_query(F.data.startswith("change_list_"))
async def handle_change_dict_data(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    callback_data = callback.data.split("change_list_")[1].split(":")
    print(callback_data)
    dict_key = callback_data[0]
    id = int(callback_data[1]) if len(callback_data) > 1 else None

    list_data = state_data.get(dict_key, [])
    lang = state_data.get("language", "ru")
    keyboard_data = []

    old_dict_key = dict_key
    if id is None:
        # first_key = next(iter(list_data[0]))
        keys = list(list_data[0].keys())[:2]
        for i, list_el in enumerate(list_data):
            btn_text = f"{i+1}, {list_el[keys[0]]} {list_el[keys[1]]}"

            if dict_key == "income_last_year":
                if list_el[keys[0]] == "no" and keys[0] == "form_NDFL":
                    btn_text = f"{i+1}, {_.get_text('doc_residence_notification.no_income', lang)}"
                elif keys[0] == "form_NDFL":
                    btn_text = f"{i+1}, {_.get_text(f'income_last_year.message_1.{list_el[keys[0]]}', lang)}"

            keyboard_data.append(
                {
                    "btn_text": btn_text,
                    "callback_text": f"change_list_{old_dict_key}:{i}",
                }
            )

    else:
        el = list_data[id]
        list_data.pop(id)
        print(el)

        state_data = await state.get_data()
        pprint(state_data)
        await state.update_data({"change_id": id, "is_now_edit": True})

        if dict_key == "worked_last_year":
            await get_worked_last_year_msg(callback, state)
        elif dict_key == "income_last_year":
            await get_income_last_year_msg(callback, state)
        elif dict_key == "travel_outside_Ru":
            await get_travel_outside_Ru_msg(callback, state)
        return

    text = _.get_text("what_change_before_gen", lang)

    # pprint(keyboard_data)
    # return_to = f"change_list_{dict_key}"
    await callback.message.edit_text(
        text=text,
        reply_markup=start_changing_data_keyboard(
            lang=lang, buttons=keyboard_data, custom_text=True
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
