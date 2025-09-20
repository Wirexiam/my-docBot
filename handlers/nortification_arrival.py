from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from pprint import pprint

from pdf_generator.gen_pdf import create_user_doc

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

from transliterate import translit

import re

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


def parse_ru_address(addr: str) -> dict:
    """
    Возвращает словарь с безопасно извлечёнными полями адреса.
    Поддерживает неполные варианты: без корпуса, без литеры, без квартиры и т.д.
    """
    s = (addr or "").strip()
    parts = [p.strip() for p in s.split(",")]

    def get(idx, default=""):
        return parts[idx] if idx < len(parts) else default

    city_region = get(0)  # "Санкт-Петербург" или "196211 г. Санкт-Петербург"
    district_city = get(1)  # опционально: "район ..." или пусто
    street_raw = get(2)  # "улица Салова" / "ул. Смоленская" / "проспект ..."
    house_raw = get(3)  # "дом 45" / "д. 45" / "45"
    corpus_raw = get(4)  # "корп. 2" / "к. 2" / "лит. А" (иногда юзер путает)
    addon_raw = get(5)  # "лит. А" / "стр. 1" / что угодно
    flat_raw = get(6)  # "кв. 307" / "307 кв." / "офис 12"

    # street name: отбрасываем префикс типа улицы
    street_name_2 = street_raw
    m_street = re.search(
        r"(ул\.?|улица|просп\.?|проспект|шоссе|пер\.?|переулок|наб\.?|набережная|пр-д|проезд)\s+(.*)$",
        street_raw,
        re.IGNORECASE,
    )
    if m_street:
        street_name_2 = m_street.group(2).strip()

    def extract_word(text, patterns):
        """Достаёт значение после одного из ключевых слов."""
        for p in patterns:
            m = re.search(rf"{p}\s*([A-Za-zА-Яа-я0-9\-]+)", text, re.IGNORECASE)
            if m:
                return m.group(1)
        return ""

    house = extract_word(house_raw + " " + s, [r"д\.|дом"]) or house_raw.strip()
    corpus = extract_word(corpus_raw + " " + s, [r"к\.|корп\.?|корпус"])
    flat = extract_word(flat_raw + " " + s, [r"кв\.?|квартира", r"офис"])

    # на случай, когда «литера» нужна отдельным слотом — оставим в street_name_2 как есть
    return {
        "char_city_region": city_region,
        "char_district_city": district_city,
        "street_name_2": street_name_2,  # что вы кладёте в шаблон как отдельную строку
        "char_street_name": (
            street_name_2.split(" ")[0] if street_name_2 else ""
        ),  # если в шаблоне нужно одно слово
        "house_adress": house,
        "corpus": corpus,
        "room": flat,
    }


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

    # ───────────────────────── OCR алиас для старого колбэка "ad" ─────────────────────────
    @nortification_arrival.callback_query(F.data == "ad")
    async def arrival_passport_photo_alias(cb: CallbackQuery, state: FSMContext):
        """
        Back-compat: если где-то в клавиатуре остался callback_data="ad" (Фото паспорта),
        не молчим: запускаем OCR «нового паспорта» и возвращаемся в after_passport.
        """
        from handlers.components.passport_photo import (
            start_new,
        )  # локальный импорт, чтобы не плодить циклов

        await state.update_data(
            from_action=Arrival_transfer.after_passport, ocr_flow="arrival"
        )
        await start_new(cb, state)


@nortification_arrival.callback_query(
    Arrival_transfer.waiting_confirm_start, F.data == "arrival_agree"
)
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
        await state.update_data(
            passport_title="name_passport_kid.title",
            passport_description="name_passport_kid.description",
        )
    else:
        # универсальный взрослый заголовок перед вводом паспорта
        await state.update_data(passport_title="name_passport.title")
    title = state_data.get("pre_passport_title", "stamp_transfer_passport_start.title")
    # await state.update_data(passport_title="registration_renewal_passport_title")
    text = f"{_.get_text(title, lang)}\n{_.get_text('stamp_transfer_passport_start.description', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_passport_arrival(lang),
    )


@nortification_arrival.callback_query(
    Arrival_transfer.waiting_confirm_start, F.data == "btn_pre_birth_certificate"
)
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
        next_states=next_states, from_action=Arrival_transfer.after_about_home
    )
    text = f"{_.get_text('have_cert_about_kid.title', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=kbs_cert_arrival(lang),
    )


@nortification_arrival.message(Arrival_transfer.after_cert_kid)
async def arrival_after_cert_kid(message: Message, state: FSMContext):
    """После ввода сведений о свидетельстве о рождении — переходим к миграционной карте (детский сценарий)."""
    # что именно пришло — кладём в тот ключ, который ждали
    sd = await state.get_data()
    lang = sd.get("language")
    waiting_data = sd.get("waiting_data")
    session_id = sd.get("session_id")

    value = (message.text or "").strip()
    if waiting_data:
        await state.update_data({waiting_data: value})
        data_manager.save_user_data(
            message.from_user.id, session_id, {waiting_data: value}
        )
    # больше не ждём одноимённый ввод
    await state.update_data(waiting_data=None)

    # куда возвращаемся после блока «о помещении»
    next_states = [HomeMigrData.adress, Arrival_transfer.after_about_home]
    await state.update_data(
        next_states=next_states,
        from_action=Arrival_transfer.after_about_home,
        migr_desc="name_migr_card_arrival_kid.description",
        home_migr_title="addres_details_kid_migr_card_arrival.title",
    )

    text = (
        f"{_.get_text('Kid_arrival_data.title', lang)}\n"
        f"{_.get_text('migr_card_arrival.description', lang)}"
    )
    await message.answer(text=text, reply_markup=kbs_migr_arrival(lang))


@nortification_arrival.message(Arrival_transfer.after_passport)
async def arrival_migr_card(message: Message, state: FSMContext):
    """Обработка cценария по миграционной карте (после паспорта)"""

    # безопасно забираем и дополняем данные паспорта
    sd = await state.get_data()
    passport_data = dict(sd.get("passport_data") or {})
    passport_issue_place = (message.text or "").strip()
    if passport_issue_place:
        passport_data["passport_issue_place"] = passport_issue_place
    await state.update_data(passport_data=passport_data)

    lang = sd.get("language")
    session_id = sd.get("session_id")
    data_manager.save_user_data(
        message.from_user.id, session_id, {"passport_data": passport_data}
    )

    # на будущее: куда вернемся после блока «о доме»
    next_states = [HomeMigrData.adress, Arrival_transfer.after_about_home]
    await state.update_data(
        next_states=next_states, from_action=Arrival_transfer.after_about_home
    )

    # тексты/титулы
    await state.update_data(passport_title="name_migr_card_arrival.title")
    text = f"{_.get_text('migr_card_arrival.title', lang)}\n{_.get_text('migr_card_arrival.description', lang)}"

    if sd.get("age"):
        await state.update_data(
            migr_desc="name_migr_card_arrival_kid.description",
            home_migr_title="addres_details_kid_migr_card_arrival.title",
        )
        text = f"{_.get_text('Kid_arrival_data.title', lang)}\n{_.get_text('Kid_arrival_data.description', lang)}"

    await message.answer(text=text, reply_markup=kbs_migr_arrival(lang))


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
        next_states=next_states, from_action=Arrival_transfer.after_about_home
    )
    await state.update_data(passport_title="name_migr_card_arrival.title")
    text = f"{_.get_text('migr_card_arrival.title', lang)}\n{_.get_text('migr_card_arrival.description', lang)}"
    age = state_data.get("age", False)
    if age:
        await state.update_data(migr_desc="name_migr_card_arrival_kid.description")
        await state.update_data(
            home_migr_title="addres_details_kid_migr_card_arrival.title"
        )
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
        next_states=next_states, from_action=Arrival_transfer.after_organisation
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
    print("Смотрим проверяем после данных о доме")
    state_data = await state.get_data()
    print(state_data)
    lang = state_data.get("language")

    # await state.clear()
    await state.set_state(None)
    next_states = [Arrival_transfer.after_organisation]
    await state.update_data(
        next_states=next_states, from_action=Arrival_transfer.after_organisation
    )
    text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    age = state_data.get("age", False)
    if age:
        text = f"{_.get_text('place_by_migr_card_arrival_kid.title', lang)}"
    await call.message.edit_text(
        text=text,
        reply_markup=kbs_who_accept(lang),
    )
    print("Смотрим проверяем после данных о доме")


@nortification_arrival.message(Arrival_transfer.check_data)
async def edit_f(message: Message, state: FSMContext):
    print("edit_f")

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

    # else:
    #     user_data = {
    #         waiting_data: message.text.strip(),
    #     }
    #     await state.update_data({waiting_data: message.text.strip()})
    #     data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await arrival_after_org_callback(message, state)


@nortification_arrival.message(Arrival_transfer.after_organisation)
async def arrival_after_org_message(message: Message, state: FSMContext):
    print("arrival_after_org_message")
    state_data = await state.get_data()
    await state.set_state(None)
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

    state_data = await state.get_data()
    migration_data = state_data.get("migration_data", {})
    organization_data = state_data.get("organization_data", {})
    individual_data = state_data.get("individual_data", {})
    age = state_data.get("age", False)
    who_accept = state_data.get("who_accept", "org")

    passport_data = state_data.get("passport_data", {})
    pprint(state_data)
    data_to_view = {
        "fio": (
            state_data.get("child_cert_info")["full_name"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("full_name", "")
        ),
        "date_bitrh": (
            state_data.get("child_cert_info")["birth_date"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("birth_date", "")
        ),
        "citizenship": (
            state_data.get("child_cert_info")["child_citizenship"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("citizenship", "")
        ),
        "live_adress": state_data.get("live_adress", ""),
        "passport": passport_data,
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data if organization_data else individual_data,
        "doc": state_data.get("document_about_home", "Не указано"),
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += (
        f"{_.get_text('cert_birth_data_succes.cert_data')}{state_data.get("child_cert_info")["child_certificate_number"]}, {_.get_text('cert_birth_data_succes.issue_info')}{state_data.get("child_certificate_issue_place", '')}\n"
        if not state_data.get("passport_data", False)
        else f"{_.get_text('organisation_info_correct.passport', lang)}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['passport']['passport_issue_date']} {data_to_view['passport']['passport_issue_place']}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    )
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["number_migr_card_arrival"]}, {_.get_text('organisation_info_correct.issue_migr_card_info', lang)} {data_to_view['migr_card']["entry_date"]}\n"
    text += (
        f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    )
    text += (
        ""
        if age
        else f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    )
    text += (
        f"{_.get_text('individual_info_correct.whoaccept', lang)}\n"
        f"{_.get_text('individual_info_correct.name_of_ind', lang)}{data_to_view['who_accept']['full_name']}\n"
        f"{_.get_text('individual_info_correct.passport_of_ind', lang)}{data_to_view['who_accept']['passport_serial_number_input']}, "
        f"{_.get_text('organisation_info_correct.issue_info')}{data_to_view['who_accept']['passport_give_date_input']}\n"
        f"{_.get_text('individual_info_correct.phone_contact_face_of_ind', lang)}"
        f"{data_to_view['who_accept'].get('phone', state_data.get('phone_by_individual', ''))}\n"
        f"{_.get_text('individual_info_correct.adress_of_ind', lang)}{data_to_view['who_accept']['adress']}\n"
        if who_accept == "individual"
        else f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{state_data.get("phone_by_organisation", '')}\n"
    )
    text += (
        f"{_.get_text('info_about_representative.info_title', lang)}\n{_.get_text('info_about_representative.fio', lang)}{state_data.get("representative_data")["full_name"]}\n{_.get_text('info_about_representative.data_birthday', lang)}{state_data.get("birth_date_cert")}\n"
        if state_data.get("representative_data", False)
        else ""
    )
    text += (
        f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}\n"
    )
    text += f"{_.get_text('organisation_info_correct.expire_period', lang)}{data_to_view['migr_card']["pretria_period"]}"

    # Отправка сообщения с клавиатурой ожидания подтверждения
    # text = f"{_.get_text('place_by_migr_card_arrival.title', lang)}"
    await message.answer(
        text=text,
        reply_markup=true_or_change_final_doc(lang),
    )


@nortification_arrival.callback_query(F.data == "true_arrival_doc_to_ready")
async def true_arrival_doc(event: CallbackQuery, state: FSMContext):
    print("ответ")
    sd = await state.get_data()
    lang = sd.get("language")

    # 1) Безопасно распарсим адрес проживания
    addr = sd.get("live_adress", "")
    addr_parsed = parse_ru_address(addr)

    # 2) Общая заготовка
    data = {
        "char_job_name": sd.get("profession", ""),
        "char_arrive_date_day": (
            sd.get("migration_data", {}).get("entry_date", "  .  .    ").split(".")
        )[0],
        "char_arrive_date_month": (
            sd.get("migration_data", {}).get("entry_date", "  .  .    ").split(".")
        )[1],
        "char_arrive_date_year": (
            sd.get("migration_data", {}).get("entry_date", "  .  .    ").split(".")
        )[2],
        "char_exit_date_day": (
            sd.get("migration_data", {}).get("pretria_period", "  .  .    ").split(".")
        )[0],
        "char_exit_date_month": (
            sd.get("migration_data", {}).get("pretria_period", "  .  .    ").split(".")
        )[1],
        "char_exit_date_year": (
            sd.get("migration_data", {}).get("pretria_period", "  .  .    ").split(".")
        )[2],
        "char_migr_cart_series": (
            sd.get("migration_data", {}).get("number_migr_card_arrival", " ").split(" ")
        )[0],
        "char_migr_cart_numbers": (
            " ".join(
                sd.get("migration_data", {})
                .get("number_migr_card_arrival", " ")
                .split(" ")[1:]
            )
        ).strip(),
        # Адрес (теперь безопасно)
        "char_city_region": addr_parsed["char_city_region"],
        "char_district_city": addr_parsed["char_district_city"],
        "char_street_name": addr_parsed["char_street_name"],
        "house_adress": addr_parsed["house_adress"],
        "corpus": addr_parsed["corpus"],
        "room": addr_parsed["room"],
        "street_name_2": addr_parsed["street_name_2"],
        # Документ о помещении (кладём как есть)
        "char_doc_name_to_verifi_1": sd.get("document_about_home", ""),
    }

    # 3) Паспорт/свидетельство: ветвим как у вас, но без IndexError
    if sd.get("passport_data"):
        pd = sd["passport_data"]
        fio = (pd.get("full_name", "  ").split(" ")) + ["", ""]
        data.update(
            {
                "char_what_a_data": "ПАСПОРТ",
                "char_first_name": fio[0],
                "char_name": fio[1],
                "char_father_name": fio[2],
                "char_cityzenship": pd.get("citizenship", " "),
                "char_birth_date_day": (pd.get("birth_date", "  .  .    ").split("."))[
                    0
                ],
                "char_birth_date_month": (
                    pd.get("birth_date", "  .  .    ").split(".")
                )[1],
                "char_birth_date_year": (pd.get("birth_date", "  .  .    ").split("."))[
                    2
                ],
                "char_passport_numbers": pd.get("passport_serial_number", ""),
                "char_passport_issue_date_day": (
                    pd.get("passport_issue_date", "  .  .    ").split(".")
                )[0],
                "char_passport_issue_date_month": (
                    pd.get("passport_issue_date", "  .  .    ").split(".")
                )[1],
                "char_passport_issue_date_year": (
                    pd.get("passport_issue_date", "  .  .    ").split(".")
                )[2],
                "char_passport_expire_date_day": (
                    pd.get("passport_expiry_date", "  .  .    ").split(".")
                )[0],
                "char_passport_expire_date_month": (
                    pd.get("passport_expiry_date", "  .  .    ").split(".")
                )[1],
                "char_passport_expire_date_year": (
                    pd.get("passport_expiry_date", "  .  .    ").split(".")
                )[2],
            }
        )
    else:
        cd = sd.get("child_cert_info", {})
        fio = (cd.get("full_name", "  ").split(" ")) + ["", ""]
        data.update(
            {
                "char_what_a_data": "СВИДЕТЕЛЬСТВО О РОЖД",
                "char_first_name": fio[0],
                "char_name": fio[1],
                "char_father_name": fio[2],
                "char_cityzenship": cd.get("child_citizenship", " "),
                "char_birth_date_day": (cd.get("birth_date", "  .  .    ").split("."))[
                    0
                ],
                "char_birth_date_month": (
                    cd.get("birth_date", "  .  .    ").split(".")
                )[1],
                "char_birth_date_year": (cd.get("birth_date", "  .  .    ").split("."))[
                    2
                ],
                "char_passport_numbers": cd.get("child_certificate_number", ""),
            }
        )

    # 4) Данные принимающей стороны
    if sd.get("age"):
        rep = sd.get("representative_data", {}) or {}
        rfio = (rep.get("full_name", "  ").split(" ")) + ["", ""]
        data.update(
            {
                "char_parent_name": rfio[0],
                "char_parent_first_name": rfio[1],
                "char_parent_last_name": rfio[2],
            }
        )

    if sd.get("organization_data"):
        od = sd["organization_data"]
        oparts = [p.strip() for p in od.get("adress", "").split(",")]

        def oget(i):
            return oparts[i] if i < len(oparts) else ""

        oc_fio = (od.get("full_name_contact_of_organization", "  ").split(" ")) + [
            "",
            "",
        ]
        data.update(
            {
                "org": "V",
                "char_org_sity": oget(0),
                "char_hood_pos": oget(1),
                "char_hood_org": oget(2),
                "numb_house": oget(3),
                "corpus_org": oget(4),
                "kvartira_org": (oget(6) or ""),
                "reciever_street_name_2": oget(5),
                "char_reciever_father_name": oc_fio[2],
                "char_reciever_name": oc_fio[1],
                "char_reciever_first_name": oc_fio[0],
                "char_reciever_name_short_1": od.get("name_org", ""),
                "char_reciever_inn": od.get("inn", ""),
                "char_phone": (
                    sd.get("phone_by_organisation", "")[1:]
                    if sd.get("phone_by_organisation")
                    else ""
                ),
            }
        )
    else:
        ind = sd.get("individual_data", {}) or {}
        if ind:
            if " " in ind.get("full_name", ""):
                ifio = (ind.get("full_name", "  ").split(" ")) + ["", ""]
            else:
                ifio = [ind.get("full_name", ""), "", ""]
            data.update(
                {
                    "f_face": "V",
                    "char_reciever_father_name": ifio[2],
                    "char_reciever_name": ifio[1],
                    "char_reciever_first_name": ifio[0],
                    "char_reciever_passport_series": (
                        ind.get("passport_serial_number_input", "").split(" ") + [""]
                    )[0],
                    "char_reciever_passport_numbers": " ".join(
                        (ind.get("passport_serial_number_input", "").split(" "))[1:]
                    ),
                    "char_reciever_passport_issue_date_day": (
                        ind.get("passport_give_date_input", "  .  .    ").split(".")
                    )[0],
                    "char_reciever_passport_issue_date_month": (
                        ind.get("passport_give_date_input", "  .  .    ").split(".")
                    )[1],
                    "char_reciever_passport_issue_date_year": (
                        ind.get("passport_give_date_input", "  .  .    ").split(".")
                    )[2],
                    "char_reciever_passport_expire_date_day": "",
                    "char_reciever_passport_expire_date_month": "",
                    "char_reciever_passport_expire_date_year": "",
                }
            )

    # 5) Чекбоксы места и цели
    place = sd.get("migration_data", {}).get("place", "")
    goal_raw = sd.get("migration_data", {}).get("goal", "")

    # нормализуем цель: регистр/ё/синонимы
    goal = (goal_raw or "").strip().lower().replace("ё", "е")

    mapping_goal = {
        "деловая": "char_goal_business_trip",
        "учеба": "char_goal_study",
        "транзит": "char_goal_transit",
        "работа": "char_goal_work",
        "трудовая": "char_goal_work",  # ← ключевая строка
        "частная": "char_goal_private_visit",
        "туризм": "char_goal_tourism",
    }

    if place == "Жилое помещение":
        data["char_living_quarters"] = "V"
    elif place == "Иное помещение":
        data["char_other_premises"] = "V"
    elif place == "Организация":
        data["char_organizations"] = "V"

    if goal in mapping_goal:
        data[mapping_goal[goal]] = "V"

    # 6) Генерация
    print(data)
    doc = create_user_doc(
        context=data,
        template_name="notif_arrival",
        user_path="pdf_generator",
        font_name="Arial",
    )
    ready_doc = FSInputFile(
        doc, filename="Уведомление о прибытии (миграционный учёт).docx"
    )
    text = f"{_.get_text('ready_to_download_doc', lang)}\n"
    await event.message.edit_text(text=text)
    await event.message.answer_document(document=ready_doc)


@nortification_arrival.callback_query(F.data == "check_arrival_after_org_message")
async def arrival_after_org_message(callback: CallbackQuery, state: FSMContext):
    print("arrival_after_org_message_c")

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
        "fio": (
            state_data.get("child_cert_info")["full_name"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("full_name", "")
        ),
        "date_bitrh": (
            state_data.get("child_cert_info")["birth_date"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("birth_date", "")
        ),
        "citizenship": (
            state_data.get("child_cert_info")["child_citizenship"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("citizenship", "")
        ),
        "live_adress": state_data.get("live_adress", ""),
        "passport": passport_data,
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data if organization_data else individual_data,
        "doc": organization_data.get("document_about_home", "Не указано"),
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += (
        f"{_.get_text('cert_birth_data_succes.cert_data')}{state_data.get("child_cert_info")["child_certificate_number"]}, {_.get_text('cert_birth_data_succes.issue_info')}{state_data.get("child_certificate_issue_place", '')}\n"
        if not state_data.get("passport_data", False)
        else f"{_.get_text('organisation_info_correct.passport', lang)}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['passport']['passport_issue_date']} {data_to_view['passport']['passport_issue_place']}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    )
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["number_migr_card_arrival"]}, {_.get_text('organisation_info_correct.issue_migr_card_info', lang)} {data_to_view['migr_card']["entry_date"]}\n"
    text += (
        f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    )
    text += (
        ""
        if age
        else f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    )
    text += (
        f"{_.get_text('individual_info_correct.whoaccept', lang)}\n"
        f"{_.get_text('individual_info_correct.name_of_ind', lang)}{data_to_view['who_accept']['full_name']}\n"
        f"{_.get_text('individual_info_correct.passport_of_ind', lang)}{data_to_view['who_accept']['passport_serial_number_input']}"
        f"{_.get_text('organisation_info_correct.issue_info')}{data_to_view['who_accept']['passport_give_date_input']}\n"
        f"{_.get_text('individual_info_correct.phone_contact_face_of_ind', lang)}"
        f"{data_to_view['who_accept'].get('phone', state_data.get('phone_by_individual', ''))}\n"
        f"{_.get_text('individual_info_correct.adress_of_ind', lang)}{data_to_view['who_accept']['adress']}\n"
        if who_accept == "individual"
        else f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{state_data.get("phone_by_organisation", '')}\n"
    )
    text += (
        f"{_.get_text('info_about_representative.info_title', lang)}\n{_.get_text('info_about_representative.fio', lang)}{state_data.get("representative_data")["full_name"]}\n{_.get_text('info_about_representative.data_birthday', lang)}{state_data.get("birth_date_cert")}\n"
        if state_data.get("representative_data", False)
        else ""
    )
    text += (
        f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}\n"
    )
    text += f"{_.get_text('organisation_info_correct.expire_period', lang)}{data_to_view['migr_card']["pretria_period"]}"

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
    print("arrival_after_org_callback")

    # Get the user's language preference from state data
    state_data = await state.get_data()
    await state.update_data(
        from_action=Arrival_transfer.check_data,
        change_data_from_check="check_arrival_after_org_callback",
    )
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    print(waiting_data)
    if waiting_data is not None:
        if "." not in waiting_data:
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
            data_manager.save_user_data(event.from_user.id, session_id, user_data)
    state_data = await state.get_data()
    migration_data = state_data.get("migration_data", {})
    organization_data = state_data.get("organization_data", {})
    individual_data = state_data.get("individual_data", {})
    age = state_data.get("age", False)
    who_accept = state_data.get("who_accept", "org")

    passport_data = state_data.get("passport_data", {})
    pprint(state_data)
    data_to_view = {
        "fio": (
            state_data.get("child_cert_info")["full_name"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("full_name", "")
        ),
        "date_bitrh": (
            state_data.get("child_cert_info")["birth_date"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("birth_date", "")
        ),
        "citizenship": (
            state_data.get("child_cert_info")["child_citizenship"]
            if state_data.get("child_cert_info", False)
            else passport_data.get("citizenship", "")
        ),
        "live_adress": state_data.get("live_adress", ""),
        "passport": passport_data,
        "migr_card": migration_data,
        "goal": migration_data.get("goal", ""),
        "profession": state_data.get("profession", ""),
        "who_accept": organization_data if organization_data else individual_data,
        "doc": state_data.get("document_about_home", "Не указано"),
    }
    text = f"{_.get_text('organisation_info_correct.title', lang)}\n\n"
    text += f"{_.get_text('organisation_info_correct.full_name', lang)}{data_to_view['fio']}\n"
    text += f"{_.get_text('organisation_info_correct.data_birthday')}{data_to_view['date_bitrh']}\n"
    text += f"{_.get_text('organisation_info_correct.citizenship')}{data_to_view['citizenship']}\n"
    text += (
        f"{_.get_text('cert_birth_data_succes.cert_data')}{state_data.get("child_cert_info")["child_certificate_number"]}, {_.get_text('cert_birth_data_succes.issue_info')}{state_data.get("child_certificate_issue_place", '')}\n"
        if not state_data.get("passport_data", False)
        else f"{_.get_text('organisation_info_correct.passport', lang)}{data_to_view['passport']['passport_serial_number']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['passport']['passport_issue_date']} {data_to_view['passport']['passport_issue_place']}{_.get_text('organisation_info_correct.issue_date')}{data_to_view['passport']['passport_expiry_date']}\n"
    )
    text += f"{_.get_text('organisation_info_correct.adress_live_in_rf', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('organisation_info_correct.migr_card', lang)}{_.get_text('organisation_info_correct.issue_migr_card', lang)}{data_to_view['migr_card']["number_migr_card_arrival"]}, {_.get_text('organisation_info_correct.issue_migr_card_info', lang)} {data_to_view['migr_card']["entry_date"]}\n"
    text += (
        f"{_.get_text('organisation_info_correct.goal', lang)}{data_to_view["goal"]}\n"
    )
    text += (
        ""
        if age
        else f"{_.get_text('organisation_info_correct.profession', lang)}{data_to_view['profession']}\n"
    )
    text += (
        f"{_.get_text('individual_info_correct.whoaccept', lang)}\n{_.get_text('individual_info_correct.name_of_ind', lang)}{data_to_view['who_accept']["full_name"]}\n{_.get_text('individual_info_correct.passport_of_ind', lang)}{data_to_view['who_accept']['passport_serial_number_input']}{_.get_text('organisation_info_correct.issue_info')}{data_to_view['who_accept']['passport_give_date_input']}{data_to_view['who_accept']['passport_give_date_input']}\n{_.get_text('individual_info_correct.phone_contact_face_of_ind', lang)}{data_to_view['who_accept']["phone"]}\n{_.get_text('individual_info_correct.adress_of_ind', lang)}{data_to_view['who_accept']["adress"]}\n"
        if who_accept == "individual"
        else f"{_.get_text('organisation_info_correct.whoaccept', lang)}\n{_.get_text('organisation_info_correct.name_of_org', lang)}{data_to_view['who_accept']["name_org"]}\n{_.get_text('organisation_info_correct.inn_of_org', lang)}{data_to_view['who_accept']["inn"]}\n{_.get_text('organisation_info_correct.adress_of_org', lang)}{data_to_view['who_accept']["adress"]}\n{_.get_text('organisation_info_correct.fio_contact_face_of_org', lang)}{data_to_view['who_accept']["full_name_contact_of_organization"]}\n{_.get_text('organisation_info_correct.phone_contact_face_of_org', lang)}{state_data.get("phone_by_organisation", '')}\n"
    )
    text += (
        f"{_.get_text('info_about_representative.info_title', lang)}\n{_.get_text('info_about_representative.fio', lang)}{state_data.get("representative_data")["full_name"]}\n{_.get_text('info_about_representative.data_birthday', lang)}{state_data.get("birth_date_cert")}\n"
        if state_data.get("representative_data", False)
        else ""
    )
    text += (
        f"{_.get_text('organisation_info_correct.doc', lang)}{data_to_view['doc']}\n"
    )
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
