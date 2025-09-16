from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def kbs_migr_arrival(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("migr_card_arrival.photo_upload", lang), callback_data="ad"
    )
    builder.button(
        text=_.get_text("migr_card_arrival.photo_manual", lang),
        callback_data="migration_manual_start",
    )
    builder.adjust(1)
    return builder.as_markup()

def kbs_for_no_specified(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("time_migr_card_arrival.no_specified", lang), callback_data="no_specified"
    )
    builder.adjust(1)
    return builder.as_markup()

def kbs_for_goals(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_one", lang), callback_data="Трудовая"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_two", lang), callback_data="Служебная"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_three", lang), callback_data="Учёба"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_four", lang), callback_data="Транзит"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_five", lang), callback_data="Работа"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_six", lang), callback_data="Частная"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_seven", lang), callback_data="Семейная"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.goal_eight", lang), callback_data="Туризм"
    )
    builder.button(
        text=_.get_text("goals_migr_card_arrival.goals.other", lang), callback_data="other"
    )
    builder.adjust(1)
    return builder.as_markup()

def kbs_who_accept(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("place_by_migr_card_arrival.option_one", lang), callback_data="individual"
    )
    builder.button(
        text=_.get_text("place_by_migr_card_arrival.option_two", lang),
        callback_data="organization_accept"
    )
    builder.adjust(1)
    return builder.as_markup()