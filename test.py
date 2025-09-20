from pdf_generator.gen_pdf import create_user_doc

state_data = {
    "change_data_from_check": "check_arrival_after_org_message",
    "docaboutegrn": "Выписка из ЕГРН",
    "document_about_home": "Выписка из ЕГРН от 08.2023",
    "fill_goal": True,
    "language": "ru",
    "live_adress": "Санкт-Петербург, Фрунзенский район, улица Белградская, дом "
    "6,  корпус 2, литера а, квартира 59",
    "migration_data": {
        "entry_date": "14.08.1996",
        "goal": "Семейная",
        "number_migr_card_arrival": "78 0254812",
        "place": "Жилое помещение",
        "pretria_period": "10.08.2025",
    },
    "organization_data": {
        "adress": "Санкт-Петербург, Фрунзенский район, улица "
        "Белградская, дом 6,  корпус 2, литера а, "
        "квартира 59",
        "full_name_contact_of_organization": "Антропов Олег " "Юрьевич",
        "inn": "7811298765",
        "name_org": "ООО ФОРМАТ",
    },
    "passport_data": {
        "birth_date": "14.08.1996",
        "citizenship": "Узбекистан",
        "full_name": "Абдуллаев Жахонгир Нодирович",
        "passport_expiry_date": "14.08.1996",
        "passport_issue_date": "14.08.1996",
        "passport_issue_place": "МВД Узбекистана",
        "passport_serial_number": "FA 123456",
    },
    "passport_title": "name_migr_card_arrival.title",
    "phone_by_organisation": "79809008090",
    "place": "Жилое помещение",
    "profession": "разнорабочий",
    "session_id": "6910d119-8a66-4943-b84f-367ee6a1225f",
    "waiting_data": "profession",
    "who_accept": "org",
}

data = {
    "char_first_name": state_data.get("passport_data", "")
    .get("full_name", " ")
    .split(" ")[0],
    "char_name": state_data.get("passport_data", "")
    .get("full_name", " ")
    .split(" ")[1],
    "char_father_name": state_data.get("passport_data", "")
    .get("full_name", " ")
    .split(" ")[2],
    "char_cityzenship": state_data.get("passport_data", "").get("citizenship", " "),
    "char_birth_date_day": state_data.get("passport_data", "")
    .get("birth_date", " ")
    .split(".")[0],
    "char_birth_date_month": state_data.get("passport_data", "")
    .get("birth_date", " ")
    .split(".")[1],
    "char_birth_date_year": state_data.get("passport_data", "")
    .get("birth_date", " ")
    .split(".")[2],
    "char_birth_place": "",
    "char_passport_series": state_data.get("passport_data", "")
    .get("passport_serial_number", " ")
    .split(" ")[0],
    "char_passport_numbers": state_data.get("passport_data", "")
    .get("passport_serial_number", "")
    .split(" ")[1],
    "char_passport_issue_date_day": state_data.get("passport_data", "")
    .get("passport_issue_date", "")
    .split(".")[0],
    "char_passport_issue_date_month": state_data.get("passport_data", "")
    .get("passport_issue_date", "")
    .split(".")[1],
    "char_passport_issue_date_year": state_data.get("passport_data", "")
    .get("passport_issue_date", "")
    .split(".")[2],
    "char_passport_expire_date_day": state_data.get("passport_data", "")
    .get("passport_expiry_date", "")
    .split(".")[0],
    "char_passport_expire_date_month": state_data.get("passport_data", "")
    .get("passport_expiry_date", "")
    .split(".")[1],
    "char_passport_expire_date_year": state_data.get("passport_data", "")
    .get("passport_expiry_date", "")
    .split(".")[2],
    "char_job_name": state_data.get("profession", ""),
    "char_arrive_date_day": state_data.get("migration_data", "")
    .get("entry_date", " ")
    .split(".")[0],
    "char_arrive_date_month": state_data.get("migration_data", "")
    .get("entry_date", " ")
    .split(".")[1],
    "char_arrive_date_year": state_data.get("migration_data", "")
    .get("entry_date", " ")
    .split(".")[2],
    "char_exit_date_day": state_data.get("migration_data", "")
    .get("pretria_period", " ")
    .split(".")[0],
    "char_exit_date_month": state_data.get("migration_data", "")
    .get("pretria_period", " ")
    .split(".")[1],
    "char_exit_date_year": state_data.get("migration_data", "")
    .get("pretria_period", " ")
    .split(".")[2],
    "char_migr_cart_series": state_data.get("migration_data", "")
    .get("number_migr_card_arrival", " ")
    .split(" ")[0],
    "char_migr_cart_numbers": state_data.get("migration_data", "")
    .get("number_migr_card_arrival", " ")
    .split(" ")[1],
    "char_city_region": state_data.get("live_adress", "").split(",")[0],
    "char_district_city": state_data.get("live_adress", "").split(",")[1],
    "char_street_name": state_data.get("live_adress", "").split(",")[2].split(" ")[1],
    "house_adress": state_data.get("live_adress", "").split(",")[3].split(" ")[-1],
    "corpus": state_data.get("live_adress", "").split(",")[4].split(" ")[-1],
    "room": state_data.get("live_adress", "").split(",")[6].split(" ")[-1],
    "street_name_2": state_data.get("live_adress", "").split(",")[5],
    "char_doc_name_to_verifi_1": f"Паспорт гражданина {state_data.get('passport_data', '').get('citizenship', ' ')}a",
    "char_doc_name_to_verifi_2": "Миграционная карта",
    "char_doc_name_to_verifi_3": state_data.get("docaboutegrn", ""),
    "char_doc_name_to_verifi_4": "Трудовой договор",
    "char_doc_name_to_verifi_5": "Регистрация по месту пребывания",
}

if state_data.get("organization_data"):
    data["char_reciever_city_region"] = (
        state_data.get("organization_data", "").get("adress", "").split(",")[0],
    )
    data["char_reciever_district_city"] = (
        state_data.get("organization_data", "").get("adress", "").split(",")[1],
    )
    data["char_reciever_street_name"] = (
        state_data.get("organization_data", "")
        .get("adress", "")
        .split(",")[2]
        .split(" ")[1],
    )
    data["reciever_house_adress"] = (
        state_data.get("organization_data", "")
        .get("adress", "")
        .split(",")[3]
        .split(" ")[-1],
    )
    data["reciever_corpus"] = (
        state_data.get("organization_data", "")
        .get("adress", "")
        .split(",")[4]
        .split(" ")[-1],
    )
    data["reciever_room"] = (
        state_data.get("organization_data", "")
        .get("adress", "")
        .split(",")[6]
        .split(" ")[-1],
    )
    data["reciever_street_name_2"] = (
        state_data.get("organization_data", "").get("adress", "").split(",")[5],
    )
    data["char_reciever_father_name"] = (
        state_data.get("organization_data", "")
        .get("full_name_contact_of_organization", "")
        .split(" ")[2],
    )
    data["char_reciever_name"] = (
        state_data.get("organization_data")
        .get("full_name_contact_of_organization", "")
        .split(" ")[0],
    )
    data["char_reciever_first_name"] = (
        state_data.get("organization_data")
        .get("full_name_contact_of_organization", "")
        .split(" ")[1],
    )
    data["char_reciever_name_short_1"] = (
        state_data.get("organization_data").get("name_org", "").split(" ")[0]
    )
    data["char_reciever_name_short_2"] = (
        state_data.get("organization_data").get("name_org", "").split(" ")[1]
    )
    data["char_reciever_inn"] = state_data.get("organization_data").get("inn", "")
    data["adress"] = state_data.get("organization_data").get("adress", "")
    data["char_phone"] = state_data.get("phone_by_organisation", "")
else:
    data["char_reciever_father_name"] = (
        state_data.get("individual_data", "").get("full_name", "").split(" ")[2],
    )
    data["char_reciever_name"] = (
        state_data.get("individual_data", "").get("full_name", "").split(" ")[1],
    )
    data["char_reciever_first_name"] = (
        state_data.get("individual_data", "").get("full_name", "").split(" ")[0],
    )
    data["char_reciever_passport_series"] = (
        state_data.get("individual_data", "")
        .get("passport_serial_number_input", "")
        .split(" ")[0],
    )
    data["char_reciever_passport_numbers"] = (
        state_data.get("individual_data", "")
        .get("passport_serial_number_input", "")
        .split(" ")[1],
    )
    data["char_reciever_passport_issue_date_day"] = (
        state_data.get("individual_data", "")
        .get("passport_give_date_input", "")
        .split(".")[0],
    )
    data["char_reciever_passport_issue_date_month"] = (
        state_data.get("individual_data", "")
        .get("passport_give_date_input", "")
        .split(".")[1],
    )
    data["char_reciever_passport_issue_date_year"] = (
        state_data.get("individual_data", "")
        .get("passport_give_date_input", "")
        .split(".")[2],
    )
    data["char_reciever_passport_expire_date_day"] = ("",)
    data["char_reciever_passport_expire_date_month"] = ("",)
    data["char_reciever_passport_expire_date_year"] = ("",)

if state_data.get("migration_data").get("place", "") == "Жилое помещение":
    data["char_living_quarters"] = "V"
elif state_data.get("migration_data").get("place", "") == "Иное помещение":
    data["char_other_premises"] = "V"
elif state_data.get("migration_data").get("place", "") == "Организация":
    data["char_organizations"] = "V"


if state_data.get("migration_data").get("goal", "") == "Деловая":
    data["char_goal_business_trip"] = "V"
elif state_data.get("migration_data").get("goal", "") == "Учёба":
    data["char_goal_study"] = "V"
elif state_data.get("migration_data").get("goal", "") == "Транзит":
    data["char_goal_transit"] = "V"
elif state_data.get("migration_data").get("goal", "") == "Работа":
    data["char_goal_work"] = "V"
elif state_data.get("migration_data").get("goal", "") == "Частная":
    data["char_goal_private_visit"] = "V"
elif state_data.get("migration_data").get("goal", "") == "Туризм":
    data["char_goal_tourism"] = "V"


doc = create_user_doc(
    context=data,
    template_name="notif_arrival",
    user_path="pdf_generator",
    font_name="Arial",
)
