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
    
    await state.set_state(Arrival_transfer.waiting_confirm_start)
    await state.update_data(pre_passport_title="to_kid_passport_start.title")
    
    # await state.update_data(passport_title="registration_renewal_passport_title")
    text = f"{_.get_text('to_kid_manual_select.title', lang)}\n\n{_.get_text('to_kid_manual_select.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=to_kid_kbs(lang),
    )
    print("выбор перед серт и пасп")
    
@nortification_arrival.callback_query(Arrival_transfer.waiting_confirm_start, F.data == "arrival_agree")
async def arrival_manual_or_photo(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки начать"""

    # Установка состояния
    # await state.set_state(Arrival_transfer.waiting_confirm_start)
    state_data = await state.get_data()
    await state.update_data(from_action=Arrival_transfer.after_passport)
    state_data = await state.get_data()
    lang = state_data.get("language")
    age = state_data.get("age", False)
    if age:
        await state.update_data(passport_title="name_passport_kid.title")
        await state.update_data(passport_description="name_passport_kid.description")
    else:
        await state.update_data(passport_title="name_passport_kid.title")
    title = state_data.get("pre_passport_title", "stamp_transfer_passport_start.title")
    # await state.update_data(passport_title="registration_renewal_passport_title")
    text = f"{_.get_text(title, lang)}\n{_.get_text('stamp_transfer_passport_start.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_passport_arrival(lang),
    )
    
    
@nortification_arrival.callback_query(Arrival_transfer.waiting_confirm_start, F.data == "btn_pre_birth_certificate")
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
    text = f"{_.get_text('have_cert_about_kid.title', lang)}"
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
    await state.update_data(waiting_data = None)
    state_data = await state.get_data()
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # Update the state with the passport issue place
    next_states = [HomeMigrData.adress, Arrival_transfer.after_about_home]
    await state.update_data(
        next_states=next_states,
        from_action=Arrival_transfer.after_about_home
    )
    await state.update_data(migr_desc="name_migr_card_arrival_kid.description")
    await state.update_data(home_migr_title="addres_details_kid_migr_card_arrival.title")
    print("сохранил")
    print(state_data)
    text = f"{_.get_text('Kid_arrival_data.title', lang)}\n{_.get_text('migr_card_arrival.description', lang)}"
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
    age = state_data.get("age", False)
    if age:
        await state.update_data(migr_desc="name_migr_card_arrival_kid.description")
        await state.update_data(home_migr_title="addres_details_kid_migr_card_arrival.title")
        text = f"{_.get_text('Kid_arrival_data.title', lang)}\n{_.get_text('Kid_arrival_data.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await message.answer(
        text=text,
        reply_markup=kbs_migr_arrival(lang),
    )

@nortification_arrival.message(Arrival_transfer.after_about_home)
async def arrival_migr_card(message: Message, state: FSMContext):
    """Обработка cценария по миграционной карте"""

    # Установка состояния
    print("хендер сработал - после заполнения инфо о доме")
    document_about_home = message.text.strip()

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Update the state with the passport expiry date
    await state.update_data(document_about_home=document_about_home)
    user_data = {
        "document_about_home": document_about_home,
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
    age = state_data.get("age", False)
    if age:
        text = f"{_.get_text('place_by_migr_card_arrival_kid.title', lang)}"
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
    age = state_data.get("age", False)
    if age:
        text = f"{_.get_text('place_by_migr_card_arrival_kid.title', lang)}"
    await call.message.edit_text(
        text=text,
        reply_markup=kbs_who_accept(lang),
    )
    print('Смотрим проверяем после данных о доме')
    




@nortification_arrival.message(Arrival_transfer.check_data)
async def edit_f(message: Message, state: FSMContext):
    print('edit_f')

    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data", None)
    lang = state_data.get("language")
    # Сохранение адреса в менеджер данных
    print(waiting_data)
    session_id = state_data.get("session_id")
    if "." in waiting_data:
        primary_key = waiting_data.split(".")[0]
        secondary_key = waiting_data.split(".")[1]

        primary_key_data = state_data.get(primary_key)
        primary_key_data[secondary_key] = message.text.strip()

        await state.update_data({primary_key: primary_key_data})

    else:
        user_data = {
            waiting_data: message.text.strip(),
        }
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await arrival_after_org_callback(message, state)










@nortification_arrival.message(Arrival_transfer.after_organisation)
async def arrival_after_org_message(message: Message, state: FSMContext):
    print('arrival_after_org_message')
    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data", None)
    lang = state_data.get("language")
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    if "." in waiting_data:
        primary_key = waiting_data.split(".")[0]
        secondary_key = waiting_data.split(".")[1]

        primary_key_data = state_data.get(primary_key)
        primary_key_data[secondary_key] = message.text.strip()

        await state.update_data({primary_key: primary_key_data})

    else:
        user_data = {
            waiting_data: message.text.strip(),
        }
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(message.from_user.id, session_id, user_data)
    
    state_data = await state.get_data()
    await state.update_data(
        from_action=Arrival_transfer.after_organisation,
        change_data_from_check="check_arrival_after_org_message",
    )
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    job = message.text.strip()
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: job,
    }
    await state.update_data({waiting_data: job})
    state_data = await state.get_data()
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    migration_data = state_data.get("migration_data", {})
    organization_data = state_data.get("organization_data", {})
    individual_data = state_data.get("individual_data", {})
    age = state_data.get("age", False)
    who_accept = state_data.get("who_accept", "org")
    
    passport_data = state_data.get("passport_data", {})
    pprint(state_data)
    data_to_view = {
        "fio": state_data.get("child_cert_info")["full_name"] if state_data.get("child_cert_info", False) else passport_data.get("full_name", ""),
        "date_bitrh": state_data.get("child_cert_info")["birth_date"] if state_data.get("child_cert_info", False) else passport_data.get("birth_date", ""),
        "citizenship": state_data.get("child_cert_info")["child_citizenship"] if state_data.get("child_cert_info", False) else passport_data.get("citizenship", ""),
        "live_adress": state_data.get("live_adress", ""),
        "passport": passport_data,
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data if organization_data else individual_data,
        "doc": state_data.get("document_about_home", "Не указано")
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += f"{_.get_text('cert_birth_data_succes.cert_data')}{state_data.get("child_cert_info")["child_certificate_number"]}, {_.get_text('cert_birth_data_succes.issue_info')}{state_data.get("child_certificate_issue_place", '')}\n" if not state_data.get("passport_data", False) else f"{_.get_text('organisation_info_correct.passport', lang)}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['passport']['passport_issue_date']}{data_to_view['passport']['passport_issue_place']}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["card_serial_number"]}, {_.get_text('organisation_info_correct.issue_migr_card_info', lang)} {data_to_view['migr_card']["entry_date"]}\n"
    text += f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    text += '' if age else f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    text += f"{_.get_text('individual_info_correct.whoaccept', lang)}\n{_.get_text('individual_info_correct.name_of_ind', lang)}{data_to_view['who_accept']["full_name"]}\n{_.get_text('individual_info_correct.passport_of_ind', lang)}{data_to_view['who_accept']['passport_serial_number_input']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['who_accept']['passport_give_date_input']}\n{_.get_text('individual_info_correct.phone_contact_face_of_ind', lang)}{state_data.get("phone_by_individual", "Не указано")}\n{_.get_text('individual_info_correct.adress_of_ind', lang)}{data_to_view['who_accept']["adress"]}\n" if who_accept == "individual" else f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{state_data.get("phone_by_organisation", '')}\n"
    text += f"{_.get_text('info_about_representative.info_title', lang)}\n{_.get_text('info_about_representative.fio', lang)}{state_data.get("representative_data")["full_name"]}\n{_.get_text('info_about_representative.data_birthday', lang)}{state_data.get("birth_date_cert")}\n" if state_data.get("representative_data", False) else ""
    text += f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}"

    # Отправка сообщения с клавиатурой ожидания подтверждения
    # text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    await message.answer(
        text=text,
        reply_markup=true_or_change_final_doc(lang),
    )





@nortification_arrival.callback_query(F.data=='check_arrival_after_org_message')
async def arrival_after_org_message(callback: CallbackQuery, state: FSMContext):
    print('arrival_after_org_message_c')

    state_data = await state.get_data()
    await state.update_data(
        from_action=Arrival_transfer.after_organisation,
        change_data_from_check="check_arrival_after_org_message",
    )
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    job = callback.message.text.strip()
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: job,
    }
    await state.update_data({waiting_data: job})
    state_data = await state.get_data()
    data_manager.save_user_data(callback.from_user.id, session_id, user_data)
    migration_data = state_data.get("migration_data", {})
    organization_data = state_data.get("organization_data", {})
    individual_data = state_data.get("individual_data", {})
    age = state_data.get("age", False)
    who_accept = state_data.get("who_accept", "org")
    
    passport_data = state_data.get("passport_data", {})
    pprint(state_data)
    data_to_view = {
        "fio": state_data.get("child_cert_info")["full_name"] if state_data.get("child_cert_info", False) else passport_data.get("full_name", ""),
        "date_bitrh": state_data.get("child_cert_info")["birth_date"] if state_data.get("child_cert_info", False) else passport_data.get("full_name", ""),
        "citizenship": state_data.get("child_cert_info")["child_citizenship"] if state_data.get("child_cert_info", False) else passport_data.get("full_name", ""),
        "live_adress": state_data.get("live_adress", ""),
        "passport": passport_data,
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data if organization_data else individual_data,
        "doc": organization_data.get("document_about_home", "Не указано")
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += f"{_.get_text('cert_birth_data_succes.cert_data')}{state_data.get("child_cert_info")["child_certificate_number"]}, {_.get_text('cert_birth_data_succes.issue_info')}{state_data.get("child_certificate_issue_place", '')}\n" if not state_data.get("passport_data", False) else f"{_.get_text('organisation_info_correct.passport', lang)}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['passport']['passport_issue_date']}{data_to_view['passport']['passport_issue_place']}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["card_serial_number"]}, {_.get_text('organisation_info_correct.issue_migr_card_info', lang)} {data_to_view['migr_card']["entry_date"]}\n"
    text += f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    text += '' if age else f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    text += f"{_.get_text('individual_info_correct.whoaccept', lang)}\n{_.get_text('individual_info_correct.name_of_ind', lang)}{data_to_view['who_accept']["full_name"]}\n{_.get_text('individual_info_correct.passport_of_ind', lang)}{data_to_view['who_accept']['passport_serial_number_input']}, {_.get_text('organisation_info_correct.issue_info')}{data_to_view['who_accept']['passport_give_date_input']}\n{_.get_text('individual_info_correct.phone_contact_face_of_ind', lang)}{state_data.get("phone_by_individual", "Не указано")}\n{_.get_text('individual_info_correct.adress_of_ind', lang)}{data_to_view['who_accept']["adress"]}\n" if who_accept == "individual" else f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{state_data.get("phone_by_organisation", '')}\n"
    text += f"{_.get_text('info_about_representative.info_title', lang)}\n{_.get_text('info_about_representative.fio', lang)}{state_data.get("representative_data")["full_name"]}\n{_.get_text('info_about_representative.data_birthday', lang)}{state_data.get("birth_date_cert")}\n" if state_data.get("representative_data", False) else ""
    text += f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}"

    # Отправка сообщения с клавиатурой ожидания подтверждения
    # text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    await callback.message.edit_text(
        text=text,
        reply_markup=true_or_change_final_doc(lang),
    )




@nortification_arrival.callback_query(Arrival_transfer.after_organisation)
@nortification_arrival.callback_query(F.data == "check_arrival_after_org_callback")
async def arrival_after_org_callback(event: CallbackQuery, state: FSMContext):
    """Обработка cценария по миграционной карте"""
    print('arrival_after_org_callback')

    # Get the user's language preference from state data
    state_data = await state.get_data()
    await state.update_data(
        from_action=Arrival_transfer.check_data,
        change_data_from_check="check_arrival_after_org_callback",
    )
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    # Сохранение адреса в менеджер данных
    job = None
    if isinstance(event, CallbackQuery):
        job = event.data
    else:
        job = event.text
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: job,
    }
    await state.update_data({waiting_data: job})
    state_data = await state.get_data()
    data_manager.save_user_data(event.from_user.id, session_id, user_data)
    migration_data = state_data.get("migration_data", {})
    organization_data = state_data.get("organization_data", {})
    individual_data = state_data.get("individual_data", {})
    age = state_data.get("age", False)
    who_accept = state_data.get("who_accept", "org")
    
    passport_data = state_data.get("passport_data", {})
    pprint(state_data)
    data_to_view = {
        "fio": state_data.get("child_cert_info")["full_name"] if state_data.get("child_cert_info", False) else passport_data.get("full_name", ""),
        "date_bitrh": state_data.get("child_cert_info")["birth_date"] if state_data.get("child_cert_info", False) else passport_data.get("full_name", ""),
        "citizenship": state_data.get("child_cert_info")["child_citizenship"] if state_data.get("child_cert_info", False) else passport_data.get("full_name", ""),
        "live_adress": state_data.get("live_adress", ""),
        "passport": passport_data,
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data if organization_data else individual_data,
        "doc": state_data.get("document_about_home", "Не указано")
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += f"{_.get_text('cert_birth_data_succes.cert_data')}{state_data.get("child_cert_info")["child_certificate_number"]}, {_.get_text('cert_birth_data_succes.issue_info')}{state_data.get("child_certificate_issue_place", '')}\n" if not state_data.get("passport_data", False) else f"{_.get_text('organisation_info_correct.passport', lang)}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['passport']['passport_issue_date']}{data_to_view['passport']['passport_issue_place']}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["card_serial_number"]}, {_.get_text('organisation_info_correct.issue_migr_card_info', lang)} {data_to_view['migr_card']["entry_date"]}\n"
    text += f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    text += '' if age else f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    text += f"{_.get_text('individual_info_correct.whoaccept', lang)}\n{_.get_text('individual_info_correct.name_of_ind', lang)}{data_to_view['who_accept']["full_name"]}\n{_.get_text('individual_info_correct.passport_of_ind', lang)}{data_to_view['who_accept']['passport_serial_number_input']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['who_accept']['passport_give_date_input']}{data_to_view['who_accept']['passport_give_date_input']}\n{_.get_text('individual_info_correct.phone_contact_face_of_ind', lang)}{state_data.get("phone_by_individual", "Не указано")}\n{_.get_text('individual_info_correct.adress_of_ind', lang)}{data_to_view['who_accept']["adress"]}\n" if who_accept == "individual" else f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{state_data.get("phone_by_organisation", '')}\n"
    text += f"{_.get_text('info_about_representative.info_title', lang)}\n{_.get_text('info_about_representative.fio', lang)}{state_data.get("representative_data")["full_name"]}\n{_.get_text('info_about_representative.data_birthday', lang)}{state_data.get("birth_date_cert")}\n" if state_data.get("representative_data", False) else ""
    text += f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}"
    text += f"{_.get_text('organisation_info_correct.expire_period', lang)}{data_to_view['migr_card']["pretria_period"]}"

    # Отправка сообщения с клавиатурой ожидания подтверждения
    # text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    # await call.message.edit_text(
    #     text=text,
    #     reply_markup=true_or_change_final_doc(lang),
    # )


    msg_obj = {"text": text, "reply_markup": true_or_change_final_doc(lang)}

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(**msg_obj)
    else:
        await event.answer(**msg_obj)

