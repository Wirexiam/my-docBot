# Документация по папке `states`

Папка `states` содержит определения групп состояний (`StatesGroup`) для FSM aiogram. Каждая группа описывает этапы сценария пользователя для отдельного процесса (например, онбординг, ввод паспорта, оформление документов).

---

## Общие рекомендации

- Для каждого бизнес-процесса создавайте отдельный класс-наследник `StatesGroup`.
- Все состояния должны быть экземплярами `State()`.
- Используйте осмысленные имена классов и состояний.
- Добавляйте docstring к каждому классу.

---

## Пример шаблона для файла состояний

```python
from aiogram.fsm.state import State, StatesGroup

class ExampleStates(StatesGroup):
    """Состояния для примера процесса"""
    first_step = State()
    second_step = State()
    third_step = State()
```

---

## Пример использования в хендлере

```python
from states.example import ExampleStates

@router.message(ExampleStates.first_step)
async def handle_first_step(message: Message, state: FSMContext):
    # ...логика...
    await state.set_state(ExampleStates.second_step)
```

---

## Рекомендации по стилю

- Используйте snake_case для имён состояний.
- Для каждого процесса создавайте отдельный файл и класс.
- Не смешивайте состояния разных сценариев в одном классе.

---

## FAQ

**В: Как добавить новый сценарий?**  
О: Создайте новый файл, определите класс-наследник `StatesGroup` с нужными состояниями.

**В: Как использовать состояния?**  
О: Импортируйте класс и используйте его состояния в хендлерах.

---

## См. также

- [FSM aiogram](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html)
