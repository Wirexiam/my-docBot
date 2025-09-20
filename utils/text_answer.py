from localization import _


def text_answer(age, state, stage, lang):
    """
    Находит по входящим параметрам нужный текст и вовзращает
    """
    text_title = f"{_.get_text(f'{age}_{state}_{stage}.title', lang)}"
    text_desc = f"{_.get_text(f'{age}_{state}_{stage}.desc', lang)}"
    texts = {"title": text_title, "desc": text_desc}
    return texts
