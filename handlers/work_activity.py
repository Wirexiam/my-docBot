from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from localization import _
from data_manager import SecureDataManager

from states.work_activity import PatentedWorkActivity

from keyboards.work_activity import (
    kbs_patent_work_activity_start, kbs_wa_validation_department_name, kbs_wa_passport_entry
)


work_activity_router = Router()
data_manager = SecureDataManager()


@work_activity_router.callback_query(F.data == "doc_work_activity")
async def wa_start(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки о трудовой деятельности по патенту"""

    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(PatentedWorkActivity.work_activity_start)

    text = f"{_.get_text("work_activity_start.title", lang)}\n{_.get_text("work_activity_start.description")}\n{_.get_text("work_activity_start.documents_to_prepare")}"

    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_patent_work_activity_start(lang)
    )


@work_activity_router.callback_query(F.data == "start_work_act")
async def full_name_of_the_department(callback: CallbackQuery, state: FSMContext):
    """Запрашиваем у пользователя полное название отдела"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.set_state(PatentedWorkActivity.input_department)

    text = f"{_.get_text("work_activity_department_name.title", lang)}\n\n{_.get_text("work_activity_department_name.example_text", lang)}"

    await callback.message.edit_text(
        text=text
    )


@work_activity_router.message(PatentedWorkActivity.input_department)
async def handler_full_name_of_the_department(message: Message, state: FSMContext):
    """Получаеем ответ полного названия отдела"""

    msg = message.text

    state_data = await state.get_data()
    lang = state_data.get("language")

    session_id = state_data.get("session_id")

    # await state.set_state(PatentedWorkActivity.passport_check)
    user_data = {
        "department_full_name": msg,
    }

    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text("work_activity_department_user_input.title", lang)}\n\n{_.get_text("work_activity_department_user_input.title_dep", lang)} {msg}\n\n{_.get_text("work_activity_department_user_input.description", lang)}"

    await message.answer(
        text=text,
        reply_markup=kbs_wa_validation_department_name(lang)
    )


@work_activity_router.callback_query(F.data == "correct_department_name")
async def handler_passport_check(callback: CallbackQuery, state: FSMContext):
    """Получаем положительный ответ от пользователя и запращиваем данные паспорта"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    text = f"{_.get_text("work_activity_passport_req.title", lang)}\n\n{_.get_text("work_activity_passport_req.description", lang)}"

    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_wa_passport_entry(lang)
    )