from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_doc_residence_notification_passport_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала передачи Продление пребывания ребёнка для паспорта"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "registration_renewal_start_passport.start_passport_photo", lang
        ),
        callback_data=f"passport_photo_start",
    )
    builder.button(
        text=_.get_text(
            "registration_renewal_start_passport.start_passport_manual", lang
        ),
        callback_data="passport_manual_start",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_travel_outside_Ru_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала Продление пребывания ребёнка для отношения"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("travel_outside_Ru.message_0.btn_no", lang),
        callback_data=f"travel_outside_Ru_n",
    )
    builder.button(
        text=_.get_text("travel_outside_Ru.message_0.btn_yes", lang),
        callback_data=f"travel_outside_Ru_y",
    )

    builder.adjust(1)
    return builder.as_markup()


def get_travel_outside_Ru_check_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала Продление пребывания ребёнка для отношения"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("travel_outside_Ru.message_3.btn_add", lang),
        callback_data=f"ck_travel_outside_Ru_add",
    )
    builder.button(
        text=_.get_text("travel_outside_Ru.message_3.btn_yes", lang),
        callback_data=f"ck_travel_outside_Ru_y",
    )
    builder.button(
        text=_.get_text("travel_outside_Ru.message_3.btn_edit", lang),
        callback_data=f"ck_travel_outside_Ru_edit",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_check_data_before_gen(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("stamp_check_datas_info.all_true_in_stamp_button", lang),
        callback_data="all_true_in_doc_residence_notification",
    )
    builder.button(
        text=_.get_text("stamp_check_datas_info.change_data_stamp_button", lang),
        callback_data="change_data_",
    )
    builder.adjust(1)
    return builder.as_markup()
