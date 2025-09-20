import re
from typing import Dict, Optional

# Простенький парсер MRZ TD3/TD1 из сплошного текста full_text.
# Разбираем две возможные строки MRZ и вытягиваем фамилию/имя и даты YYMMDD.

MRZ_LINE_RX = re.compile(r"^[A-Z0-9<]{25,44}$")
ONLY_AZ09LT = re.compile(r"[^A-Z0-9<]")


def _clean(line: str) -> str:
    s = line.upper().replace(" ", "")
    s = ONLY_AZ09LT.sub("", s)
    return s


def _split_name(name_field: str) -> (str, str):
    # Surname<<Given<<Middle -> Surname / Given Middle
    parts = name_field.split("<<")
    surname = parts[0].replace("<", " ").strip()
    given = " ".join(p.replace("<", " ").strip() for p in parts[1:] if p)
    return surname, given


def parse_mrz(full_text: str) -> Optional[Dict[str, str]]:
    """
    Возвращает:
      {'surname': str, 'name': str, 'birth_date': 'YYMMDD', 'expiry_date': 'YYMMDD'}
      или None.
    Дополнительно: если нет двух подряд строк TD3, пытаемся разобрать хотя бы одну
    строку 'P<...' (имя+фамилия) и добрать даты из ближайших 1–3 строк.
    """
    if not full_text:
        return None

    raw_lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    lines = [_clean(ln) for ln in raw_lines if ln]

    # --- 1) Классический TD3: 2 подряд MRZ-строки ---
    # УСЛОВИЕ УЖЕСТОЧЕНО: принимаем ТОЛЬКО если первая строка действительно 'P<' и содержит '<<'
    for i in range(len(lines) - 1):
        a, b = lines[i], lines[i + 1]
        if (
            a.startswith("P<")
            and "<<" in a
            and MRZ_LINE_RX.match(a)
            and MRZ_LINE_RX.match(b)
            and 25 <= len(a) <= 44
            and 25 <= len(b) <= 44
        ):
            try:
                # Для TD3 берём поле после кода страны
                after_country = a.split("<", 2)[2]
                surname, given = _split_name(after_country)
                digits = re.findall(r"\d{6}", b)
                birth_yyMMdd = digits[0] if digits else ""
                expiry_yyMMdd = digits[1] if len(digits) > 1 else ""
                # Базовая валидация: нужна хотя бы фамилия и имя
                if surname and given:
                    return {
                        "surname": surname,
                        "name": given,
                        "birth_date": birth_yyMMdd,
                        "expiry_date": expiry_yyMMdd,
                    }
            except Exception:
                continue

    # --- 2) Облегчённый режим: одна строка 'P<...' где-то в тексте ---
    for idx, a in enumerate(lines):
        if a.startswith("P<") and "<<" in a and 15 <= len(a) <= 48:
            try:
                after_country = a.split("<", 2)[2]
                surname, given = _split_name(after_country)
                if not surname or not given:
                    continue
                # попробуем добрать даты из следующих 1–3 "линий"
                birth_yyMMdd = ""
                expiry_yyMMdd = ""
                for j in range(1, 4):
                    if idx + j >= len(lines):
                        break
                    b = lines[idx + j]
                    digits = re.findall(r"\d{6}", b)
                    if digits and not birth_yyMMdd:
                        birth_yyMMdd = digits[0]
                    if digits and len(digits) > 1 and not expiry_yyMMdd:
                        expiry_yyMMdd = digits[1]
                    if birth_yyMMdd and expiry_yyMMdd:
                        break
                return {
                    "surname": surname,
                    "name": given,
                    "birth_date": birth_yyMMdd,
                    "expiry_date": expiry_yyMMdd,
                }
            except Exception:
                continue

    return None
