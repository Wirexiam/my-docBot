from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from keyboards.components.residence_reason_child import (
    get_residence_reason_photo_or_manual_keyboard,
    get_residence_reason_who_for_child_keyboard,
)
from states.components.residence_reason_child import ResidenceReasonChildStates
from states.components.live_adress import LiveAdress

from localization import _
from data_manager import SecureDataManager

residence_reason_child_router = Router()
data_manager = SecureDataManager()


# ───────────────────────── Старт: выбор способа (фото/вручную) ─────────────────────────
@residence_reason_child_router.callback_query(F.data == "residence_reason_child")
async def handle_residence_reason_child_start(callback: CallbackQuery, state: FSMContext):
    """Запуск ветки 'Продление по ребёнку': выбор способа ввода данных (фото/вручную)."""
    await state.set_state(ResidenceReasonChildStates.choose_photo_or_manual)
    await state.update_data(residence_reason="residence_reason_child")

    sd = await state.get_data()
    lang = sd.get("language")

    text = _.get_text("start_residence_reason.description", lang)
    await callback.message.edit_text(
        text=text,
        reply_markup=get_residence_reason_photo_or_manual_keyboard(lang)
    )


# ───────────────────────── Ручной ввод: ФИО ребёнка ─────────────────────────
@residence_reason_child_router.callback_query(F.data == "start_residence_reason_child_manual")
async def handle_start_manual(callback: CallbackQuery, state: FSMContext):
    """Переход к ручному вводу данных ребёнка."""
    await state.set_state(ResidenceReasonChildStates.child_fio)

    sd = await state.get_data()
    lang = sd.get("language")

    text = (
        f"{_.get_text('residence_reason_manual_child_messages.child_fio.title', lang)}\n\n"
        f"{_.get_text('residence_reason_manual_child_messages.child_fio.description', lang)}\n\n"
        f"{_.get_text('residence_reason_manual_child_messages.child_fio.name_text', lang)}\n"
        f"{_.get_text('residence_reason_manual_child_messages.child_fio.example_text', lang)}"
    )
    await callback.message.edit_text(text=text)


@residence_reason_child_router.message(ResidenceReasonChildStates.child_fio)
async def get_child_fio(message: Message, state: FSMContext):
    """ФИО ребёнка → дата рождения."""
    sd = await state.get_data()
    child_data = dict(sd.get("child_data") or {})
    child_data["child_fio"] = (message.text or "").strip()
    await state.update_data(child_data=child_data)

    await state.set_state(ResidenceReasonChildStates.child_birth_date)
    lang = sd.get("language")
    text = (
        f"{_.get_text('residence_reason_manual_child_messages.child_birth_date.title', lang)}\n"
        f"{_.get_text('residence_reason_manual_child_messages.child_birth_date.example_text', lang)}"
    )
    await message.answer(text=text)


# ───────────────────────── Дата рождения → гражданство ─────────────────────────
@residence_reason_child_router.message(ResidenceReasonChildStates.child_birth_date)
async def get_child_birth_date(message: Message, state: FSMContext):
    sd = await state.get_data()
    child_data = dict(sd.get("child_data") or {})
    child_data["child_birth_date"] = (message.text or "").strip()
    await state.update_data(child_data=child_data)

    await state.set_state(ResidenceReasonChildStates.child_citizenship)
    lang = sd.get("language")
    text = (
        f"{_.get_text('residence_reason_manual_child_messages.child_citizenship.title', lang)}\n"
        f"{_.get_text('residence_reason_manual_child_messages.child_citizenship.example_text', lang)}"
    )
    await message.answer(text=text)


# ───────────────────────── Гражданство → № свидетельства ─────────────────────────
@residence_reason_child_router.message(ResidenceReasonChildStates.child_citizenship)
async def get_child_citizenship(message: Message, state: FSMContext):
    sd = await state.get_data()
    child_data = dict(sd.get("child_data") or {})
    child_data["child_citizenship"] = (message.text or "").strip()
    await state.update_data(child_data=child_data)

    await state.set_state(ResidenceReasonChildStates.child_certificate_number)
    lang = sd.get("language")
    text = (
        f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_number.title', lang)}\n"
        f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_number.example_text', lang)}"
    )
    await message.answer(text=text)


# ───────────────────────── № свидетельства → место выдачи ─────────────────────────
@residence_reason_child_router.message(ResidenceReasonChildStates.child_certificate_number)
async def get_child_certificate_number(message: Message, state: FSMContext):
    sd = await state.get_data()
    child_data = dict(sd.get("child_data") or {})
    child_data["child_certificate_number"] = (message.text or "").strip()
    await state.update_data(child_data=child_data)

    await state.set_state(ResidenceReasonChildStates.child_certificate_issue_place)
    lang = sd.get("language")
    text = (
        f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_issue_place.title', lang)}\n"
        f"{_.get_text('residence_reason_manual_child_messages.child_birth_cert_issue_place.example_text', lang)}"
    )
    await message.answer(text=text)


# ───────────────────────── Место выдачи → кто для ребёнка ─────────────────────────
@residence_reason_child_router.message(ResidenceReasonChildStates.child_certificate_issue_place)
async def get_child_certificate_issue_place(message: Message, state: FSMContext):
    sd = await state.get_data()
    child_data = dict(sd.get("child_data") or {})
    child_data["child_certificate_issue_place"] = (message.text or "").strip()
    await state.update_data(child_data=child_data)

    await state.set_state(ResidenceReasonChildStates.who_for_child)
    lang = sd.get("language")
    text = _.get_text("residence_reason_manual_child_messages.who_for_child.description", lang)
    await message.answer(text=text, reply_markup=get_residence_reason_who_for_child_keyboard(lang))


# ───────────────────────── Выбор: отец/мать/опекун → адрес проживания ─────────────────────────
@residence_reason_child_router.callback_query(F.data.startswith("residence_reason_child_"))
async def handle_residence_reason_child_who(callback: CallbackQuery, state: FSMContext):
    """Выбрали: residence_reason_child_father / _mother / _guardian → спрашиваем адрес."""
    who_for_child = callback.data.split("child_")[1]  # father|mother|guardian

    sd = await state.get_data()
    lang = sd.get("language")

    child_data = dict(sd.get("child_data") or {})
    child_data["who_for_child"] = who_for_child

    # КЛЮЧЕВОЕ: фиксируем основание/шаблон и указываем, что дальше ждём адрес
    await state.update_data(
        residence_reason="residence_reason_child",
        who="child",
        child_data=child_data,
        waiting_data="live_adress",
    )

    # Покажем пример + переводим в общий компонент адреса
    photo = FSInputFile("static/live_adress_example.png")
    caption = f"{_.get_text('live_adress.title', lang)}\n{_.get_text('live_adress.example', lang)}"
    await callback.message.answer_photo(photo=photo, caption=caption)

    await state.set_state(LiveAdress.adress)
