from typing import Optional, List, Tuple, Dict
import re

from ocr.models.domain import PassportUZ
from ocr.parsing.mrz import parse_mrz


# ──────────────────────────────────────────────────────────────────────────────
# Регулярные выражения и утилиты
# ──────────────────────────────────────────────────────────────────────────────

_RX_DATE = re.compile(r"\b(\d{2})[ .\/-](\d{2})[ .\/-](\d{2,4})\b")
_RX_SUBDIV = re.compile(r"\b(\d{3}-\d{3})\b")
# внутр. паспорт: 2+2+6; загран: 2+7
_RX_SER_NUM_INTERNAL = re.compile(r"\b(\d{2})\s?(\d{2})\s?(\d{6})\b")
_RX_SER_NUM_ZAG = re.compile(r"\b(\d{2})\s?(\d{7})\b")
# маркеры «кем выдан»
_RX_ISSUER_HINT = re.compile(r"(ГУ\s*МВД|МВД|УФМС|ОТДЕЛ(?:ОМ)?|ОВД|ОУФМС|ТП\s*№|ГУМВД)", re.I)

def _norm_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def _fmt_century(dd: str, mm: str, yy: str) -> str:
    if len(yy) == 2:
        yy = ("20" if int(yy) <= 49 else "19") + yy
    return f"{dd}.{mm}.{yy}"

def _fmt_mrz_date(yymmdd: Optional[str]) -> Optional[str]:
    if not (yymmdd and yymmdd.isdigit() and len(yymmdd) == 6):
        return None
    yy, mm, dd = yymmdd[0:2], yymmdd[2:4], yymmdd[4:6]
    return _fmt_century(dd, mm, yy)

def _pick_near(lines: List[str], idx: int) -> str:
    prev = lines[idx - 1].strip() if idx > 0 else ""
    cur = lines[idx].strip()
    return _norm_spaces(f"{prev} {cur}".strip())

def _collapse_spaced_caps(text: str) -> str:
    """
    Склеиваем «Р О С С И Й С К А Я  Ф Е Д Е Р А Ц И Я» -> «РОССИЙСКАЯФЕДЕРАЦИЯ».
    Затем лишнее удалим отдельно.
    """
    return re.sub(r"(?:\b[А-ЯЁ]\b\s*)+", lambda m: m.group(0).replace(" ", ""), text)

def _clean_issuer(issuer: str) -> str:
    if not issuer:
        return issuer
    t = issuer.replace('"', ' ').replace("«", " ").replace("»", " ")
    t = _collapse_spaced_caps(t.upper())
    # убрать заголовок страницы «РОССИЙСКАЯ ФЕДЕРАЦИЯ»
    t = re.sub(r"\bРОССИЙСКАЯ\s*ФЕДЕРАЦИЯ\b", "", t)
    # нормализация написания ГУМВД → ГУ МВД
    t = t.replace("ГУМВД", "ГУ МВД")
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t.title()

def _extract_series_number_from_text(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Пытаемся достать серию/номер из OCR-текста (без MRZ).
    Поддерживаем внутренний (2+2+6) и загран (2+7).
    """
    t = text.replace("\n", " ")
    m1 = _RX_SER_NUM_INTERNAL.search(t)
    if m1:
        return f"{m1.group(1)}{m1.group(2)}", m1.group(3)
    m2 = _RX_SER_NUM_ZAG.search(t)
    if m2:
        return m2.group(1), m2.group(2)
    return None, None

# ──────────────────────────────────────────────────────────────────────────────
# Основной парсер
# ──────────────────────────────────────────────────────────────────────────────

class PassportRUSParser:
    """
    Сильный парсер российского паспорта (внутренний + загран).
    Приоритет: MRZ → entities → OCR-текст.
    Извлекает: ФИО, дата рождения, серия/номер, кем выдан (склейка строк + очистка), код подразделения,
               дата выдачи / срок действия (по меткам; у внутр. паспорта expiry обычно пуст).
    """

    def parse(self, lines: List[str], full_text: str, entities: list) -> Optional[PassportUZ]:
        text = full_text or ""
        ent_map: Dict[str, str] = {
            (e.get("name") or ""): (e.get("text") or "").strip()
            for e in (entities or []) if isinstance(e, dict)
        }

        # Базовые значения из entities
        surname = (ent_map.get("surname") or "").title()
        name    = (ent_map.get("name") or "").title()
        patron  = (ent_map.get("middle_name") or "") or None
        birth   = ent_map.get("birth_date") or ""
        issue   = ent_map.get("issue_date") or ""
        expiry  = ent_map.get("expiration_date") or ""
        nationality = (ent_map.get("citizenship") or "").upper() or None

        series = None
        number = None

        # 1) MRZ: главный источник правды
        mrz = parse_mrz(text)
        if mrz:
            surname = (mrz.get("surname") or surname or "").title()
            name    = (mrz.get("name") or name or "").title()
            # отчество MRZ чаще пусто — оставляем OCR-вариант, если он был
            birth_mrz  = _fmt_mrz_date(mrz.get("birth_date"))
            expiry_mrz = _fmt_mrz_date(mrz.get("expiry_date"))
            if birth_mrz:
                birth = birth_mrz

            num_mrz = mrz.get("number") or ""
            if num_mrz.isdigit():
                if len(num_mrz) >= 10:
                    # ВНУТРЕННИЙ: серия=первые 4, номер=следующие 6
                    series, number = num_mrz[:4], num_mrz[4:10]
                    # Для внутреннего «вторая MRZ-дата» — дата выдачи
                    if expiry_mrz:
                        issue = expiry_mrz
                        expiry = None
                elif len(num_mrz) >= 9:
                    # ЗАГРАН: серия=2, номер=7; вторая дата — срок действия
                    series, number = num_mrz[:2], num_mrz[2:9]
                    if expiry_mrz:
                        expiry = expiry_mrz

            nationality = nationality or (mrz.get("nationality") or "").upper() or None

        # 2) Серия/номер из текста (если MRZ не помог)
        if not (series and number):
            s2, n2 = _extract_series_number_from_text(text)
            series = series or s2
            number = number or n2

        # 3) Кем выдан (склейка двух строк + очистка мусора)
        issuer = None
        up = [ln.upper() for ln in lines]
        for i, ln in enumerate(up):
            if _RX_ISSUER_HINT.search(ln):
                base = _pick_near(lines, i)
                # если следующая строка — уточнение уровня («ОБЛАСТИ», «КРАЯ», «ГОРОДА …»), добавим её
                tail = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if re.fullmatch(r"(ОБЛАСТИ|КРАЯ|ГОРОДА\s+.+|РЕСПУБЛИКИ\s+.+)", tail.upper()):
                    base = f"{base} {tail}"
                issuer = _clean_issuer(base)
                break
        if not issuer:
            # fallback по явной подписи «Кем выдан»
            for i, ln in enumerate(lines):
                if "КЕМ ВЫДАН" in ln.upper():
                    issuer = _clean_issuer(_pick_near(lines, i))
                    break

        # 4) Код подразделения
        subdiv = None
        msub = _RX_SUBDIV.search(text.replace("\n", " "))
        if msub:
            subdiv = msub.group(1)

        # 5) Даты «выдачи/срок» (строго возле меток; не путать с DOB)
        if not issue:
            m = re.search(r"(Дата\s+выдачи|Выдан[ао]?)\W{0,120}" + _RX_DATE.pattern, text, re.I | re.S)
            if m:
                issue = _fmt_century(m.group(2), m.group(3), m.group(4))
        if not expiry:
            m = re.search(r"(Срок\s+действия|Действителен\s+до)\W{0,120}" + _RX_DATE.pattern, text, re.I | re.S)
            if m:
                expiry = _fmt_century(m.group(2), m.group(3), m.group(4))

        # 6) Гражданство по тексту (на случай отсутствия в entities/MRZ)
        if not nationality and "РОССИЯ" in text.upper():
            nationality = "RUS"

        # 7) Финальная проверка
        if not (surname and name):
            return None

        model = PassportUZ(
            surname=surname,
            name=name,
            patronymic=patron,
            birth_date=birth or "",
            issue_date=issue or None,
            expiry_date=expiry or None,
            issued_by=issuer or None,
            number=number or None,
            series=series or None,
            nationality=nationality or None,
            sex=ent_map.get("gender"),
            place_of_birth=ent_map.get("birth_place"),
        )

        # Примечание по коду подразделения:
        # если решишь выводить, положи его в extras в роутере после .to_canonical():
        #   canon.extras["subdivision"] = subdiv
        # Сейчас блок «Дополнительно» отключён по твоей просьбе.
        _ = subdiv  # чтобы линтер не ругался, если не используем здесь

        return model
