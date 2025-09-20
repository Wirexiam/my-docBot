from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from handlers.components.passport_manual import handle_passport_manual_start
from keyboards.components.child_data import (
    get_child_data_have_passport_keyboard,
    get_child_data_start_keyboard,
)
from states.components.passport_manual import PassportManualStates

from localization import _
from data_manager import SecureDataManager

child_data_router = Router()
data_manager = SecureDataManager()


@child_data_router.callback_query(F.data == "child_data_manual_start")
async def handle_child_data_start(callback: CallbackQuery, state: FSMContext):
    """Начинает ввод данных ребёнка, присылает выбор документа ребёнка"""
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")

    text = f"{_.get_text("doc_child_stay_extension_child_data.message_1.title", lang)}"
    await callback.message.edit_text(
        text, reply_markup=get_child_data_have_passport_keyboard(lang)
    )


@child_data_router.callback_query(F.data.startswith("child_data_passport_"))
async def handle_child_data_get(callback: CallbackQuery, state: FSMContext):
    """Начинает ввод данных ребёнка в зависимости от документа"""

    have_passport = callback.data.split("_")[-1]
    state_data = await state.get_data()

    if have_passport == "y":
        await state.update_data(
            passport_title="doc_child_stay_extension_child_data.message_2.manually.title"
        )
    else:
        await state.update_data(
            passport_title="doc_child_stay_extension_child_data.message_2.manually.title",
            skip_passport_expiry_date=True,
        )

        passport_data = state_data.get("passport_data")
        passport_data["document_type"] = "birth_certificate"

        user_data = {
            "passport_data": passport_data,
        }
        session_id = state_data.get("session_id")
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)

    await handle_passport_manual_start(callback, state)
