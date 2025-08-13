from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from localization import _
from data_manager import SecureDataManager

from states.work_activity import PatentedWorkActivity

from keyboards.work_activity import (
    kbs_patent_work_activity_start
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
async def handler_full_name_of_the_department(callback: CallbackQuery, state: FSMContext):
    """Запрашиваем у пользователя полное название отдела"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.set_state(PatentedWorkActivity.input_department)

    text = f"{_.get_text("work_activity_department_name.title", lang)}\n\n{_.get_text("work_activity_department_name.example_text", lang)}"

    await callback.message.edit_text(
        text=text
    )
