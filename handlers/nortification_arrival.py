from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.arrival import Arrival_transfer
from states.components.passport_manual import PassportManualStates

from states.components.home_migr_data import HomeMigrData

from keyboards.nortification_arrival import *
from keyboards.migration_card import *

from localization import _
from data_manager import SecureDataManager

nortification_arrival = Router()
data_manager = SecureDataManager()

@nortification_arrival.callback_query(F.data == "doc_migration_notice")
async def arrival_start_who_agree(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки по миграционному учету"""

    # Установка состояния
    await state.set_state(Arrival_transfer.waiting_confirm_start)
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="")
    text = f"{_.get_text('who_going_to.title', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_start_arrival_who(lang),
    )

@nortification_arrival.callback_query(F.data == "to_adult")
async def arrival_start(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки для родителя"""

    # Установка состояния
    await state.set_state(Arrival_transfer.waiting_confirm_start)
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="")
    text = f"{_.get_text('startarrival.title', lang)}\n{_.get_text('startarrival.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_start_arrival(lang),
    )
    
@nortification_arrival.callback_query(Arrival_transfer.waiting_confirm_start)
async def arrival_manual_or_photo(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки начать"""

    # Установка состояния
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
    state_data = await state.get_data()
    lang = state_data["language"]

    await state.update_data(from_action=Arrival_transfer.after_passport)
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(passport_title="registration_renewal_passport_title")
    text = f"{_.get_text('stamp_transfer_passport_start.title', lang)}\n{_.get_text('stamp_transfer_passport_start.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_passport_arrival(lang),
    )
    
@nortification_arrival.message(Arrival_transfer.after_passport)
async def arrival_migr_card(message: Message, state: FSMContext):
    """Обработка cценария по миграционной карте"""

    # Установка состояния
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
    passport_data = await state.get_data()
    passport_data = passport_data.get("passport_data")
    passport_issue_place = message.text.strip()
    passport_data["passport_issue_place"] = passport_issue_place

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    # Update the state with the passport issue place
    await state.update_data(passport_data=passport_data)
    user_data = {
        "passport_data": passport_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    next_states = [HomeMigrData.adress, Arrival_transfer.after_about_home]
    await state.update_data(
        next_states=next_states
    )
    await state.update_data(passport_title="name_migr_card_arrival.title")
    text = f"{_.get_text('migr_card_arrival.title', lang)}\n{_.get_text('migr_card_arrival.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await message.answer(
        text=text,
        reply_markup=kbs_migr_arrival(lang),
    )

@nortification_arrival.message(Arrival_transfer.after_about_home)
async def arrival_migr_card(message: Message, state: FSMContext):
    """Обработка cценария по миграционной карте"""

    # Установка состояния
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
    migration_data = await state.get_data()
    migration_data = migration_data.get("migration_data")
    document_about_home = message.text.strip()
    migration_data["document_about_home"] = document_about_home

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport expiry date
    await state.update_data(migration_data=migration_data)
    user_data = {
        "migration_data": migration_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await message.answer(
        text=text,
        reply_markup=kbs_migr_arrival(lang),
    )

@nortification_arrival.callback_query(Arrival_transfer.after_about_home)
async def arrival_migr_card(call: CallbackQuery, state: FSMContext):
    """Обработка cценария по миграционной карте"""

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Отправка сообщения с клавиатурой ожидания подтверждения
    text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    await call.message.answer(
        text=text,
        reply_markup=kbs_migr_arrival(lang),
    )
