from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def kbs_patent_work_activity_start(lang: str = "ru"):
    """Стартовая клавиатура уведомления по труд. деят."""

    builder = InlineKeyboardBuilder()

    builder.button(
        text=_.get_text("work_activity_start.buttons.start_button", lang),
        callback_data="start_work_act"
    )

    builder.button(
        text=_.get_text("work_activity_start.buttons.cancel_button", lang),
        callback_data="main_menu"
    )

    builder.adjust(1)
    return builder.as_markup()


def kbs_wa_validation_department_name(lang: str = "ru"):
    """Подтвеждение корректого названия отдела"""

    builder = InlineKeyboardBuilder()

    builder.button(
        text=_.get_text("work_activity_department_user_input.buttons.correct_btn", lang),
        callback_data="correct_department_name"
    )

    builder.button(
        text=_.get_text("work_activity_department_user_input.buttons.cancel_button", lang),
        callback_data="start_work_act"
    )

    builder.adjust(1)
    return builder.as_markup()


def kbs_wa_passport_entry(lang: str = "ru"):
    """Запрашиваем данные паспорта"""

    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("work_activity_passport_req.buttons.passport_photo", lang),
        callback_data="passport_photo_start"
    )

    builder.button(
        text=_.get_text("work_activity_passport_req.buttons.photo_manual", lang),
        callback_data="passport_manual_start"
    )

    builder.adjust(1)
    return builder.as_markup()


def kbs_policy_data_confirmation(lang: str = "ru"):
    """Клавиатура подтверждения данных полиса"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_.get_text("wa_patent.wa_police_prof.buttons.accept", lang),
        callback_data="accept_police_data"
    )

    builder.button(
        text=_.get_text("wa_patent.wa_police_prof.buttons.edit", lang),
        callback_data="edit_police_data"
    )

    builder.adjust(1)
    return builder.as_markup()