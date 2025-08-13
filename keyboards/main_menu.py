from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_documents_menu_keyboard(lang: str = "ru"):
    """Клавиатура меню документов"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки документов используя прямые ключи
    builder.button(
        text=_.get_text("main_menu.documents.migration_notice", lang),
        callback_data="doc_migration_notice",
    )
    builder.button(
        text=_.get_text("main_menu.documents.residence_notification", lang),
        callback_data="doc_residence_notification",
    )
    builder.button(
        text=_.get_text("main_menu.documents.work_activity", lang),
        callback_data="doc_work_activity",
    )
    builder.button(
        text=_.get_text("main_menu.documents.patent_extension", lang),
        callback_data="doc_patent_extension",
    )
    builder.button(
        text=_.get_text("main_menu.documents.family_stay_extension", lang),
        callback_data="registration_renewal",
    )
    builder.button(
        text=_.get_text("main_menu.documents.child_stay_extension", lang),
        callback_data="doc_child_stay_extension",
    )
    builder.button(
        text=_.get_text("main_menu.documents.stamp_restoration", lang),
        callback_data="doc_stamp_restoration",
    )

    # Размещаем по одной кнопке в ряд
    builder.adjust(1)
    return builder.as_markup()
