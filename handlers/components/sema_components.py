from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State

from keyboards.components.inline_keyboard import get_callback_btns
from keyboards.components.residence_reason_patent import (
    get_residence_reason_photo_or_manual_keyboard,
)
from states.components.residence_reason_patent import ResidenceReasonPatentStates

from localization import _
from data_manager import SecureDataManager
from states.components.sema_components import WorkedLastYearStates

sema_components_router = Router()
data_manager = SecureDataManager()


callback_start = "message_chain_"
dialogue_msgs = {
    "WorkedLastYearStates": {
        "hiring_date": {
            "text": ["title", "example_text"],
        },
        "org_name": {
            "text": ["title", "example_text"],
        },
        "job_title": {
            "text": ["title", "example_text"],
        },
        "work_adress": {
            "text": ["title", "example_text"],
        },
        "is_working": {
            "text": ["title"],
            "btns": {
                "y": {"name": "btn_yes", "next_state": "end_state"},
                "n": {
                    "name": "btn_no",
                },
            },
        },
        "dismissal_date": {
            "text": ["title", "example_text"],
        },
    },
}


async def start_dialogue(message: Message, state: FSMContext, callback_data=None):
    current_state = await state.get_state()
    state_data = await state.get_data()

    sema_components_data = state_data["sema_components"]
    state_obj = sema_components_data["state_obj"]
    end_hendler = sema_components_data["end_hendler"]

    all_states = state_obj.__all_states__
    # print(all_states)
    current_index = all_states.index(current_state)

    current_state_class, current_state_name = tuple(str(current_state).split(":"))
    msgs = dialogue_msgs[current_state_class]
    # print(current_state_name)

    if msgs[current_state_name].get("btns") is not None and callback_data is None:
        return

    next_state = None
    if callback_data is not None:
        data_to_add = callback_data
        current_state_data = msgs[current_state_name]
        # print(current_state_data)
        current_state_btn_data = current_state_data["btns"][callback_data]
        next_state = current_state_btn_data.get("next_state")

        if next_state is not None:
            if next_state == "end_state":
                await state.update_data({current_state_name: data_to_add})
                await end_hendler(message, state)
                return
            next_state = (
                current_state_class + ":" + current_state_btn_data["next_state"]
            )
    else:
        data_to_add = message.text.strip()

    if next_state is None:
        next_index = current_index + 1
        if next_index < len(all_states):
            next_state = all_states[next_index]
        else:
            await state.update_data({current_state_name: data_to_add})
            await end_hendler(message, state)
            return

    await state.set_state(next_state)

    await state.update_data({current_state_name: data_to_add})
    state_data = await state.get_data()
    # print(state_data)
    lang = state_data.get("language")

    current_state = await state.get_state()
    current_state_name = str(current_state).split(":")[-1]
    path_to_text = f"worked_last_year.{current_state_name}."

    text_list = []
    for text_el in msgs[current_state_name]["text"]:
        text_list += [f"{_.get_text(f"{path_to_text}{text_el}", lang)}"]
    text = "\n".join(text_list)

    if "btns" in msgs[current_state_name].keys():
        current_state_data = msgs[current_state_name]

        btns = {
            path_to_text + btn["name"]: callback_start + callback_d
            for callback_d, btn in current_state_data["btns"].items()
        }
        await message.answer(text, reply_markup=get_callback_btns(btns, lang))
    else:
        await message.answer(text)
        return


@sema_components_router.callback_query(StateFilter(WorkedLastYearStates))
@sema_components_router.message(StateFilter(WorkedLastYearStates))
async def message_worked_last_year_state(
    event: Message | CallbackQuery, state: FSMContext, callback_data=None
):
    if isinstance(event, Message):
        await start_dialogue(event, state)
    else:
        await event.answer("")
        await start_dialogue(event.message, state, event.data.split("_")[-1])
