from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from pdf_generator.gen_pdf import create_user_doc
from states.stamp_transfer import Stamp_transfer
from states.components.passport_manual import PassportManualStates
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from keyboards.stamp_transfer import (
    get_stamp_transfer_check_data_before_gen,
    get_waiting_confirm_stamp_transfer_start_keyboard,
    passport_start_keyboard,
)

from localization import _
from data_manager import SecureDataManager

stamp_transfer_router = Router()
data_manager = SecureDataManager()


@stamp_transfer_router.callback_query(F.data == "doc_stamp_restoration")
async def handle_stamp_restoration(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки восстановления штампа."""
    await state.set_state(Stamp_transfer.waiting_confirm_stamp_transfer_start)
    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(from_action="stamp_transfer_after_mvd")
    text = (
        f"{_.get_text('stamp_transfer.title', lang)}\n"
        f"{_.get_text('stamp_transfer.description', lang)}"
        f"{_.get_text('stamp_transfer.documents_to_prepare', lang)}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_waiting_confirm_stamp_transfer_start_keyboard(lang),
    )


@stamp_transfer_router.callback_query(F.data == "stamp_transfer_after_mvd")
async def handle_stamp_transfer_after_mvd(callback: CallbackQuery, state: FSMContext):
    """Переход после выбора МВД: готовим шаг старого паспорта."""
    await state.set_state(Stamp_transfer.after_select_mvd)
    state_data = await state.get_data()
    lang = state_data["language"]
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")

    data_manager.save_user_data(callback.from_user.id, session_id, {"mvd_adress": mvd_adress})

    await state.update_data(from_action=Stamp_transfer.after_old_passport)
    await state.update_data(passport_title="stamp_transfer_passport_old_title")

    text = (
        f"{_.get_text('stamp_transfer_passport_start.title', lang)}\n"
        f"{_.get_text('stamp_transfer_passport_start.description', lang)}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=passport_start_keyboard("old", lang),
    )


@stamp_transfer_router.message(Stamp_transfer.after_old_passport)
async def handle_old_passport_data(message: Message, state: FSMContext):
    """
    «Мост» на ввод нового паспорта:
    переносим текущие passport_data -> old_passport_data и предлагаем выбрать способ ввода НОВОГО паспорта.
    """
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    current_pd = state_data.get("passport_data") or {}
    await state.update_data(old_passport_data=current_pd, passport_data={})
    data_manager.save_user_data(message.from_user.id, session_id, {"old_passport_data": current_pd})

    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        passport_title="stamp_transfer_passport_new_title"
    )

    text = (
        f"{_.get_text('stamp_transfer_start_new_passport.title', lang)}\n\n"
        f"{_.get_text('stamp_transfer_start_new_passport.description', lang)}"
    )
    await message.answer(
        text=text,
        reply_markup=passport_start_keyboard("new", lang),
    )

    # На дальнейший сценарий: адрес -> телефон
    next_states = [LiveAdress.adress, PhoneNumberStates.phone_number_input]
    await state.update_data(next_states=next_states)


@stamp_transfer_router.message(Stamp_transfer.after_new_passport)
async def handle_new_passport_data(message: Message, state: FSMContext):
    """Обработка ручного ввода полей нового паспорта и показ сводки."""
    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data")
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    # безопасное сохранение как простого ключа, так и вложенного (dot-path)
    if waiting_data and "." in waiting_data:
        primary_key, secondary_key = waiting_data.split(".", 1)
        primary_key_data = dict(state_data.get(primary_key) or {})
        primary_key_data[secondary_key] = (message.text or "").strip()
        await state.update_data({primary_key: primary_key_data})
        data_manager.save_user_data(message.from_user.id, session_id, {primary_key: primary_key_data})
    elif waiting_data:
        value = (message.text or "").strip()
        await state.update_data({waiting_data: value})
        data_manager.save_user_data(message.from_user.id, session_id, {waiting_data: value})
    # else: ничего не ждали — пропускаем

    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        change_data_from_check="stamp_transfer_after_new_passport",
    )

    state_data = await state.get_data()
    pprint(state_data)
    new_passport_datas = state_data.get("passport_data") or {}
    old_passport_datas = state_data.get("old_passport_data") or {}

    data_to_view = {
        "name": new_passport_datas.get("full_name", "Не найден"),
        "new_passport_number": new_passport_datas.get("passport_serial_number", "Не найден"),
        "old_passport_number": old_passport_datas.get("passport_serial_number", "Не найден"),
        "new_passport_issue_place": new_passport_datas.get("passport_issue_place", "Не найден"),
        "old_passport_issue_place": old_passport_datas.get("passport_issue_place", "Не найден"),
        "new_passport_issue_date": new_passport_datas.get("passport_issue_date", "Не найден"),
        "old_passport_issue_date": old_passport_datas.get("passport_issue_date", "Не найден"),
        "new_passport_expiry_date": new_passport_datas.get("passport_expiry_date", "Не найден"),
        "old_passport_expiry_date": old_passport_datas.get("passport_expiry_date", "Не найден"),
        "live_adress": state_data.get("live_adress", "Не найден"),
        "phone_number": state_data.get("phone_number", "Не найден"),
        "mvd_adress": state_data.get("mvd_adress", "Не найден"),
    }

    text = (
        f"{_.get_text('stamp_check_datas_info.title', lang)}\n\n"
        f"{_.get_text('stamp_check_datas_info.full_name', lang)}{data_to_view['name']}\n"
        f"{_.get_text('stamp_check_datas_info.new_passport', lang)}"
        f"{data_to_view['new_passport_number']}"
        f"{_.get_text('stamp_check_datas_info.issue_date', lang)}"
        f"{data_to_view['new_passport_issue_date']} {data_to_view['new_passport_issue_place']}"
        f"{_.get_text('stamp_check_datas_info.expiry_date', lang)}"
        f"{data_to_view['new_passport_expiry_date']}\n"
        f"{_.get_text('stamp_check_datas_info.old_passport', lang)}"
        f"{data_to_view['old_passport_number']}"
        f"{_.get_text('stamp_check_datas_info.issue_date', lang)}"
        f"{data_to_view['old_passport_issue_date']} {data_to_view['old_passport_issue_place']}"
        f"{_.get_text('stamp_check_datas_info.expiry_date', lang)}"
        f"{data_to_view['old_passport_expiry_date']}\n"
        f"{_.get_text('stamp_check_datas_info.stamp_in', lang)}\n"
        f"{_.get_text('stamp_check_datas_info.adress', lang)}{data_to_view['live_adress']}\n"
        f"{_.get_text('stamp_check_datas_info.phone', lang)}{data_to_view['phone_number']}\n"
        f"{_.get_text('stamp_check_datas_info.mvd_adress', lang)}{data_to_view['mvd_adress']}"
    )

    await message.answer(
        text=text,
        reply_markup=get_stamp_transfer_check_data_before_gen(lang),
    )


@stamp_transfer_router.callback_query(F.data == "stamp_transfer_after_new_passport")
async def handle_new_passport_data_summary(message: CallbackQuery, state: FSMContext):
    """Переход «изменить» из сводки — пересобираем сводку с актуальными данными."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        change_data_from_check="stamp_transfer_after_new_passport",
    )

    state_data = await state.get_data()
    pprint(state_data)
    new_passport_datas = state_data.get("passport_data") or {}
    old_passport_datas = state_data.get("old_passport_data") or {}

    data_to_view = {
        "name": new_passport_datas.get("full_name", "Не найден"),
        "new_passport_number": new_passport_datas.get("passport_serial_number", "Не найден"),
        "old_passport_number": old_passport_datas.get("passport_serial_number", "Не найден"),
        "new_passport_issue_place": new_passport_datas.get("passport_issue_place", "Не найден"),
        "old_passport_issue_place": old_passport_datas.get("passport_issue_place", "Не найден"),
        "new_passport_issue_date": new_passport_datas.get("passport_issue_date", "Не найден"),
        "old_passport_issue_date": old_passport_datas.get("passport_issue_date", "Не найден"),
        "new_passport_expiry_date": new_passport_datas.get("passport_expiry_date", "Не найден"),
        "old_passport_expiry_date": old_passport_datas.get("passport_expiry_date", "Не найден"),
        "live_adress": state_data.get("live_adress", "Не найден"),
        "phone_number": state_data.get("phone_number", "Не найден"),
        "mvd_adress": state_data.get("mvd_adress", "Не найден"),
    }

    text = (
        f"{_.get_text('stamp_check_datas_info.title', lang)}\n\n"
        f"{_.get_text('stamp_check_datas_info.full_name', lang)}{data_to_view['name']}\n"
        f"{_.get_text('stamp_check_datas_info.new_passport', lang)}"
        f"{data_to_view['new_passport_number']}"
        f"{_.get_text('stamp_check_datas_info.issue_date', lang)}"
        f"{data_to_view['new_passport_issue_date']} {data_to_view['new_passport_issue_place']}"
        f"{_.get_text('stamp_check_datas_info.expiry_date', lang)}"
        f"{data_to_view['new_passport_expiry_date']}\n"
        f"{_.get_text('stamp_check_datas_info.old_passport', lang)}"
        f"{data_to_view['old_passport_number']}"
        f"{_.get_text('stamp_check_datas_info.issue_date', lang)}"
        f"{data_to_view['old_passport_issue_date']} {data_to_view['old_passport_issue_place']}"
        f"{_.get_text('stamp_check_datas_info.expiry_date', lang)}"
        f"{data_to_view['old_passport_expiry_date']}\n"
        f"{_.get_text('stamp_check_datas_info.stamp_in', lang)}\n"
        f"{_.get_text('stamp_check_datas_info.adress', lang)}{data_to_view['live_adress']}\n"
        f"{_.get_text('stamp_check_datas_info.phone', lang)}{data_to_view['phone_number']}\n"
        f"{_.get_text('stamp_check_datas_info.mvd_adress', lang)}{data_to_view['mvd_adress']}"
    )

    await message.message.edit_text(
        text=text,
        reply_markup=get_stamp_transfer_check_data_before_gen(lang),
    )


@stamp_transfer_router.callback_query(F.data == "all_true_in_stamp")
async def handle_all_true_in_stamp(callback: CallbackQuery, state: FSMContext):
    """Финальное подтверждение: генерируем документ."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    # стабильно парсим адрес в город/улицу/дом+хвост
    addr = (state_data.get("live_adress") or "").strip()
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    city = parts[0] if len(parts) > 0 else ""
    street = parts[1] if len(parts) > 1 else ""
    house = ", ".join(parts[2:]) if len(parts) > 2 else ""

    data = {
        "mvd_adress": state_data.get("mvd_adress", ""),
        "citizenship": (state_data.get("passport_data", {}) or {}).get("citizenship", ""),
        "full_name": (state_data.get("passport_data", {}) or {}).get("full_name", ""),
        "city": city,
        "street": street,
        "house": house,
        "phone": state_data.get("phone_number", ""),
        "old_passport_number": (state_data.get("old_passport_data", {}) or {}).get("passport_serial_number", ""),
        "old_passport_issue_place": (state_data.get("old_passport_data", {}) or {}).get("passport_issue_place", ""),
        "old_passport_issue_date": (state_data.get("old_passport_data", {}) or {}).get("passport_issue_date", ""),
        "old_passport_expire_date": (state_data.get("old_passport_data", {}) or {}).get("passport_expiry_date", ""),
        "new_passport_number": (state_data.get("passport_data", {}) or {}).get("passport_serial_number", ""),
        "new_passport_issue_place": (state_data.get("passport_data", {}) or {}).get("passport_issue_place", ""),
        "new_passport_issue_date": (state_data.get("passport_data", {}) or {}).get("passport_issue_date", ""),
        "new_passport_expire_date": (state_data.get("passport_data", {}) or {}).get("passport_expiry_date", ""),
    }

    doc = create_user_doc(context=data, template_name='template_ready', user_path='pdf_generator')
    ready_doc = FSInputFile(doc, filename='Заявление о перестановке штампа ВНЖ.docx')
    await state.clear()

    text = f"{_.get_text('ready_to_download_doc', lang)}\n"
    await callback.message.edit_text(text=text)
    await callback.message.answer_document(document=ready_doc)
