from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
import re

from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from localization import _
from data_manager import SecureDataManager

live_adress_router = Router()
data_manager = SecureDataManager()


@live_adress_router.callback_query(LiveAdress.adress)
async def ask_live_adress(call: CallbackQuery, state: FSMContext):
    """
    Показываем пример и запрашиваем адрес.
    ВАЖНО: заранее фиксируем, что дальше ждём 'live_adress'.
    """
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")

    title = _.get_text("live_adress.title", lang)
    if title.startswith("[Missing:"):
        title = "📝 Укажите адрес проживания в РФ в одной строке."
    example = _.get_text("live_adress.example", lang)
    if example.startswith("[Missing:"):
        example = "Формат: город, улица, дом, корпус/строение (если есть), квартира."

    if state_data.get("live_adress_conf") is None:
        photo_path = "static/live_adress_example.png"
        text = f"{title}\n{example}"
    else:
        photo_path = "static/live_adress.png"
        text_key = _.get_text("adress_residence_permit", lang)
        text = text_key if not text_key.startswith("[Missing:") else title

    await state.update_data(waiting_data="live_adress")

    try:
        photo = FSInputFile(photo_path)
        await call.message.answer_photo(photo=photo, caption=text)
    except Exception:
        await call.message.answer(text)

    # остаёмся в состоянии LiveAdress.adress — ждём сообщение пользователя


@live_adress_router.message(LiveAdress.adress)
async def handle_live_adress(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    waiting_data = state_data.get("waiting_data")
    session_id = state_data.get("session_id")

    # ── нормализация и лёгкая валидация адреса ─────────────────────
    raw = (message.text or "").strip()
    value = re.sub(r"[ \t]+", " ", raw)  # Убираем лишние пробелы
    value = re.sub(r"\s*,\s*", ", ", value).strip(", ")  # Убираем лишние пробелы после запятой

    # Если в строке нет запятой, но это не пустая строка, считаем, что адрес валиден
    if len(value.split(",")) == 1 and value:
        # Если строка состоит только из одного компонента и она не пустая, пропускаем её
        pass
    else:
        parts = [p for p in value.split(",") if p]  # Разделяем по запятой, убираем пустые элементы
        if len(parts) < 2:  # Если меньше двух компонентов, то это неполный адрес
            hint = _.get_text("live_adress.example", lang)
            if hint.startswith("[Missing:"):
                hint = "Формат: город, улица, дом, корпус/строение (если есть), квартира."
            await message.answer("Адрес выглядит неполным. " + hint)
            return

    # ── сохранение (dot-path поддержан) ────────────────────────────
    if waiting_data and "." in waiting_data:
        pkey, skey = waiting_data.split(".", 1)
        container = dict(state_data.get(pkey) or {})
        container[skey] = value
        await state.update_data({pkey: container})
        data_manager.save_user_data(message.from_user.id, session_id, {pkey: container})
    else:
        key = waiting_data or "live_adress"
        await state.update_data({key: value})
        data_manager.save_user_data(message.from_user.id, session_id, {key: value})

    # ── маршрутизация после адреса (ТОЛЬКО вперёд) ─────────────────
    state_data = await state.get_data()
    next_states = list(state_data.get("next_states") or [])
    from_action = state_data.get("from_action")

    print(">>> live_adress next_states:", next_states, "from_action:", from_action)

    # выкидываем возможный повтор текущего стейта в голове очереди
    try:
        from states.components.live_adress import LiveAdress as _LA
        while next_states and next_states[0] == _LA.adress:
            next_states.pop(0)
    except Exception:
        pass

    # больше НИКАКОГО len(next_states) == 1 -> from_action!
    next_state = next_states[0] if next_states else None
    rest = next_states[1:] if len(next_states) > 1 else []
    await state.update_data(next_states=rest)

    if next_state is None:
        # страховка: ведём на телефон
        await state.update_data(waiting_data="phone_number")
        await state.set_state(PhoneNumberStates.phone_number_input)
        prompt = _.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📞 Введите номер телефона в формате 79XXXXXXXXX."
        await message.answer(prompt)
        return

    if next_state == PhoneNumberStates.phone_number_input:
        await state.update_data(waiting_data="phone_number")
        await state.set_state(next_state)
        prompt = _.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📞 Введите номер телефона в формате 79XXXXXXXXX."
        await message.answer(prompt)
    else:
        await state.set_state(next_state)



# обратная совместимость со старым импортом имени функции
handle_live_adress_input = handle_live_adress
