from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates  # ← понадобится для шага телефона
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

    # фолбэк текстов
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

    # зафиксируем, что ждём ввод адреса
    await state.update_data(waiting_data="live_adress")

    try:
        photo = FSInputFile(photo_path)
        await call.message.answer_photo(photo=photo, caption=text)
    except Exception:
        # если картинки нет — просто текст
        await call.message.answer(text)

    # остаёмся в состоянии LiveAdress.adress — ждём сообщение пользователя


@live_adress_router.message(LiveAdress.adress)
async def handle_live_adress(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    waiting_data = state_data.get("waiting_data")
    session_id = state_data.get("session_id")

    value = message.text.strip()

    # Сохранение адреса
    if waiting_data and "." in waiting_data:
        pkey, skey = waiting_data.split(".", 1)
        container = state_data.get(pkey) or {}
        container[skey] = value
        await state.update_data({pkey: container})
        data_manager.save_user_data(message.from_user.id, session_id, {pkey: container})
    else:
        key = waiting_data or "live_adress"
        await state.update_data({key: value})
        data_manager.save_user_data(message.from_user.id, session_id, {key: value})

    # --- Переходы ---
    state_data = await state.get_data()
    next_states = state_data.get("next_states") or []
    from_action = state_data.get("from_action")

    # для отладки — видно, куда идём
    print(">>> live_adress next_states:", next_states, "from_action:", from_action)

    if next_states:
        # Если первым в очереди по ошибке оказался текущий стейт — выбросим его
        try:
            from states.components.live_adress import LiveAdress as _LA
            while next_states and next_states[0] == _LA.adress:
                next_states = next_states[1:]
        except Exception:
            pass

        if next_states:
            next_state = next_states[0]
            rest = next_states[1:]
            await state.update_data(next_states=rest)
        else:
            next_state = None

        if next_state == PhoneNumberStates.phone_number_input:
            await state.update_data(waiting_data="phone_number")
            await state.set_state(next_state)
            prompt = _.get_text("phone_number.ask", lang)
            if prompt.startswith("[Missing:"):
                prompt = "📞 Введите номер телефона в формате 79XXXXXXXXX."
            await message.answer(prompt)
        else:
            await state.set_state(next_state)
    else:
        # страховка: даже если очередь пуста — всё равно ведём на телефон
        await state.update_data(waiting_data="phone_number")
        await state.set_state(PhoneNumberStates.phone_number_input)
        prompt = _.get_text("phone_number.ask", lang)
        if prompt.startswith("[Missing:"):
            prompt = "📞 Введите номер телефона в формате 79XXXXXXXXX."
        await message.answer(prompt)


handle_live_adress_input = handle_live_adress
