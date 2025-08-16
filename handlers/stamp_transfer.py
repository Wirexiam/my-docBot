from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.stamp_transfer import Stamp_transfer
from states.components.passport_manual import PassportManualStates
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from keyboards.stamp_transfer import (
    get_stamp_transfer_check_data_before_gen,
    get_waiting_confirm_stamp_transfer_start_keyboard,
    stamp_transfer_passport_start_keyboard,
)
from localization import _
from data_manager import SecureDataManager

stamp_transfer_router = Router()
data_manager = SecureDataManager()


@stamp_transfer_router.callback_query(F.data == "doc_stamp_restoration")
async def handle_stamp_restoration(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки восстановления штампа"""

    # Установка состояния для передачи штампа
    await state.set_state(Stamp_transfer.waiting_confirm_stamp_transfer_start)
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="stamp_transfer_after_mvd")
    text = f"{_.get_text('stamp_transfer.title', lang)}\n{_.get_text('stamp_transfer.description', lang)}{_.get_text('stamp_transfer.documents_to_prepare', lang)}"
    # Отправка сообщения с клавиатурой ожидания подтверждения
    await callback.message.edit_text(
        text=text,
        reply_markup=get_waiting_confirm_stamp_transfer_start_keyboard(lang),
    )


@stamp_transfer_router.callback_query(F.data == "stamp_transfer_after_mvd")
async def handle_stamp_transfer_after_mvd(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки после выбора МВД для передачи штампа"""

    # Установка состояния для передачи штампа
    await state.set_state(Stamp_transfer.after_select_mvd)
    state_data = await state.get_data()
    lang = state_data["language"]
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")
    user_data = {
        "mvd_adress": mvd_adress,
    }
    data_manager.save_user_data(callback.from_user.id, session_id, user_data)

    await state.update_data(from_action=Stamp_transfer.after_old_passport)
    await state.update_data(passport_title="stamp_transfer_passport_old_title")

    text = f"{_.get_text('stamp_transfer_passport_start.title', lang)}\n{_.get_text('stamp_transfer_passport_start.description', lang)}"
    # Отправка сообщения с клавиатурой для начала передачи паспорта
    await callback.message.edit_text(
        text=text,
        reply_markup=stamp_transfer_passport_start_keyboard(lang),
    )


@stamp_transfer_router.message(Stamp_transfer.after_old_passport)
async def handle_old_passport_data(message: Message, state: FSMContext):
    """Обработка начала передачи паспорта после выбора МВД"""
    passport_data = await state.get_data()
    passport_data = passport_data.get("passport_data")
    passport_issue_place = message.text.strip()
    passport_data["passport_issue_place"] = passport_issue_place

    # Get the user's language preference from state data
    state_data = await state.get_data()
    lang = state_data.get("language")
    old_passport_data = passport_data
    passport_data = {}
    # Update the state with the passport issue place
    await state.update_data(passport_data=passport_data)
    user_data = {
        "passport_data": passport_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    user_data = {
        "old_passport_data": old_passport_data,
    }
    await state.update_data(old_passport_data=old_passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    # Установка состояния для передачи паспорта

    text = f"{_.get_text('stamp_transfer_start_new_passport.title', lang)}\n\n{_.get_text('stamp_transfer_start_new_passport.description', lang)}"

    # Отправка сообщения с клавиатурой для начала передачи паспорта
    await message.answer(
        text=text,
    )
    next_states = [LiveAdress.adress, PhoneNumberStates.phone_number_input]
    await state.update_data(
        from_action=Stamp_transfer.after_new_passport, next_states=next_states
    )
    await state.set_state(PassportManualStates.birth_date_input)


@stamp_transfer_router.message(Stamp_transfer.after_new_passport)
async def handle_new_passport_data(message: Message, state: FSMContext):
    """Обработка ввода данных нового паспорта после передачи старого паспорта"""
    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data", None)
    lang = state_data.get("language")
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

    await state.update_data(from_action=Stamp_transfer.after_new_passport)
    state_data = await state.get_data()
    pprint(state_data)
    new_passport_datas = state_data.get("passport_data")
    old_passport_datas = state_data.get("old_passport_data")

    data_to_view = {
        "name": new_passport_datas.get("full_name", "Не найден"),
        "new_passport_number": new_passport_datas.get(
            "passport_serial_number", "Не найден"
        ),
        "old_passport_number": old_passport_datas.get(
            "passport_serial_number", "Не найден"
        ),
        "new_passport_issue_date": new_passport_datas.get(
            "passport_issue_date", "Не найден"
        ),
        "old_passport_issue_date": old_passport_datas.get(
            "passport_issue_date", "Не найден"
        ),
        "live_adress": state_data.get("live_adress", "Не найден"),
        "phone_number": state_data.get("phone_number", "Не найден"),
    }

    text = f"{_.get_text('stamp_check_datas_info.title', lang)}\n\n"
    text += f"{_.get_text('stamp_check_datas_info.full_name', lang)}{data_to_view['name']}\n"
    text += f"{_.get_text('stamp_check_datas_info.new_passport')}{data_to_view['new_passport_number']}{_.get_text('stamp_check_datas_info.issue_date')}{data_to_view['new_passport_issue_date']}\n"
    text += f"{_.get_text('stamp_check_datas_info.old_passport')}{data_to_view['old_passport_number']}{_.get_text('stamp_check_datas_info.issue_date')}{data_to_view['old_passport_issue_date']}\n"
    text += f"{_.get_text('stamp_check_datas_info.stamp_in', lang)}\n"
    text += f"{_.get_text('stamp_check_datas_info.adress', lang)}{data_to_view['live_adress']}\n"
    text += f"{_.get_text('stamp_check_datas_info.phone', lang)}{data_to_view['phone_number']}"

    await message.answer(
        text=text,
        reply_markup=get_stamp_transfer_check_data_before_gen(lang),
    )
