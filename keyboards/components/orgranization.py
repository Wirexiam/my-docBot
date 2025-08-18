from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _

def inn_organization(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("inn_org_migr_card_arrival.no", lang), callback_data="no_have_inn"
    )
    builder.adjust(1)
    return builder.as_markup()
        
def phone_organization(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("phone_contact_of_organization.not_have_phone", lang), callback_data="no_have_phone"
    )
    builder.adjust(1)
    return builder.as_markup()


def ur_work(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("ur_job.no_work", lang), callback_data="no_work"
    )
    builder.adjust(1)
    return builder.as_markup()

def true_or_change_final_doc(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("organisation_info_correct.true_in_organization_doc", lang), callback_data="d"
    )
    builder.button(
        text=_.get_text("organisation_info_correct.change_in_organization_doc", lang), callback_data="change_data_"
    )
    builder.adjust(1)
    return builder.as_markup()