from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from pdf_generator.gen_pdf import create_user_doc
from states.stamp_transfer import Stamp_transfer
from states.components.passport_manual import PassportManualStates
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from keyboards.stamp_transfer import (
    get_stamp_transfer_check_data_before_gen,
    get_waiting_confirm_stamp_transfer_start_keyboard,
    stamp_transfer_passport_start_keyboard,
    passport_start_keyboard,
)
# заменил короткое имя '_' на явное i18n
from localization import _ as i18n
from data_manager import SecureDataManager

stamp_transfer_router = Router()
data_manager = SecureDataManager()


@stamp_transfer_router.callback_query(F.data == "doc_stamp_restoration")
async def handle_stamp_restoration(callback: CallbackQuery, state: FSMContext):
    """Начало процесса восстановления штампа"""
    await state.set_state(Stamp_transfer.waiting_confirm_stamp_transfer_start)
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="stamp_transfer_after_mvd")

    text = (
        f"{i18n.get_text('stamp_transfer.title', lang)}\n"
        f"{i18n.get_text('stamp_transfer.description', lang)}\n"
        f"{i18n.get_text('stamp_transfer.documents_to_prepare', lang)}"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_waiting_confirm_stamp_transfer_start_keyboard(lang),
    )


@stamp_transfer_router.callback_query(F.data == "stamp_transfer_after_mvd")
async def handle_stamp_transfer_after_mvd(callback: CallbackQuery, state: FSMContext):
    """Переход после выбора МВД: готовим шаг старого паспорта"""
    await state.set_state(Stamp_transfer.after_select_mvd)
    state_data = await state.get_data()
    lang = state_data.get("language")
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")

    # Сохраняем адрес МВД
    data_manager.save_user_data(callback.from_user.id, session_id, {"mvd_adress": mvd_adress})

    # Устанавливаем, что следующий шаг — старый паспорт
    await state.update_data(from_action=Stamp_transfer.after_old_passport)
    await state.update_data(passport_title="stamp_transfer_passport_old_title")

    text = (
        f"{i18n.get_text('stamp_transfer_passport_start.title', lang)}\n"
        f"{i18n.get_text('stamp_transfer_passport_start.description', lang)}"
    )

    # Отправляем клавиатуру с выбором OCR или ручного ввода
    await callback.message.edit_text(
        text=text,
        reply_markup=passport_start_keyboard("old", lang),
    )


@stamp_transfer_router.callback_query(F.data == "passport_old_manual_start")
async def start_old_manual(cb: CallbackQuery, state: FSMContext):
    """Начало ручного ввода старого паспорта"""
    await state.set_state(Stamp_transfer.after_old_passport)
    await state.update_data(waiting_data="old_passport_data.full_name")
    lang = (await state.get_data()).get("language")
    await cb.message.edit_text("⌨️ Введите ФИО старого паспорта:")


@stamp_transfer_router.callback_query(F.data == "passport_new_manual_start")
async def start_new_manual(cb: CallbackQuery, state: FSMContext):
    """Начало ручного ввода нового паспорта"""
    await state.set_state(Stamp_transfer.after_new_passport)
    await state.update_data(waiting_data="passport_data.full_name")
    lang = (await state.get_data()).get("language")
    await cb.message.edit_text("⌨️ Введите ФИО нового паспорта:")


# ─────────── обработчик ручного ввода старого паспорта ───────────
@stamp_transfer_router.message(Stamp_transfer.after_old_passport)
async def handle_old_passport_data(message: Message, state: FSMContext):
    """
    Обработка пошагового ручного ввода полей СТАРОГО паспорта.
    Последовательность полей:
      full_name -> birth_date -> citizenship -> passport_serial_number ->
      passport_issue_place -> passport_issue_date -> passport_expiry_date
    Поддерживается dot-path "old_passport_data.<field>" в waiting_data.
    """
    from keyboards.passport_preview import old_preview_kb

    state_data = await state.get_data()
    lang = state_data.get("language")
    session_id = state_data.get("session_id")
    waiting_data = state_data.get("waiting_data")
    return_after_edit = state_data.get("return_after_edit")

    # если не ждём ввода — игнорируем
    if not waiting_data:
        return

    # если это dot-path для old_passport_data.*
    if waiting_data.startswith("old_passport_data."):
        _, field = waiting_data.split(".", 1)
        old_pd = dict(state_data.get("old_passport_data") or {})
        old_pd[field] = (message.text or "").strip()
        # сохраняем
        await state.update_data(old_passport_data=old_pd, waiting_data=None)
        data_manager.save_user_data(message.from_user.id, session_id, {"old_passport_data": old_pd})
        # обновим snapshot
        state_data = await state.get_data()
    else:
        # на всякий случай — простое поле
        await state.update_data({waiting_data: (message.text or "").strip(), "waiting_data": None})
        data_manager.save_user_data(message.from_user.id, session_id, {waiting_data: (message.text or "").strip()})
        state_data = await state.get_data()

    # если пришли из режима правки — показываем превью и выходим
    if return_after_edit == "old_preview":
        p = state_data.get("old_passport_data") or {}
        title = i18n.get_text("ocr.passport.success.title", lang)
        preview_tpl = i18n.get_text("ocr.passport.success.preview", lang)
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

    # Проверим, какие поля ещё не заполнены — если есть незаполненные, спросим следующий
    seq = [
        "full_name",
        "birth_date",
        "citizenship",
        "passport_serial_number",
        "passport_issue_place",
        "passport_issue_date",
        "passport_expiry_date",
    ]
    old_pd = state_data.get("old_passport_data") or {}
    # найдём первое непустое поле
    next_field = None
    for f in seq:
        if not (old_pd.get(f) and str(old_pd.get(f)).strip()):
            next_field = f
            break

    # если есть следующее поле — запросим его
    if next_field:
        prompts = {
            "full_name": "👤 Введите ФИО старого паспорта (Только кириллица). Пример: Иванов Иван Иванович",
            "birth_date": "🗓 Введите дату рождения (формат ДД.ММ.ГГГГ). Пример: 20.01.1985",
            "citizenship": "🌍 Введите гражданство (название страны). Пример: Узбекистан",
            "passport_serial_number": "📄 Введите серию и номер паспорта (пример: AA0960090)",
            "passport_issue_place": "🏢 Введите кем выдан паспорт (пример: ГУ МВД Узбекистана, Ташкент г.)",
            "passport_issue_date": "🗓 Введите дату выдачи (формат ДД.MM.ГГГГ). Пример: 03.03.2013",
            "passport_expiry_date": "⏳ Введите срок действия паспорта (формат ДД.MM.ГГГГ). Пример: 02.03.2023",
        }
        await state.update_data(waiting_data=f"old_passport_data.{next_field}")
        await message.answer(prompts[next_field])
        return

    # если все поля заполнены — мост к новому паспорту (как раньше)
    current_pd = state_data.get("passport_data") or {}
    existing_old = state_data.get("old_passport_data") or {}
    if not existing_old and current_pd:
        await state.update_data(old_passport_data=current_pd, passport_data={})
        data_manager.save_user_data(message.from_user.id, session_id, {"old_passport_data": current_pd})

    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        passport_title="stamp_transfer_passport_new_title",
        next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input],
    )

    text = (
        f"{i18n.get_text('stamp_transfer_start_new_passport.title', lang)}\n\n"
        f"{i18n.get_text('stamp_transfer_start_new_passport.description', lang)}"
    )
    await message.answer(text=text, reply_markup=passport_start_keyboard("new", lang))

# ─────────── обработчик ручного ввода нового паспорта ───────────
@stamp_transfer_router.message(Stamp_transfer.after_new_passport)
async def handle_new_passport_data(message: Message, state: FSMContext):
    """
    Пошаговый ручной ввод полей НОВОГО паспорта:
    full_name -> birth_date -> citizenship -> passport_serial_number ->
    passport_issue_place -> passport_issue_date -> passport_expiry_date
    После заполнения всех полей продолжаем к адресу/телефону.
    """
    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data")
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    # Если не ждём ввода — игнорируем
    if not waiting_data:
        return

    # Сохранение значения (поддержка dot-path)
    if "." in waiting_data:
        primary_key, secondary_key = waiting_data.split(".", 1)
        primary_key_data = dict(state_data.get(primary_key) or {})
        primary_key_data[secondary_key] = (message.text or "").strip()
        await state.update_data({primary_key: primary_key_data, "waiting_data": None})
        data_manager.save_user_data(message.from_user.id, session_id, {primary_key: primary_key_data})
    else:
        value = (message.text or "").strip()
        await state.update_data({waiting_data: value, "waiting_data": None})
        data_manager.save_user_data(message.from_user.id, session_id, {waiting_data: value})

    # Обновим snapshot
    state_data = await state.get_data()

    # Маркеры сценария (оставляем так, как есть)
    await state.update_data(
        from_action=Stamp_transfer.after_new_passport,
        change_data_from_check="stamp_transfer_after_new_passport",
    )
    state_data = await state.get_data()
    is_edit = state_data.get("return_after_edit") == "stamp_transfer_after_new_passport"

    # Если возвращаемся из правки — показываем мини-сводку (как раньше)
    if is_edit:
        new_pd = state_data.get("passport_data") or {}
        old_pd = state_data.get("old_passport_data") or {}

        def _val(d: dict, k: str, default: str = "—") -> str:
            v = (d.get(k) or "").strip() if isinstance(d.get(k), str) else d.get(k) or ""
            return v if v else default

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

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно — перейти к адресу и телефону", callback_data="goto_adress_phone")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="new_edit")],
            [InlineKeyboardButton(text="🖼 Загрузить другое фото", callback_data="new_retry")],
        ])

        await message.answer(text, reply_markup=kb)
        await state.update_data(return_after_edit=None)
        return

    # Если мы только начинаем/в процессе заполнения passport_data — спросим следующий незаполненный паспортный поле
    seq = [
        "full_name",
        "birth_date",
        "citizenship",
        "passport_serial_number",
        "passport_issue_place",
        "passport_issue_date",
        "passport_expiry_date",
    ]
    passport_pd = state_data.get("passport_data") or {}
    next_field = None
    for f in seq:
        if not (passport_pd.get(f) and str(passport_pd.get(f)).strip()):
            next_field = f
            break

    if next_field:
        prompts = {
            "full_name": "👤 Введите ФИО (только кириллицей)\nПример: Абдуллаев Жахонгир Нодирович",
            "birth_date": "🗓 Введите дату рождения (ДД.MM.ГГГГ). Пример: 20.01.1962",
            "citizenship": "🌍 Введите гражданство. Пример: Узбекистан",
            "passport_serial_number": "📄 Введите серию и номер паспорта (пример: AA0960090)",
            "passport_issue_place": "🏢 Введите кем выдан паспорт (пример: ГУ МВД Узбекистана, Ташкент г.)",
            "passport_issue_date": "🗓 Введите дату выдачи (ДД.MM.ГГГГ). Пример: 03.03.2013",
            "passport_expiry_date": "⏳ Введите срок действия (ДД.MM.ГГГГ). Пример: 02.03.2023",
        }
        await state.update_data(waiting_data=f"passport_data.{next_field}")
        await message.answer(prompts[next_field])
        return

    # Если все поля паспорта заполнены — переходим к сбору адреса/телефона (как раньше)
    state_data = await state.get_data()
    if not state_data.get("live_adress"):
        await state.update_data(waiting_data="live_adress")
        await state.set_state(LiveAdress.adress)
        prompt = i18n.get_text("live_adress.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📝 Укажите адрес проживания в РФ в одной строке: город, улица, дом, корпус/строение (если есть), квартира."
        await message.answer(prompt)
        return

    if not state_data.get("phone_number"):
        await state.update_data(waiting_data="phone_number")
        await state.set_state(PhoneNumberStates.phone_number_input)
        prompt = i18n.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "☎️ Введите ваш актуальный номер телефона\nПример: 79809008090"
        await message.answer(prompt)
        return

    # Всё есть — финальная сводка (как раньше)
    new_passport = state_data.get("passport_data") or {}
    old_passport = state_data.get("old_passport_data") or {}

    data_to_view = {
        "name": new_passport.get("full_name", "Не найден"),
        "new_passport_number": new_passport.get("passport_serial_number", "Не найден"),
        "old_passport_number": old_passport.get("passport_serial_number", "Не найден"),
        "new_passport_issue_place": new_passport.get("passport_issue_place", "Не найден"),
        "old_passport_issue_place": old_passport.get("passport_issue_place", "Не найден"),
        "new_passport_issue_date": new_passport.get("passport_issue_date", "Не найден"),
        "old_passport_issue_date": old_passport.get("passport_issue_date", "Не найден"),
        "new_passport_expiry_date": new_passport.get("passport_expiry_date", "Не найден"),
        "old_passport_expiry_date": old_passport.get("passport_expiry_date", "Не найден"),
        "live_adress": state_data.get("live_adress", "Не найден"),
        "phone_number": state_data.get("phone_number", "Не найден"),
        "mvd_adress": state_data.get("mvd_adress", "Не найден"),
    }

    text = (
        f"{i18n.get_text('stamp_check_datas_info.title', lang)}\n\n"
        f"{i18n.get_text('stamp_check_datas_info.full_name', lang)}{data_to_view['name']}\n"
        f"{i18n.get_text('stamp_check_datas_info.new_passport', lang)}{data_to_view['new_passport_number']}"
        f"{i18n.get_text('stamp_check_datas_info.issue_date', lang)}{data_to_view['new_passport_issue_date']} {data_to_view['new_passport_issue_place']}"
        f"{i18n.get_text('stamp_check_datas_info.expiry_date', lang)}{data_to_view['new_passport_expiry_date']}\n"
        f"{i18n.get_text('stamp_check_datas_info.old_passport', lang)}{data_to_view['old_passport_number']}"
        f"{i18n.get_text('stamp_check_datas_info.issue_date', lang)}{data_to_view['old_passport_issue_date']} {data_to_view['old_passport_issue_place']}"
        f"{i18n.get_text('stamp_check_datas_info.expiry_date', lang)}{data_to_view['old_passport_expiry_date']}\n"
        f"{i18n.get_text('stamp_check_datas_info.stamp_in', lang)}\n"
        f"{i18n.get_text('stamp_check_datas_info.adress', lang)}{data_to_view['live_adress']}\n"
        f"{i18n.get_text('stamp_check_datas_info.phone', lang)}{data_to_view['phone_number']}\n"
        f"{i18n.get_text('stamp_check_datas_info.mvd_adress', lang)}{data_to_view['mvd_adress']}"
    )

    await message.answer(text=text, reply_markup=get_stamp_transfer_check_data_before_gen(lang))

# ─────────── переход из мини-сводки к адресу/телефону ───────────
@stamp_transfer_router.callback_query(F.data == "goto_adress_phone")
async def goto_adress_phone(cb: CallbackQuery, state: FSMContext):
    """
    Нажали в мини-сводке: идём собирать адрес, затем телефон.
    """
    data = await state.get_data()
    lang = data.get("language")

    # готовим очередь шагов
    await state.update_data(next_states=[LiveAdress.adress, PhoneNumberStates.phone_number_input])

    # спрашиваем адрес
    await state.update_data(waiting_data="live_adress")
    await state.set_state(LiveAdress.adress)
    prompt = i18n.get_text("live_adress.ask", lang)
    if prompt.startswith("[Missing:"):
        prompt = "📝 Укажите адрес проживания в РФ в одной строке: город, улица, дом, корпус/строение (если есть), квартира."
    await cb.message.edit_text(prompt)


# ─────────── финал: формирование документа и отправка ───────────
@stamp_transfer_router.callback_query(F.data == "all_true_in_stamp")
async def handle_all_true_in_stamp(callback: CallbackQuery, state: FSMContext):
    """Финальное подтверждение: генерируем документ на основе введённых данных."""
    state_data = await state.get_data()
    lang = state_data.get("language")

    # Парсим адрес в город / улицу / дом
    addr = (state_data.get("live_adress") or "").strip()
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    city = parts[0] if len(parts) > 0 else ""
    street = parts[1] if len(parts) > 1 else ""
    house = ", ".join(parts[2:]) if len(parts) > 2 else ""

    data = {
        "mvd_adress": state_data.get("mvd_adress", ""),
        "citizenship": (state_data.get("passport_data", {}) or {}).get("citizenship", ""),
        "full_name": (state_data.get("passport_data", {}) or {}).get("full_name", "") or (state_data.get("old_passport_data", {}) or {}).get("full_name", ""),
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

    # Генерация документа DOCX (с защитой)
    try:
        pprint(data)
        doc = create_user_doc(context=data, template_name='template_ready', user_path='pdf_generator')
        if not doc:
            raise RuntimeError("create_user_doc вернул пустое значение")
        ready_doc = FSInputFile(doc, filename='Заявление о перестановке штампа ВНЖ.docx')
    except Exception as e:
        pprint({"create_doc_error": str(e), "state_data": state_data})
        await callback.message.edit_text("❌ Ошибка при формировании документа. Попробуйте позже.")
        return

    # Очистка состояния
    await state.clear()

    # Отправляем сообщение и документ
    text = f"{i18n.get_text('ready_to_download_doc', lang)}\n"
    await callback.message.edit_text(text=text)
    await callback.message.answer_document(document=ready_doc)
