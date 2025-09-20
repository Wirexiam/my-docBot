from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _

import logging

logger = logging.getLogger(__name__)


def get_doc_child_stay_extension_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала Продление пребывания ребёнка"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("doc_child_stay_extension_start.confirm_start_button", lang),
        callback_data="select_region_and_mvd",
    )
    builder.button(
        text=_.get_text("stamp_transfer.cancel_button", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_doc_child_stay_extension_passport_start_keyboard(lang: str = "ru"):
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


def get_doc_child_accept_data(lang: str = "ru"):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_.get_text("child_stay_extension.buttons.accept", lang),
        callback_data="child_stay_accept",
    )

    builder.button(
        text=_.get_text("child_stay_extension.buttons.edit", lang),
        callback_data="child_stay_data_edit",
    )

    builder.adjust(1)
    return builder.as_markup()


def get_doc_child_stay_extension_related_child_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала Продление пребывания ребёнка для отношения"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("how_you_are_related_to_the_child.mother_btn", lang),
        callback_data=f"mother",
    )
    builder.button(
        text=_.get_text("how_you_are_related_to_the_child.father_btn", lang),
        callback_data=f"father",
    )
    builder.button(
        text=_.get_text("how_you_are_related_to_the_child.guardian_btn", lang),
        callback_data=f"guardian",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_main_editor_keyboard(lang: str = "ru"):

    builder = InlineKeyboardBuilder()
    core = "child_stay_extension"

    builder.button(
        text=_.get_text(f"{core}.mother_related", lang).rstrip(": ").strip(),
        callback_data="cs_editor_mother_related",
    )

    builder.button(
        text=_.get_text(f"{core}.basis_section", lang).rstrip(": ").strip(),
        callback_data="cs_editor_basis_section",
    ),

    builder.button(
        text=_.get_text(f"{core}.child_section", lang).rstrip(": ").strip(),
        callback_data="cs_editor_child_section",
    )

    builder.button(
        text=_.get_text(f"{core}.address_section", lang).rstrip(": ").strip(),
        callback_data="cs_editor_address_section",
    )

    builder.button(
        text=_.get_text(f"{core}.extend_section", lang).rstrip(": ").strip(),
        callback_data="cs_editor_extend_section",
    )

    builder.button(
        text=_.get_text(f"{core}.mvd_section", lang).rstrip(": ").strip(),
        callback_data="cs_editor_mvd_section",
    )

    builder.button(
        text=_.get_text("phone_number_text", lang).rstrip(": ").strip(),
        callback_data="cs_editor_phone_number_text",
    )

    builder.button(
        text=_.get_text("startarrival.cancel_button", lang),
        callback_data="cs_editor_back_to_child_stay",
    )

    builder.adjust(1)
    markup = builder.as_markup()
    logger.info(markup)
    return markup


def subkeyboard(postfix: list[str], lang: str = "ru"):

    builder = InlineKeyboardBuilder()
    core = "child_stay_extension"

    for key in postfix:
        label = _.get_text(f"{core}.{key}", lang).removesuffix(": ").strip()
        builder.button(text=label, callback_data=f"cs_sub_editor_{key}")

    builder.button(
        text=_.get_text("startarrival.cancel_button", lang),
        callback_data="cs_sub_editor_back",
    )

    builder.adjust(1)
    markup = builder.as_markup()
    return markup
