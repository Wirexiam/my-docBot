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

PHONE_STORE_RE = re.compile(r"^79\d{9}$")


def _normalize_phone(raw: str) -> str | None:
    """Нормализуем к формату 79XXXXXXXXX; вернём None, если невозможно."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw.strip())
    # частые варианты → 79XXXXXXXXX
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "7" + digits
    # '+7...' уже норм — убрали все нецифры выше
    if (
        len(digits) == 11
        and digits.startswith("7")
        and PHONE_STORE_RE.fullmatch(digits)
    ):
        return digits
    return None


async def _store_phone(
    user_id: int,
    session_id: str | None,
    state: FSMContext,
    phone: str,
    waiting_key: str | None,
):
    """
    Кладём телефон канонически (phone_number) и, при необходимости, дублируем под waiting_key
    для обратной совместимости со старым кодом.
    """
    await state.update_data(phone_number=phone)
    if session_id:
        data_manager.save_user_data(user_id, session_id, {"phone_number": phone})
    if waiting_key and waiting_key != "phone_number":
        await state.update_data({waiting_key: phone})
        if session_id:
            data_manager.save_user_data(user_id, session_id, {waiting_key: phone})


def _build_summary_text(lang: str, data: dict) -> str:
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
    t = (
        f"{_.get_text('stamp_check_datas_info.title', lang)}\n\n"
        f"{_.get_text('stamp_check_datas_info.full_name', lang)}{view['name']}\n"
        f"{_.get_text('stamp_check_datas_info.new_passport', lang)}"
        f"{view['new_passport_number']}"
        f"{_.get_text('stamp_check_datas_info.issue_date', lang)}"
        f"{view['new_passport_issue_date']} {view['new_passport_issue_place']}"
        f"{_.get_text('stamp_check_datas_info.expiry_date', lang)}"
        f"{view['new_passport_expiry_date']}\n"
        f"{_.get_text('stamp_check_datas_info.old_passport', lang)}"
        f"{view['old_passport_number']}"
        f"{_.get_text('stamp_check_datas_info.issue_date', lang)}"
        f"{view['old_passport_issue_date']} {view['old_passport_issue_place']}"
        f"{_.get_text('stamp_check_datas_info.expiry_date', lang)}"
        f"{view['old_passport_expiry_date']}\n"
        f"{_.get_text('stamp_check_datas_info.stamp_in', lang)}\n"
        f"{_.get_text('stamp_check_datas_info.adress', lang)}{view['live_adress']}\n"
        f"{_.get_text('stamp_check_datas_info.phone', lang)}{view['phone_number']}\n"
        f"{_.get_text('stamp_check_datas_info.mvd_adress', lang)}{view['mvd_adress']}"
    )
    return t


async def _after_phone_routing(message: Message, state: FSMContext, lang: str):
    """
    Универсальный роутинг после ввода телефона:
    - если есть next_states/return_action → идём по ним (совместимость),
    - иначе показываем сводку stamp_transfer.
    """
    data = await state.get_data()

    next_states = data.get("after_phone_next_states") or data.get("next_states")
    return_action = data.get("after_phone_return_action") or data.get("from_action")
    show_summary = data.get("show_summary_after_phone", True)  # по умолчанию включено

    if next_states:
        # классическая конвейерная логика
        if len(next_states) == 1 and return_action:
            await state.set_state(return_action)
            return
        next_state = next_states[0]
        rest = next_states[1:]
        await state.update_data(after_phone_next_states=rest)
        await state.set_state(next_state)
        return

    if show_summary:
        await state.update_data(
            from_action=Stamp_transfer.after_new_passport,
            change_data_from_check="stamp_transfer_after_new_passport",
        )
        text = _build_summary_text(lang, data)
        await message.answer(
            text=text, reply_markup=get_stamp_transfer_check_data_before_gen(lang)
        )
        return

    # Фолбэк, если сводка отключена
    saved = _.get_text("phone_number.saved", lang)
    if saved.startswith("[Missing:"):
        saved = "✅ Номер сохранён."
    await message.answer(saved)


@phone_number_router.message(PhoneNumberStates.phone_number_input, F.text)
async def handle_phone_number_text(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    session_id = state_data.get("session_id")
    waiting = state_data.get("waiting_data")

    phone = _normalize_phone(message.text or "")
    if not phone:
        prompt = _.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📞 Введите номер телефона в формате 79XXXXXXXXX."
        await message.answer("Некорректный номер. " + prompt)
        return

    await _store_phone(message.from_user.id, session_id, state, phone, waiting)
    await _after_phone_routing(message, state, lang)


@phone_number_router.message(PhoneNumberStates.phone_number_input, F.contact)
async def handle_phone_number_contact(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    session_id = state_data.get("session_id")
    waiting = state_data.get("waiting_data")

    raw = (message.contact.phone_number if message.contact else "") or ""
    phone = _normalize_phone(raw)
    if not phone:
        prompt = _.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📞 Введите номер телефона в формате 79XXXXXXXXX."
        await message.answer("Некорректный номер контакта. " + prompt)
        return

    await _store_phone(message.from_user.id, session_id, state, phone, waiting)
    await _after_phone_routing(message, state, lang)


handle_phone_number_input = handle_phone_number_text
