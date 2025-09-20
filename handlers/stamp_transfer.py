from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from handlers.components.live_adress import ask_live_adress

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
    lang = state_data.get("language")
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")

    data_manager.save_user_data(
        callback.from_user.id, session_id, {"mvd_adress": mvd_adress}
    )

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
    from keyboards.passport_preview import old_preview_kb

    """
    Если пришли из правки старого паспорта — сохраняем поле и снова показываем превью старого.
    Если нет — это «мост» к новому паспорту.
    """
    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")
    waiting_data = state_data.get("waiting_data")
    return_after_edit = state_data.get("return_after_edit")

    # Сохраняем точечное поле old_passport_data.* если ждали его
    if waiting_data and waiting_data.startswith("old_passport_data."):
        _unused, field = waiting_data.split(".", 1)
        old_pd = dict(state_data.get("old_passport_data") or {})
        old_pd[field] = (message.text or "").strip()
        await state.update_data(old_passport_data=old_pd, waiting_data=None)
        data_manager.save_user_data(
            message.from_user.id, session_id, {"old_passport_data": old_pd}
        )

    # Возврат из правки старого паспорта → показать превью и выйти
    if return_after_edit == "old_preview":
        p = (await state.get_data()).get("old_passport_data") or {}
        title = _.get_text("ocr.passport.success.title", lang)
        preview_tpl = _.get_text("ocr.passport.success.preview", lang)
        preview = preview_tpl.format(
            full_name=p.get("full_name", "—"),
            birth_date=p.get("birth_date", "—"),
            citizenship=p.get("citizenship", "—"),
            doc_id=p.get("passport_serial_number", p.get("doc_id", "—")),
            issued_by=p.get("passport_issue_place", "—"),
            issue_date=p.get("passport_issue_date", "—"),
            expiry_date=p.get("passport_expiry_date", "—"),
        )
        await message.answer(f"{title}\n\n{preview}", reply_markup=old_preview_kb())
        await state.update_data(return_after_edit=None)
        return

    # Если старый ещё не был скопирован, а в passport_data что-то есть — переносим
    current_pd = state_data.get("passport_data") or {}
    existing_old = state_data.get("old_passport_data") or {}
    if not existing_old and current_pd:
        await state.update_data(old_passport_data=current_pd, passport_data={})
        data_manager.save_user_data(
            message.from_user.id, session_id, {"old_passport_data": current_pd}
        )

    # Готовим ввод НОВОГО паспорта
    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        passport_title="stamp_transfer_passport_new_title",
        next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
        passport_input_mode="new",
        passport_data={},
    )

    text = (
        f"{_.get_text('stamp_transfer_start_new_passport.title', lang)}\n\n"
        f"{_.get_text('stamp_transfer_start_new_passport.description', lang)}"
    )
    await message.answer(text=text, reply_markup=passport_start_keyboard("new", lang))


@stamp_transfer_router.callback_query(F.data == "goto_adress_phone")
async def goto_adress_phone(cb: CallbackQuery, state: FSMContext):
    """Нажали в мини-сводке: идём собирать адрес, затем телефон."""
    data = await state.get_data()
    lang = data.get("language")

    # очередь шагов
    await state.update_data(
        next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
    )

    # спрашиваем адрес
    await state.update_data(waiting_data="live_adress")
    await state.set_state(LiveAdress.adress)
    await ask_live_adress(cb, state)  # ← прикрепит фото из static и подпись


@stamp_transfer_router.message(Stamp_transfer.after_new_passport)
async def handle_new_passport_data(message: Message, state: FSMContext):
    """
    Обработка ручного ввода полей НОВОГО паспорта.
    ЛОГИКА:
      - Сохраняем введённое значение (поддержка dot-path "passport_data.full_name").
      - Если это возврат из правки (return_after_edit == 'stamp_transfer_after_new_passport'):
            показываем МИНИ-СВОДКУ паспорта (без адреса/телефона) и ВЫХОДИМ.
      - Иначе: спрашиваем адрес -> телефон.
      - Когда адрес и телефон есть: показываем ФИНАЛЬНУЮ сводку с кнопкой формирования документа.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data")
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    # 1) Сохранить введённое значение (поддержка dot-path)
    if waiting_data and "." in waiting_data:
        primary_key, secondary_key = waiting_data.split(".", 1)
        primary_key_data = dict(state_data.get(primary_key) or {})
        primary_key_data[secondary_key] = (message.text or "").strip()
        # ВАЖНО: распаковка kwargs
        await state.update_data(**{primary_key: primary_key_data})
        data_manager.save_user_data(
            message.from_user.id, session_id, {primary_key: primary_key_data}
        )
    elif waiting_data:
        value = (message.text or "").strip()
        await state.update_data(**{waiting_data: value})
        data_manager.save_user_data(
            message.from_user.id, session_id, {waiting_data: value}
        )

    await state.update_data(waiting_data=None)

    # 2) Маркеры сценария + флаг редактирования
    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        change_data_from_check="stamp_transfer_after_new_passport",
    )
    state_data = await state.get_data()
    is_edit = state_data.get("return_after_edit") == "stamp_transfer_after_new_passport"

    # 3) Возврат из правки → мини-сводка
    if is_edit:
        new_pd = state_data.get("passport_data") or {}
        old_pd = state_data.get("old_passport_data") or {}

        def _val(d: dict, k: str, default: str = "—") -> str:
            v = (d.get(k) or "").strip()
            return v if v else default

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_.get_text("buttons.goto_adress_phone", lang),
                        callback_data="goto_adress_phone",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_.get_text("buttons.new_edit", lang),
                        callback_data="new_edit",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_.get_text("buttons.new_retry", lang),
                        callback_data="new_retry",
                    )
                ],
            ]
        )

        text = (
            "Проверьте паспортные данные\n\n"
            f"👤 ФИО: {_val(new_pd, 'full_name')}\n"
            f"🗓 Дата рождения: {_val(new_pd, 'birth_date')}\n"
            f"🌍 Гражданство: {_val(new_pd, 'citizenship')}\n"
            f"📄 Номер: {_val(new_pd, 'passport_serial_number')}\n"
            f"🏢 Кем выдан / дата: {_val(new_pd, 'passport_issue_place')} / {_val(new_pd, 'passport_issue_date')}\n"
            f"⏳ Срок действия: {_val(new_pd, 'passport_expiry_date')}\n\n"
            f"📄 Старый паспорт: {_val(old_pd, 'passport_serial_number')} "
            f"({_val(old_pd, 'passport_issue_place')} / {_val(old_pd, 'passport_issue_date')})"
        )

        await message.answer(text, reply_markup=kb)
        await state.update_data(return_after_edit=None)
        return

    # 4) Обычный поток: сначала адрес, потом телефон
    if not state_data.get("live_adress"):
        await state.update_data(waiting_data="live_adress")
        await state.set_state(LiveAdress.adress)
        prompt = _.get_text("live_adress.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📝 Укажите адрес проживания в РФ в одной строке: город, улица, дом, корпус/строение (если есть), квартира."
        await message.answer(prompt)
        return

    if not state_data.get("phone_number"):
        await state.update_data(waiting_data="phone_number")
        await state.set_state(PhoneNumberStates.phone_number_input)
        prompt = _.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "☎️ Введите ваш актуальный номер телефона\nПример: 79809008090"
        await message.answer(prompt)
        return

    # 4.1 Самопроверка: заполнен ли новый паспорт?
    new_passport = state_data.get("passport_data") or {}
    required = [
        "full_name",
        "passport_serial_number",
        "passport_issue_place",
        "passport_issue_date",
        "passport_expiry_date",
    ]
    if not any(new_passport.get(k) for k in required):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        await message.answer(
            "Похоже, данные нового паспорта не заполнены. Вернёмся к вводу?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=_.get_text("buttons.new_edit", lang),
                            callback_data="stamp_transfer_after_new_passport",
                        )
                    ]
                ]
            ),
        )
        return

    # 5) Оба паспорта введены — финальная сводка
    old_passport = state_data.get("old_passport_data") or {}

    data_to_view = {
        "name": new_passport.get("full_name", "Не найден"),
        "new_passport_number": new_passport.get("passport_serial_number", "Не найден"),
        "old_passport_number": old_passport.get("passport_serial_number", "Не найден"),
        "new_passport_issue_place": new_passport.get(
            "passport_issue_place", "Не найден"
        ),
        "old_passport_issue_place": old_passport.get(
            "passport_issue_place", "Не найден"
        ),
        "new_passport_issue_date": new_passport.get("passport_issue_date", "Не найден"),
        "old_passport_issue_date": old_passport.get("passport_issue_date", "Не найден"),
        "new_passport_expiry_date": new_passport.get(
            "passport_expiry_date", "Не найден"
        ),
        "old_passport_expiry_date": old_passport.get(
            "passport_expiry_date", "Не найден"
        ),
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
async def handle_new_passport_data_summary(cb: CallbackQuery, state: FSMContext):
    """
    Возврат из режима правки НОВОГО паспорта → показываем МИНИ-СВОДКУ паспорта
    (без адреса и телефона) и предлагаем перейти к их вводу.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        change_data_from_check="stamp_transfer_after_new_passport",
    )

    new_pd = state_data.get("passport_data") or {}
    old_pd = state_data.get("old_passport_data") or {}

    def _val(d, k, default="—"):
        v = (d.get(k) or "").strip()
        return v if v else default

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_.get_text("buttons.goto_adress_phone", lang),
                    callback_data="goto_adress_phone",
                )
            ],
            [
                InlineKeyboardButton(
                    text=_.get_text("buttons.new_edit", lang), callback_data="new_edit"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_.get_text("buttons.new_retry", lang),
                    callback_data="new_retry",
                )
            ],
        ]
    )

    text = (
        "Проверьте паспортные данные\n\n"
        f"👤 ФИО: {_val(new_pd, 'full_name')}\n"
        f"🗓 Дата рождения: {_val(new_pd, 'birth_date')}\n"
        f"🌍 Гражданство: {_val(new_pd, 'citizenship')}\n"
        f"📄 Номер: {_val(new_pd, 'passport_serial_number')}\n"
        f"🏢 Кем выдан / дата: {_val(new_pd, 'passport_issue_place')} / {_val(new_pd, 'passport_issue_date')}\n"
        f"⏳ Срок действия: {_val(new_pd, 'passport_expiry_date')}\n\n"
        f"📄 Старый паспорт: {_val(old_pd, 'passport_serial_number')} "
        f"({_val(old_pd, 'passport_issue_place')} / {_val(old_pd, 'passport_issue_date')})"
    )

    await cb.message.edit_text(text, reply_markup=kb)


@stamp_transfer_router.callback_query(F.data == "all_true_in_stamp")
async def handle_all_true_in_stamp(callback: CallbackQuery, state: FSMContext):
    """Финальное подтверждение: генерируем документ."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    # стабильно парсим адрес
    addr = (state_data.get("live_adress") or "").strip()
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    city = parts[0] if len(parts) > 0 else ""
    street = parts[1] if len(parts) > 1 else ""
    house = ", ".join(parts[2:]) if len(parts) > 2 else ""

    data = {
        "mvd_adress": state_data.get("mvd_adress", ""),
        "citizenship": (state_data.get("passport_data", {}) or {}).get(
            "citizenship", ""
        ),
        "full_name": (state_data.get("passport_data", {}) or {}).get("full_name", ""),
        "city": city,
        "street": street,
        "house": house,
        "phone": state_data.get("phone_number", ""),
        "old_passport_number": (state_data.get("old_passport_data", {}) or {}).get(
            "passport_serial_number", ""
        ),
        "old_passport_issue_place": (state_data.get("old_passport_data", {}) or {}).get(
            "passport_issue_place", ""
        ),
        "old_passport_issue_date": (state_data.get("old_passport_data", {}) or {}).get(
            "passport_issue_date", ""
        ),
        "old_passport_expire_date": (state_data.get("old_passport_data", {}) or {}).get(
            "passport_expiry_date", ""
        ),
        "new_passport_number": (state_data.get("passport_data", {}) or {}).get(
            "passport_serial_number", ""
        ),
        "new_passport_issue_place": (state_data.get("passport_data", {}) or {}).get(
            "passport_issue_place", ""
        ),
        "new_passport_issue_date": (state_data.get("passport_data", {}) or {}).get(
            "passport_issue_date", ""
        ),
        "new_passport_expire_date": (state_data.get("passport_data", {}) or {}).get(
            "passport_expiry_date", ""
        ),
    }

    doc = create_user_doc(
        context=data, template_name="template_ready", user_path="pdf_generator"
    )
    ready_doc = FSInputFile(doc, filename="Заявление о перестановке штампа ВНЖ.docx")
    await state.clear()

    text = f"{_.get_text('ready_to_download_doc', lang)}\n"
    await callback.message.edit_text(text=text)
    await callback.message.answer_document(document=ready_doc)
