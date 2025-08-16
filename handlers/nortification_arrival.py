from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from pprint import pprint

from states.migr_card import MigrCardManualStates

from states.arrival import Arrival_transfer
from states.components.passport_manual import PassportManualStates
from keyboards.components.orgranization import true_or_change_final_doc

from utils.text_answer import text_answer

from states.components.home_migr_data import HomeMigrData
from states.components.organization import OrganizationStates

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
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
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
    
@nortification_arrival.callback_query(F.data == "to_kid")
async def arrival_start_kid(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки для родителя"""

    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(age="to_kid")
    texts = text_answer("to_kid", "arrival", "start", lang)
    text = f"{texts["title"]}\n{texts["desc"]}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_start_arrival_kids(lang),
    )

@nortification_arrival.callback_query(F.data == "to_kid_agree")
async def arrival_to_kid_agree(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки начать"""

    state_data = await state.get_data()
    # await state.update_data(from_action=Arrival_transfer.after_passport)
    state_data = await state.get_data()
    lang = state_data.get("language")
    
    
    # await state.update_data(passport_title="registration_renewal_passport_title")
    text = f"{_.get_text('to_kid_manual_select.title', lang)}\n\n{_.get_text('to_kid_manual_select.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=to_kid_kbs(lang),
    )
    print("выбор перед серт и пасп")
    
@nortification_arrival.callback_query(Arrival_transfer.waiting_confirm_start)
async def arrival_manual_or_photo(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки начать"""

    # Установка состояния
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
    state_data = await state.get_data()
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
    
@nortification_arrival.callback_query(F.data == "btn_pre_birth_certificate")
async def arrival_manual_or_photo_cert_kid(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки начать"""
    print("серт")
    # Установка состояния
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
    state_data = await state.get_data()
    await state.update_data(from_action=Arrival_transfer.after_passport)
    state_data = await state.get_data()
    lang = state_data.get("language")
    next_states = [Arrival_transfer.after_cert_kid, HomeMigrData.adress]
    await state.update_data(
        next_states=next_states,
        from_action=Arrival_transfer.after_about_home
    )
    text = f"{_.get_text('stamp_transfer_passport_start.title', lang)}\n{_.get_text('stamp_transfer_passport_start.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_cert_arrival(lang),
    )
    
@nortification_arrival.message(Arrival_transfer.after_cert_kid)
async def arrival_migr_card(message: Message, state: FSMContext):
    """Обработка cценария по миграционной карте"""

    print("После заполнения о свидетильсве о рождении")
    
    # Установка состояния
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
    place = message.text.strip()

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: place,
    }
    await state.update_data({waiting_data: place})
    state_data = await state.get_data()
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # Update the state with the passport issue place
    next_states = [HomeMigrData.adress, Arrival_transfer.after_about_home]
    await state.update_data(
        next_states=next_states,
        from_action=Arrival_transfer.after_about_home
    )
    await state.update_data(passport_title="name_migr_card_arrival.title")
    text = f"{_.get_text('migr_card_arrival.title', lang)}\n{_.get_text('migr_card_arrival.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await message.answer(
        text=text,
        reply_markup=kbs_migr_arrival(lang),
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
        next_states=next_states,
        from_action=Arrival_transfer.after_about_home
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
    await state.set_state(None)
    next_states = [Arrival_transfer.after_organisation]
    await state.update_data(
        next_states = next_states,
        from_action = Arrival_transfer.after_organisation
    )
    text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await message.answer(
        text=text,
        reply_markup=kbs_who_accept(lang),
    )

@nortification_arrival.callback_query(F.data == "nothave")
async def arrival_migr_card_about_home(call: CallbackQuery, state: FSMContext):
    """Обработка cценария по миграционной карте"""

    # Get the user's language preference from state data
    print('Смотрим проверяем после данных о доме')
    state_data = await state.get_data()
    print(state_data)
    lang = state_data.get("language")
    
    # await state.clear()
    await state.set_state(None)
    next_states = [Arrival_transfer.after_organisation]
    await state.update_data(
        next_states = next_states,
        from_action = Arrival_transfer.after_organisation
    )
    text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    await call.message.edit_text(
        text=text,
        reply_markup=kbs_who_accept(lang),
    )
    print('Смотрим проверяем после данных о доме')
    

@nortification_arrival.message(Arrival_transfer.after_organisation)
async def arrival_after_org_message(message: Message, state: FSMContext):
    
    state_data = await state.get_data()
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    job = message.text.strip()
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: "job",
    }
    await state.update_data({waiting_data: "job"})
    state_data = await state.get_data()
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    migration_data = state_data.get("migration_data")
    organization_data = state_data.get("organization_data")
    passport_data = state_data.get("passport_data")
    pprint(state_data)
    data_to_view = {
        "fio": passport_data.get("full_name", ""),
        "date_bitrh": passport_data.get("birth_date", ""),
        "citizenship": passport_data.get("citizenship", ""),
        "passport": passport_data,
        "live_adress": state_data.get("live_adress", ""),
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data,
        "doc": organization_data.get("document_about_home", "")
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += f"{_.get_text('organisation_info_correct.passport', lang)}{_.get_text('organisation_info_correct.issue_passport')}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{state_data.get('mvd_adress', "")}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["card_serial_number"]}{_.get_text('organisation_info_correct.issue_migr_card_info', lang)}{data_to_view['migr_card']["entry_date"]}\n"
    text += f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    text += f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    text += f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{data_to_view['who_accept']["phone_contact_of_organization"]}\n"
    text += f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}"

    # Отправка сообщения с клавиатурой ожидания подтверждения
    # text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    await message.answer(
        text=text,
        reply_markup=true_or_change_final_doc(lang),
    )


@nortification_arrival.callback_query(Arrival_transfer.after_organisation)
async def arrival_after_org_callback(call: CallbackQuery, state: FSMContext):
    """Обработка cценария по миграционной карте"""

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: "Нет работы",
    }
    await state.update_data({waiting_data: "Нет работы"})
    state_data = await state.get_data()
    data_manager.save_user_data(call.from_user.id, session_id, user_data)
    migration_data = state_data.get("migration_data")
    organization_data = state_data.get("organization_data")
    passport_data = state_data.get("passport_data")
    pprint(state_data)
    data_to_view = {
        "fio": passport_data.get("full_name", ""),
        "date_bitrh": passport_data.get("birth_date", ""),
        "citizenship": passport_data.get("citizenship", ""),
        "passport": passport_data,
        "live_adress": state_data.get("live_adress", ""),
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data,
        "doc": organization_data.get("document_about_home", "")
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += f"{_.get_text('organisation_info_correct.passport', lang)}{_.get_text('organisation_info_correct.issue_passport')}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{state_data.get('mvd_adress', "")}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["card_serial_number"]}{_.get_text('organisation_info_correct.issue_migr_card_info', lang)}{data_to_view['migr_card']["entry_date"]}\n"
    text += f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    text += f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    text += f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{data_to_view['who_accept']["phone_contact_of_organization"]}\n"
    text += f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}"

    # Отправка сообщения с клавиатурой ожидания подтверждения
    # text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    await call.message.edit_text(
        text=text,
        reply_markup=true_or_change_final_doc(lang),
    )