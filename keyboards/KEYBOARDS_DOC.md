# Документация по папке `keyboards`

Папка `keyboards` содержит функции для генерации inline-клавиатур с помощью aiogram. Все тексты кнопок должны быть локализованы через модуль `localization`.

---

## Общие рекомендации

- Используйте `InlineKeyboardBuilder` для создания клавиатур.
- Все тексты кнопок должны получатьcя через `_.get_text('key', lang)`.
- Для каждой клавиатуры создавайте отдельную функцию с параметром `lang: str = "ru"`.
- Не используйте захардкоженные строки для текста кнопок.
- Клавиатуры должны возвращать результат `as_markup()`.

---

## Пример шаблона для клавиатуры

```python
from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _

def get_example_keyboard(lang: str = "ru"):
    """Клавиатура для примера действия"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("example.confirm_button", lang),
        callback_data="example_confirm"
    )
    builder.button(
        text=_.get_text("example.cancel_button", lang),
        callback_data="main_menu"
    )
    builder.adjust(1)
    return builder.as_markup()
```

---

## Использование локализации

**Правильно:**
```python
text=_.get_text("some.key", lang)
```
**Неправильно:**
```python
text="Текст на русском"
```

---

## Пример использования в хендлере

```python
from keyboards.example import get_example_keyboard

await message.answer(
    _.get_text("example.prompt", lang),
    reply_markup=get_example_keyboard(lang)
)
```

---

## Рекомендации по стилю

- Для каждой логической группы кнопок создавайте отдельную функцию.
- Не смешивайте генерацию клавиатур и бизнес-логику.
- Используйте параметр `lang` во всех функциях для поддержки мультиязычности.
- Для динамических списков используйте циклы с локализацией внутри.

---

## FAQ

**В: Как добавить новую клавиатуру?**  
О: Создайте новую функцию в соответствующем файле, используйте локализацию для текста, возвращайте `as_markup()`.

**В: Как добавить новый язык?**  
О: Добавьте ключи для всех текстов кнопок в файлы локализации.

---

## См. также

- [Документация aiogram: InlineKeyboardBuilder](https://docs.aiogram.dev/en/latest/telegram/keyboards.html)
- [Документация по локализации](../localization/README.md)
