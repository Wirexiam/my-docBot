# Документация по папке `handlers`

Папка `handlers` содержит обработчики (хендлеры) событий для бота на базе [aiogram](https://docs.aiogram.dev/). Каждый файл реализует отдельную логику взаимодействия с пользователем: обработку команд, сообщений, нажатий на кнопки и работу с состояниями FSM.

---

## Общие рекомендации

- Каждый хендлер должен быть оформлен как асинхронная функция с аннотацией типа.
- Используйте docstring для описания назначения хендлера.
- Импортируйте необходимые состояния, клавиатуры, локализацию и менеджер данных.
- Для каждого хендлера используйте явное указание состояния FSM.
- Все хендлеры должны быть сгруппированы в роутеры (`Router`).
- Старайтесь не дублировать код, используйте вспомогательные функции и менеджеры.

---

## Структура файла-хендлера

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

# Импортируйте состояния, клавиатуры, локализацию, менеджер данных
from states.example import ExampleStates
from keyboards.example import get_example_keyboard
from localization import _
from data_manager import SecureDataManager

example_router = Router()
data_manager = SecureDataManager()

# Пример хендлера для callback_query
@example_router.callback_query(F.data == "example_action")
async def handle_example_action(callback: CallbackQuery, state: FSMContext):
    """Краткое описание назначения хендлера."""
    state_data = await state.get_data()
    lang = state_data.get("language")
    await callback.message.edit_text(
        _.get_text("example_action_text", lang),
        reply_markup=get_example_keyboard(lang)
    )

# Пример хендлера для сообщений в определённом состоянии
@example_router.message(ExampleStates.some_state)
async def handle_example_message(message: Message, state: FSMContext):
    """Описание обработки сообщения в состоянии ExampleStates.some_state."""
    state_data = await state.get_data()
    lang = state_data.get("language")
    await message.answer(_.get_text("example_state_reply", lang))
```

---

## Пример шаблона для нового хендлера

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.my_state import MyStates
from keyboards.my_keyboard import get_my_keyboard
from localization import _
from data_manager import SecureDataManager

my_router = Router()
data_manager = SecureDataManager()

@my_router.callback_query(F.data == "my_action")
async def handle_my_action(callback: CallbackQuery, state: FSMContext):
    """Обработка действия my_action."""
    await state.set_state(MyStates.next_state)
    state_data = await state.get_data()
    lang = state_data.get("language")
    await callback.message.edit_text(
        _.get_text("my_action_text", lang),
        reply_markup=get_my_keyboard(lang)
    )

@my_router.message(MyStates.next_state)
async def handle_my_state_message(message: Message, state: FSMContext):
    """Обработка сообщения в состоянии next_state."""
    state_data = await state.get_data()
    lang = state_data.get("language")
    await message.answer(_.get_text("my_state_saved_reply", lang))
```

---

## Описание основных элементов

- **Router** — объект для группировки хендлеров.
- **FSMContext** — объект для работы с состояниями пользователя.
- **CallbackQuery, Message** — типы событий aiogram.
- **Состояния (States)** — определяют этапы сценария пользователя.
- **Клавиатуры (Keyboards)** — используются для отправки inline-кнопок.
- **Локализация** — используйте `_.get_text(key, lang)` для получения текста на нужном языке.
- **SecureDataManager** — для сохранения и получения пользовательских данных.

---

## Пример обработки FSM

```python
@router.message(MyStates.input_name)
async def handle_name_input(message: Message, state: FSMContext):
    """Сохраняет имя пользователя и переводит к следующему шагу."""
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(MyStates.input_age)
    state_data = await state.get_data()
    lang = state_data.get("language")
    await message.answer(_.get_text("input_age_prompt", lang))
```

---

## Рекомендации по стилю

- Используйте f-строки для форматирования сообщений.
- Все строки, отображаемые пользователю, должны быть через локализацию (`_.get_text('key', lang)`).
- Не храните чувствительные данные в состоянии FSM, используйте менеджер данных.
- Для каждого действия пользователя создавайте отдельный хендлер.

---

## Регистрация роутеров

В файле инициализации (например, `main.py` или `bot.py`) зарегистрируйте все роутеры:

```python
from handlers import onboarding, main_menu, passport_manual, stamp_transfer, select_region_and_mvd

dp.include_router(onboarding.onboarding_router)
dp.include_router(main_menu.main_menu)
dp.include_router(passport_manual.components.passport_manual_router)
dp.include_router(stamp_transfer.stamp_transfer_router)
dp.include_router(select_region_and_mvd.select_region_router)
```

---

## FAQ

**В: Как добавить новый сценарий?**  
О: Создайте новый файл-хендлер, определите состояния, клавиатуры, добавьте роутер и зарегистрируйте его.

**В: Как добавить локализацию?**  
О: Добавьте ключи в файлы локализации и используйте `_.get_text('key', lang)`.

---

## См. также

- [Документация aiogram](https://docs.aiogram.dev/)
- [FSM aiogram](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html)
