from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
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
    passport_data = state_data.get("passport_data")
    passport_data[waiting_data] = message.text.strip()

    await state.update_data(passport_data=passport_data)
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


@registration_renewal_router.callback_query(
    F.data.startswith("residence_reason_child_")
)
async def handle_residence_reason_child(callback: CallbackQuery, state: FSMContext):
    who_for_child = callback.data.split("child_")[1]
    print(f"Selected who for child: {who_for_child}")
    state_data = await state.get_data()

    lang = state_data.get("language")
    child_data = state_data.get("child_data", {})
    child_data["who_for_child"] = who_for_child

    await state.update_data(child_data=child_data)
    state_data = await state.get_data()
    photo = FSInputFile("static/live_adress_example.png")
    # Отправка подтверждения пользователю

    text = f"{_.get_text('live_adress.title', lang)}\n{_.get_text('live_adress.example', lang)}"

    await callback.message.answer_photo(caption=text, photo=photo)
    await state.update_data(waiting_data="live_adress")
    next_states = state_data.get("next_states", [])
    from_action = state_data.get("from_action")
    if len(next_states) == 1:
        await state.set_state(from_action)
    elif len(next_states) > 0:
        next_state = next_states[1:][0]
        await state.update_data(next_states=next_states[1:])
        await state.set_state(next_state)
    else:
        # If no next states, return to the previous action
        await state.set_state(from_action)


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
    if "." in waiting_data:
        primary_key = waiting_data.split(".")[0]
        secondary_key = waiting_data.split(".")[1]

        primary_key_data = state_data.get(primary_key)
        primary_key_data[secondary_key] = message.text.strip()

        await state.update_data({primary_key: primary_key_data})

    else:
        user_data = {
            waiting_data: message.text.strip(),
        }
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(message.from_user.id, session_id, user_data)
    state_data = await state.get_data()
    pprint(state_data)
    await state.update_data(
        from_action=RegistrationRenewalStates.after_residence_reason_and_location,
        change_data_from_check="registrationrenewalstates_after_residence_reason_and_location",
    )
    passport_number = state_data.get("passport_data", {}).get(
        "passport_serial_number", "Не найдено"
    )
    passport_issue_date = state_data.get("passport_data", {}).get(
        "passport_issue_date", "Не найдено"
    )
    passport_issue_place = state_data.get("passport_data", {}).get(
        "passport_issue_place", "Не найдено"
    )
    passport_expiry_date = state_data.get("passport_data", {}).get(
        "passport_expiry_date", "Не найдено"
    )

    residence_reason = state_data.get("residence_reason", "Не найдено")
    if residence_reason == "residence_reason_patent":
        text = (
            f"{_.get_text('registration_renewal_patient_check_data.title', lang)}\n\n"
        )
        patient_data = state_data.get("patient_data", {})
        text += f"{_.get_text('registration_renewal_patient_check_data.full_name', lang)}{state_data.get("passport_data",{}).get("full_name","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.birth_date', lang)}{state_data.get("passport_data",{}).get("birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.citizenship', lang)}{state_data.get("passport_data",{}).get("citizenship","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{passport_number}{_.get_text("registration_renewal_patient_check_data.issue_date")}{passport_issue_date} {passport_issue_place}{_.get_text("registration_renewal_patient_check_data.expiry_date")}{passport_expiry_date}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.adress', lang)}{state_data.get("live_adress","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.residence_reason', lang)}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.patient_number', lang)}{patient_data.get("patient_number","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.patient_date', lang)}{patient_data.get("patient_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.patient_issue_place', lang)}{patient_data.get("patient_issue_place","Не найдено")}\n\n"
    elif residence_reason == "residence_reason_marriage":
        text = (
            f"{_.get_text('registration_renewal_marriage_check_data.title', lang)}\n\n"
        )
        marriage_data = state_data.get("marriage_data", {})
        text += f"{_.get_text('registration_renewal_marriage_check_data.full_name', lang)}{state_data.get("passport_data",{}).get("full_name","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.birth_date', lang)}{state_data.get("passport_data",{}).get("birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.citizenship', lang)}{state_data.get("passport_data",{}).get("citizenship","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{passport_number}{_.get_text("registration_renewal_patient_check_data.issue_date")}{passport_issue_date} {passport_issue_place}{_.get_text("registration_renewal_patient_check_data.expiry_date")}{passport_expiry_date}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.adress', lang)}{state_data.get("live_adress","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.residence_reason', lang)}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.spouse_fio', lang)}{marriage_data.get("spouse_fio","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.marriage_citizenship', lang)}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.marriage_certificate_number', lang)}{marriage_data.get("marriage_number","Не найдено")}{_.get_text("registration_renewal_marriage_check_data.issue_place")}\n{marriage_data.get("issue_date","Не найдено")} {marriage_data.get("marriage_issue_place","Не найдено")}"
    elif residence_reason == "residence_reason_child":
        child_data = state_data.get("child_data", {})
        text = f"{_.get_text('registration_renewal_child_check_data.title', lang)}\n\n"
        text += f"{_.get_text('registration_renewal_child_check_data.full_name', lang)}{state_data.get("passport_data",{}).get("full_name","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.birth_date', lang)}{state_data.get("passport_data",{}).get("birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.citizenship', lang)}{state_data.get("passport_data",{}).get("citizenship","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{passport_number}{_.get_text("registration_renewal_patient_check_data.issue_date")}{passport_issue_date} {passport_issue_place}{_.get_text("registration_renewal_patient_check_data.expiry_date")}{passport_expiry_date}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.adress', lang)}{state_data.get("live_adress","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.residence_reason', lang)}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_fio', lang)}{child_data.get("child_fio","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_birth_date', lang)}{child_data.get("child_birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_citizenship', lang)}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_certificate_number', lang)}{child_data.get("child_certificate_number","Не найдено")}{_.get_text("registration_renewal_child_check_data.issue_place")}\n{child_data.get("child_certificate_issue_place","Не найдено")}\n"

    text += f"{_.get_text("stamp_check_datas_info.mvd_adress",lang)}{state_data.get("mvd_adress", "Не найдено")}"
    await message.answer(
        text=text,
        reply_markup=get_registration_renewal_after_residence_reason_and_location_keyboard(
            lang
        ),
    )


@registration_renewal_router.callback_query(
    F.data == "registrationrenewal_after_residence_reason"
)
async def handle_registration_renewal_after_residence_reason_and_location(
    message: CallbackQuery, state: FSMContext
):
    """Обработка сообщения после выбора причины проживания и адреса"""
    state_data = await state.get_data()
    lang = state_data.get("language")

    state_data = await state.get_data()
    pprint(state_data)
    await state.update_data(
        from_action=RegistrationRenewalStates.after_residence_reason_and_location,
        change_data_from_check="registrationrenewal_after_residence_reason",
    )
    passport_number = state_data.get("passport_data", {}).get(
        "passport_serial_number", "Не найдено"
    )
    passport_issue_date = state_data.get("passport_data", {}).get(
        "passport_issue_date", "Не найдено"
    )
    passport_issue_place = state_data.get("passport_data", {}).get(
        "passport_issue_place", "Не найдено"
    )
    passport_expiry_date = state_data.get("passport_data", {}).get(
        "passport_expiry_date", "Не найдено"
    )
    residence_reason = state_data.get("residence_reason", "Не найдено")
    if residence_reason == "residence_reason_patent":
        text = (
            f"{_.get_text('registration_renewal_patient_check_data.title', lang)}\n\n"
        )
        patient_data = state_data.get("patient_data", {})
        text += f"{_.get_text('registration_renewal_patient_check_data.full_name', lang)}{state_data.get("passport_data",{}).get("full_name","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.birth_date', lang)}{state_data.get("passport_data",{}).get("birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.citizenship', lang)}{state_data.get("passport_data",{}).get("citizenship","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{passport_number}{_.get_text("registration_renewal_patient_check_data.issue_date")}{passport_issue_date} {passport_issue_place}{_.get_text("registration_renewal_patient_check_data.expiry_date")}{passport_expiry_date}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.adress', lang)}{state_data.get("live_adress","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.residence_reason', lang)}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.patient_number', lang)}{patient_data.get("patient_number","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.patient_date', lang)}{patient_data.get("patient_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.patient_issue_place', lang)}{patient_data.get("patient_issue_place","Не найдено")}\n\n"
    elif residence_reason == "residence_reason_marriage":
        text = (
            f"{_.get_text('registration_renewal_marriage_check_data.title', lang)}\n\n"
        )
        marriage_data = state_data.get("marriage_data", {})
        text += f"{_.get_text('registration_renewal_marriage_check_data.full_name', lang)}{state_data.get("passport_data",{}).get("full_name","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.birth_date', lang)}{state_data.get("passport_data",{}).get("birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.citizenship', lang)}{state_data.get("passport_data",{}).get("citizenship","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{passport_number}{_.get_text("registration_renewal_patient_check_data.issue_date")}{passport_issue_date} {passport_issue_place}{_.get_text("registration_renewal_patient_check_data.expiry_date")}{passport_expiry_date}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.adress', lang)}{state_data.get("live_adress","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.residence_reason', lang)}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.spouse_fio', lang)}{marriage_data.get("spouse_fio","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.marriage_citizenship', lang)}\n"
        text += f"{_.get_text('registration_renewal_marriage_check_data.marriage_certificate_number', lang)}{marriage_data.get("marriage_number","Не найдено")}{_.get_text("registration_renewal_marriage_check_data.issue_place")}\n{marriage_data.get("issue_date","Не найдено")} {marriage_data.get("marriage_issue_place","Не найдено")}"
    elif residence_reason == "residence_reason_child":
        child_data = state_data.get("child_data", {})
        text = f"{_.get_text('registration_renewal_child_check_data.title', lang)}\n\n"
        text += f"{_.get_text('registration_renewal_child_check_data.full_name', lang)}{state_data.get("passport_data",{}).get("full_name","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.birth_date', lang)}{state_data.get("passport_data",{}).get("birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.citizenship', lang)}{state_data.get("passport_data",{}).get("citizenship","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_patient_check_data.passport', lang)}{passport_number}{_.get_text("registration_renewal_patient_check_data.issue_date")}{passport_issue_date} {passport_issue_place}{_.get_text("registration_renewal_patient_check_data.expiry_date")}{passport_expiry_date}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.adress', lang)}{state_data.get("live_adress","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.residence_reason', lang)}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_fio', lang)}{child_data.get("child_fio","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_birth_date', lang)}{child_data.get("child_birth_date","Не найдено")}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_citizenship', lang)}\n"
        text += f"{_.get_text('registration_renewal_child_check_data.child_certificate_number', lang)}{child_data.get("child_certificate_number","Не найдено")}{_.get_text("registration_renewal_child_check_data.issue_place")}\n{child_data.get("child_certificate_issue_place","Не найдено")}"

    text += f"{_.get_text("stamp_check_datas_info.mvd_adress",lang)}{state_data.get("mvd_adress", "Не найдено")}"
    await message.answer(
        text=text,
        reply_markup=get_registration_renewal_after_residence_reason_and_location_keyboard(
            lang
        ),
    )
