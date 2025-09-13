from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import re

from states.components.phone_number import PhoneNumberStates
from states.stamp_transfer import Stamp_transfer
from keyboards.stamp_transfer import get_stamp_transfer_check_data_before_gen
from localization import _
from data_manager import SecureDataManager

phone_number_router = Router()
data_manager = SecureDataManager()

PHONE_RE = re.compile(r"^79\d{9}$")  # простой валидатор номера

@phone_number_router.message(PhoneNumberStates.phone_number_input, F.text)
async def handle_phone_number_input(message: Message, state: FSMContext):
    """Принимаем телефон, сохраняем, показываем сводку перед генерацией."""
    state_data = await state.get_data()
    lang       = state_data.get("language", "ru")
    session_id = state_data.get("session_id")

    phone = (message.text or "").strip()

    # валидация
    if not PHONE_RE.match(phone):
        prompt = _.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📞 Введите номер телефона в формате 79XXXXXXXXX."
        await message.answer("Некорректный номер. " + prompt)
        return

    # сохраняем телефон
    await state.update_data(phone_number=phone)
    data_manager.save_user_data(message.from_user.id, session_id, {"phone_number": phone})

    # готовим сводку
    data   = await state.get_data()
    new_pd = data.get("passport_data") or {}
    old_pd = data.get("old_passport_data") or {}

    view = {
        "name": new_pd.get("full_name", "Не найден"),
        "new_passport_number": new_pd.get("passport_serial_number", "Не найден"),
        "old_passport_number": old_pd.get("passport_serial_number", "Не найден"),
        "new_passport_issue_place": new_pd.get("passport_issue_place", "Не найден"),
        "old_passport_issue_place": old_pd.get("passport_issue_place", "Не найден"),
        "new_passport_issue_date": new_pd.get("passport_issue_date", "Не найден"),
        "old_passport_issue_date": old_pd.get("passport_issue_date", "Не найден"),
        "new_passport_expiry_date": new_pd.get("passport_expiry_date", "Не найден"),
        "old_passport_expiry_date": old_pd.get("passport_expiry_date", "Не найден"),
        "live_adress": data.get("live_adress", "Не найден"),
        "phone_number": data.get("phone_number", "Не найден"),
        "mvd_adress": data.get("mvd_adress", "Не найден"),
    }

    text  = f"{_.get_text('stamp_check_datas_info.title', lang)}\n\n"
    text += f"{_.get_text('stamp_check_datas_info.full_name', lang)}{view['name']}\n"
    text += f"{_.get_text('stamp_check_datas_info.new_passport', lang)}{view['new_passport_number']}{_.get_text('stamp_check_datas_info.issue_date', lang)}{view['new_passport_issue_date']} {view['new_passport_issue_place']}{_.get_text('stamp_check_datas_info.expiry_date', lang)}{view['new_passport_expiry_date']}\n"
    text += f"{_.get_text('stamp_check_datas_info.old_passport', lang)}{view['old_passport_number']}{_.get_text('stamp_check_datas_info.issue_date', lang)}{view['old_passport_issue_date']} {view['old_passport_issue_place']}{_.get_text('stamp_check_datas_info.expiry_date', lang)}{view['old_passport_expiry_date']}\n"
    text += f"{_.get_text('stamp_check_datas_info.stamp_in', lang)}\n"
    text += f"{_.get_text('stamp_check_datas_info.adress', lang)}{view['live_adress']}\n"
    text += f"{_.get_text('stamp_check_datas_info.phone', lang)}{view['phone_number']}\n"
    text += f"{_.get_text('stamp_check_datas_info.mvd_adress', lang)}{view['mvd_adress']}"

    # сюда вернётся сценарий, если выберут «изменить» в сводке
    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        change_data_from_check="stamp_transfer_after_new_passport",
    )

    # показываем сводку + клавиатуру подтверждения
    await message.answer(text=text, reply_markup=get_stamp_transfer_check_data_before_gen(lang))
