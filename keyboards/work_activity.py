from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def kbs_patent_work_activity_start(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("work_activity_start.buttons.start_button", lang),
        callback_data="start_work_act",
    )
    builder.button(
        text=_.get_text("work_activity_start.buttons.cancel_button", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()


def kbs_wa_validation_department_name(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "work_activity_department_user_input.buttons.correct_btn", lang
        ),
        callback_data="correct_department_name",
    )
    builder.button(
        text=_.get_text(
            "work_activity_department_user_input.buttons.cancel_button", lang
        ),
        callback_data="start_work_act",
    )
    builder.adjust(1)
    return builder.as_markup()


def kbs_wa_passport_entry(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("work_activity_passport_req.buttons.passport_photo", lang),
        callback_data="wa_passport_photo_start",
    )
    builder.button(
        text=_.get_text("work_activity_passport_req.buttons.photo_manual", lang),
        callback_data="wa_passport_manual_start",
    )
    builder.adjust(1)
    return builder.as_markup()


def kbs_policy_data_confirmation(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.buttons.accept", lang),
        callback_data="accept_wa_patent_data",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.buttons.edit", lang),
        callback_data="edit_wa_patent_data",
    )
    builder.adjust(1)
    return builder.as_markup()


def kbs_edit_wa_data(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.full_name", lang),
        callback_data="edit_passport_full_name",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.passport", lang),
        callback_data="wa_edit_passport",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.patent", lang),
        callback_data="wa_edit_patent",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.work_adress", lang),
        callback_data="wa_edit_work_adress",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.profession", lang),
        callback_data="wa_edit_profession",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.inn", lang), callback_data="wa_edit_inn"
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.policy", lang),
        callback_data="wa_edit_policy",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.phone_number", lang),
        callback_data="wa_edit_phone_number",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.buttons.back_button", lang),
        callback_data="wa_edit_back_to_data",
    )
    builder.adjust(1)
    return builder.as_markup()


def kbs_sub_editor_policy(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.policy.buttons.policy_number",
            lang,
        ),
        callback_data="edit_policy_number",
    )
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.policy.buttons.company", lang
        ),
        callback_data="edit_policy_company",
    )
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.policy.buttons.dateof", lang
        ),
        callback_data="edit_policy_dateof",
    )
    builder.button(
        text=_.get_text("wa_patent.edit_wa_data.buttons.back_button", lang),
        callback_data="edit_wa_patent_data",
    )
    builder.adjust(1)
    return builder.as_markup()


def kbs_sub_editor_passport(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.passport.buttons.serial_number",
            lang,
        ),
        callback_data="edit_passport_passport_serial_number",
    )
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.passport.buttons.date_issue", lang
        ),
        callback_data="edit_passport_passport_issue_date",
    )
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.passport.buttons.issued_by", lang
        ),
        callback_data="edit_passport_passport_issued",
    )
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.passport.buttons.validity_period",
            lang,
        ),
        callback_data="edit_passport_passport_expiry_date",
    )
    builder.adjust(1)
    return builder.as_markup()


def kbs_sub_editor_patient(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.patent.buttons.serial_number",
            lang,
        ),
        callback_data="edit_patent_patient_number",
    )
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.patent.buttons.date_issue", lang
        ),
        callback_data="edit_patent_patient_date",
    )
    builder.button(
        text=_.get_text(
            "wa_patent.wa_data_editor.sub_editor_data.patent.buttons.issued_by", lang
        ),
        callback_data="edit_patent_patient_issue_place",
    )
    builder.adjust(1)
    return builder.as_markup()
