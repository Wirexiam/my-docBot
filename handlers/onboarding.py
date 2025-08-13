from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.onboarding import OnboardingStates
from keyboards.onboarding import (
    get_consent_keyboard,
    get_refusal_keyboard,
    get_language_keyboard,
)
from keyboards.main_menu import get_documents_menu_keyboard
from localization import _
from data_manager import SecureDataManager

onboarding_router = Router()
data_manager = SecureDataManager()


@onboarding_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Начальная команда - показываем согласие"""
    await state.clear()
    await state.set_state(OnboardingStates.waiting_consent)

    consent_text = (
        f"{_.get_text('consent.title')}\n\n" f"{_.get_text('consent.description')}"
    )

    await message.answer(consent_text, reply_markup=get_consent_keyboard())


@onboarding_router.callback_query(F.data == "consent_agree")
async def consent_agreed(callback: CallbackQuery, state: FSMContext):
    """Пользователь согласился на обработку данных"""
    await state.set_state(OnboardingStates.waiting_language)

    language_text = f"{_.get_text('language.title')}\n" f"{_.get_text('language.note')}"

    await callback.message.edit_text(
        language_text, reply_markup=get_language_keyboard()
    )


@onboarding_router.callback_query(F.data == "consent_refuse")
async def consent_refused(callback: CallbackQuery, state: FSMContext):
    """Пользователь отказался от обработки данных"""
    await state.clear()

    refusal_text = (
        f"{_.get_text('refusal.title')}\n" f"{_.get_text('refusal.description')}"
    )

    await callback.message.edit_text(refusal_text, reply_markup=get_refusal_keyboard())


@onboarding_router.callback_query(F.data == "back_to_consent")
async def back_to_consent(callback: CallbackQuery, state: FSMContext):
    """Возврат к согласию"""
    await state.set_state(OnboardingStates.waiting_consent)

    consent_text = (
        f"{_.get_text('consent.title')}\n\n" f"{_.get_text('consent.description')}"
    )

    await callback.message.edit_text(consent_text, reply_markup=get_consent_keyboard())


@onboarding_router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery, state: FSMContext):
    """Выбран язык - показываем главное меню"""
    lang_code = callback.data.split("_")[1]

    # Сохраняем выбранный язык в состоянии
    await state.update_data(language=lang_code)
    await state.set_state(OnboardingStates.completed)

    # Создаем сессию пользователя
    session_id = data_manager.create_user_session(callback.from_user.id)
    await state.update_data(session_id=session_id)

    # Сохраняем язык в данные пользователя
    user_data = {"language": lang_code}
    data_manager.save_user_data(callback.from_user.id, session_id, user_data)

    # Показываем главное меню с документами
    welcome_text = (
        f"{_.get_text('main_menu.welcome', lang_code)}\n\n"
        f"{_.get_text('main_menu.documents_title', lang_code)}"
    )

    await callback.message.edit_text(
        welcome_text, reply_markup=get_documents_menu_keyboard(lang_code)
    )
