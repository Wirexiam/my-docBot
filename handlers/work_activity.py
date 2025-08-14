from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from localization import _
from data_manager import SecureDataManager
from handlers.components.passport_manual import handle_passport_manual_start

from states.work_activity import PatentedWorkActivity

from keyboards.work_activity import (
    kbs_patent_work_activity_start, kbs_wa_validation_department_name, kbs_wa_passport_entry,
    kbs_panetn_entry_start
)
from keyboards.components.residence_reason_patent import get_residence_reason_photo_or_manual_keyboard


work_activity_router = Router()
data_manager = SecureDataManager()


@work_activity_router.callback_query(F.data == "doc_work_activity")
async def wa_start(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки о трудовой деятельности по патенту"""

    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(PatentedWorkActivity.work_activity_start)

    text = f"{_.get_text("work_activity_start.title", lang)}\n{_.get_text("work_activity_start.description", lang)}\n{_.get_text("work_activity_start.documents_to_prepare", lang)}"

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

    await state.update_data(from_action=PatentedWorkActivity.passport_data,
                         passport_title="wa_passport_title")

    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_wa_passport_entry(lang)
    )

    # await handle_passport_manual_start(callback, state)


@work_activity_router.message(PatentedWorkActivity.passport_data)
async def handle_passport_data(message: Message, state: FSMContext):
    """Получаем данные ввода паспорта"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    session_id = state_data.get("session_id")

    passport_data = state_data.get("passport_data")
    if passport_data:
        user_data = {
            "passport_user_data": passport_data
        }
        data_manager.save_user_data(message.from_user.id, session_id, user_data)

        await state.update_data(from_action=(PatentedWorkActivity.patent_entry))
    
    text = f"{_.get_text("wa_patent.wa_patent_start.title", lang)}\n{_.get_text("wa_patent.wa_patent_start.description", lang)}"

    await message.answer(
        text=text,
        reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )