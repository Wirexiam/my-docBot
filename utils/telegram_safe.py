# utils/telegram_safe.py
from aiogram.exceptions import TelegramBadRequest

def _kb_dump(kb) -> str:
    return kb.model_dump_json(exclude_none=True, by_alias=True) if kb else ""

async def safe_edit_text(msg, text: str, reply_markup=None):
    try:
        same_text = (msg.text or "") == (text or "")
        same_kb = _kb_dump(msg.reply_markup) == _kb_dump(reply_markup)
        if same_text and same_kb:
            return
        return await msg.edit_text(text=text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        raise

async def safe_edit_reply_markup(msg, reply_markup):
    try:
        same_kb = _kb_dump(msg.reply_markup) == _kb_dump(reply_markup)
        if same_kb:
            return
        return await msg.edit_reply_markup(reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        raise
