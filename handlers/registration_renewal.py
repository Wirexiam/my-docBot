from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.registration_renewal import RegistrationRenewalStates
from states.components.live_adress import LiveAdress
from keyboards.registration_renewal import (
    get_registration_renewal_start_keyboard,
    get_registration_renewal_passport_start_keyboard,
    get_registration_renewal_residence_reason_keyboard,
    get_registration_renewal_after_residence_reason_and_location_keyboard,
)

from localization import _
from data_manager import SecureDataManager

registration_renewal_router = Router()
data_manager = SecureDataManager()


@registration_renewal_router.callback_query(F.data == "registration_renewal")
async def handle_registration_renewal_start(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки начала процесса продления регистрации"""

    # Установка состояния для начала процесса продления регистрации
    await state.set_state(
        RegistrationRenewalStates.waiting_confirm_registration_renewal_start
    )
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="registration_renewal_after_mvd")
    # Отправка сообщения с инструкциями
    text = f"{_.get_text('registration_renewal_start.title', lang)}\n{_.get_text('registration_renewal_start.description', lang)}\n{_.get_text('registration_renewal_start.documents_to_prepare', lang)}"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_registration_renewal_start_keyboard(lang),
    )


@registration_renewal_router.callback_query(F.data == "registration_renewal_after_mvd")
async def handle_registration_renewal_after_mvd(
    callback: CallbackQuery, state: FSMContext
):
    """Обработка нажатия кнопки после выбора МВД для продления регистрации"""
    await state.set_state(RegistrationRenewalStates.after_select_mvd)
    state_data = await state.get_data()
    lang = state_data["language"]
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")
    user_data = {
        "mvd_adress": mvd_adress,
    }
    data_manager.save_user_data(callback.from_user.id, session_id, user_data)

    await state.update_data(from_action=RegistrationRenewalStates.after_passport)
    await state.update_data(passport_title="registration_renewal_passport_title")

    text = f"{_.get_text('registration_renewal_start_passport.title', lang)}\n{_.get_text('registration_renewal_start_passport.description', lang)}"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_registration_renewal_passport_start_keyboard(lang),
    )


@registration_renewal_router.message(RegistrationRenewalStates.after_passport)
async def handle_registration_renewal_after_passport(
    message: Message, state: FSMContext
):
    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data", None)
    lang = state_data.get("language")
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: message.text.strip(),
    }
    await state.update_data({waiting_data: message.text.strip()})
    state_data = await state.get_data()
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    next_states = [LiveAdress.adress]
    from_action = RegistrationRenewalStates.after_residence_reason_and_location
    await state.update_data(
        next_states=next_states,
        from_action=from_action,
    )
    text = f"{_.get_text('registration_renewal_residence_reason.title', lang)}"
    await message.answer(
        text=text,
        reply_markup=get_registration_renewal_residence_reason_keyboard(lang),
    )


@registration_renewal_router.message(
    RegistrationRenewalStates.after_residence_reason_and_location
)
async def handle_registration_renewal_after_residence_reason_and_location(
    message: Message, state: FSMContext
):
    """Обработка сообщения после выбора причины проживания и адреса"""
    state_data = await state.get_data()
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: message.text.strip(),
    }
    await state.update_data({waiting_data: message.text.strip()})
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    state_data = await state.get_data()
    pprint(state_data)
    passport_number = state_data.get("passport_data", {}).get(
        "passport_serial_number", "Не найдено"
    )
    passport_issue_date = state_data.get("passport_data", {}).get(
        "passport_issue_date", "Не найдено"
    )
    passport_issue_place = state_data.get("passport_issue_place", "Не найдено")
    text = f"{_.get_text('registration_renewal_patient_check_data.title', lang)}\n\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.full_name', lang)}{state_data.get("passport_data",{}).get("full_name","Не найдено")}\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.birth_date', lang)}{state_data.get("passport_data",{}).get("birth_date","Не найдено")}\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.citizenship', lang)}{state_data.get("passport_data",{}).get("citizenship","Не найдено")}\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{passport_number}{_.get_text("registration_renewal_patient_check_data.issue_date")}{passport_issue_date} {passport_issue_place}\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.adress', lang)}{state_data.get("live_adress","Не найдено")}\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.residence_reason', lang)}Патент\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.patient_number', lang)}{state_data.get("patient_number","Не найдено")}\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.patient_date', lang)}{state_data.get("patient_date","Не найдено")}\n"
    text += f"{_.get_text('registration_renewal_patient_check_data.patient_issue_place', lang)}{state_data.get("patient_issue_place","Не найдено")}\n\n"

    await message.answer(
        text=text,
        reply_markup=get_registration_renewal_after_residence_reason_and_location_keyboard(
            lang
        ),
    )
