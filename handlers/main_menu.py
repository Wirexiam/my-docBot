from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.main_menu import Main_menu
from keyboards.main_menu import get_documents_menu_keyboard
from localization import _
from data_manager import SecureDataManager

main_menu = Router()
data_manager = SecureDataManager()


@main_menu.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки возврата в главное меню"""

    # Установка состояния для главного меню
    await state.set_state(Main_menu.main_menu)

    state_data = await state.get_data()
    lang_code = state_data.get("language")
    # Показываем главное меню с документами
    welcome_text = (
        f"{_.get_text('main_menu.welcome', lang_code)}\n\n"
        f"{_.get_text('main_menu.documents_title', lang_code)}"
    )

    await callback.message.edit_text(
        welcome_text, reply_markup=get_documents_menu_keyboard(lang_code)
    )
