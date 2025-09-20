# app/parsing/passport_parser.py
from typing import Optional, List, Tuple, Dict
import re

from ocr.models.domain import PassportUZ
from ocr.secondary_ocr import tesseract_patronymic
from ocr.parsing.parsers import parse_passport
from ocr.parsing.mrz import parse_mrz


# ───────── нормализация серий/номеров ─────────
# Поддерживаем: №4010 123456, 4010 123456, AA 5737888, AA5737888 (включая кейс Узбекистана)
_RX_SERNUM = re.compile(
    r"(?:№|N[o°]?)\s*?([A-ZА-Я]{0,3}\s*\d{2,4})\s*[-\s]?\s*([A-ZА-Я]?\d{6,9})", re.I
)
_TRANS_NUM = str.maketrans(
    {"O": "0", "o": "0", "I": "1", "l": "1", "|": "1", "S": "5", "B": "8"}
)

# ───────── эвристики ФИО ─────────
_RX_PATRON_VALID = re.compile(r"(?:ov?ich|evna|ovna|o'g'li|og'li|o‘g‘li|qizi)$", re.I)


def _split_fio_anyorder(fio: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """
    Делим ФИО устойчиво к дефисам/многословности:
    Возвращает (surname, name, patronymic|None).
    Эвристика: фамилия — ПОСЛЕДНЯЯ часть, имя — ПЕРВАЯ, всё между — отчество.
    """
    t = " ".join(fio.replace("—", "-").split()).strip()
    if not t:
        return None
    parts = [p for p in t.split(" ") if p]
    if len(parts) == 1:
        return None
    if len(parts) == 2:
        return parts[1], parts[0], None
    return parts[-1], parts[0], " ".join(parts[1:-1]) or None


def _sanitize_patronymic(p: Optional[str]) -> Optional[str]:
    if not p:
        return None
    p = re.sub(r"[^A-Za-zА-Яа-яЁё'‘’ʼ`´\- ]+", "", p).strip()
    return p if _RX_PATRON_VALID.search(p) else None


def _extract_issuer(lines: List[str]) -> Optional[str]:
    """
    Ищем блок «Кем выдан» как текущая строка с IIB/МВД + предыдущая строка.
    Пример: 'TOSHKENT SHAHAR' + 'MIRZO-ULUG‘BEK TUMANI IIB'
    """
    up = [ln.upper() for ln in lines]
    for i, ln in enumerate(up):
        if (
            (" IIB" in ln)
            or (" МВ" in ln)
            or ("УМВД" in ln)
            or (" МВД " in ln)
            or ("MVD" in ln)
        ):
            prev = lines[i - 1].strip() if i > 0 else ""
            cur = lines[i].strip()
            return re.sub(r"\s+", " ", f"{prev} {cur}".strip())
    return None


def _extract_series_number(blob: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлекаем серию/номер из общего текста (верх+низ+MRZ), после цифровой нормализации.
    Поддерживаем: AA5737888, №4010 123456, 4010123456, AA 12345678, и схемы с метками PASSPORT No./PASPORT RAQAMI и промежуточной строкой UZB.
    """
    t = (blob or "").translate(_TRANS_NUM)

    # 0) Явные метки "PASSPORT"/"PASPORT" (+ опциональный UZB на своей строке)
    m_label = re.search(
        r"(?:PASSPORT|PASPORT)\b[^\n]{0,40}\n(?:\s*UZB\s*\n)?\s*([A-Z]{1,3})\s*?(\d{6,9})",
        t,
        re.I,
    )
    if m_label:
        return m_label.group(1).upper(), m_label.group(2)

    # 1) Общая маска (№, серия/номер)
    m = _RX_SERNUM.search(t)
    if m:
        raw_series = (m.group(1) or "").strip()
        raw_number = (m.group(2) or "").strip()
        series = re.sub(r"[^A-Za-zА-Яа-я0-9]", "", raw_series)
        number = re.sub(r"[^0-9]", "", raw_number)

        # РФ: серия цифры (2 или 4) + номер 6
        if series and series.isdigit() and len(series) in (2, 4) and number.isdigit():
            return series, number

        # Узбекистан: серия буквы (1–3) + номер 7–9
        if series and re.fullmatch(r"[A-Za-zА-Яа-я]{1,3}", series) and number.isdigit():
            return series.upper(), number

    # 2) Монолит AA5737888 в любом месте
    mono = re.search(r"\b([A-ZА-Я]{1,3})\s?(\d{6,9})\b", t, re.I)
    if mono:
        return mono.group(1).upper(), mono.group(2)

    # 3) Склейка в одну строку без пробела (на всякий случай)
    mono2 = re.search(r"\b([A-ZА-Я]{2}\d{7,8})\b", t, re.I)
    if mono2:
        token = mono2.group(1)
        return token[:2].upper(), token[2:]

    return None, None


def _fmt_mrz_date(yymmdd: Optional[str]) -> Optional[str]:
    if not yymmdd or len(yymmdd) != 6 or not yymmdd.isdigit():
        return None
    yy, mm, dd = yymmdd[0:2], yymmdd[2:4], yymmdd[4:6]
    century = "20" if int(yy) <= 49 else "19"
    return f"{dd}.{mm}.{century}{yy}"


_DATE_TOKEN = r"(\d{2})[ ./-](\d{2})[ ./-](\d{2,4})"


def _pick_date(
    blob: str,
    labels: List[str],
    exclude: Optional[str] = None,
    allow_fallback: bool = False,
) -> Optional[str]:
    """
    Ищем дату формата DD[ ./-]MM[ ./-]YYYY только в «окне» после одной из меток.
    - labels: список regex-меток (напр. DATE OF EXPIRY, AMAL QILISH MUDDATI)
    - exclude: дата, которую нельзя возвращать (например, дата рождения)
    - allow_fallback: если True, можно искать первую дату в документе (кроме exclude)
    """
    t = blob or ""
    # 1) Поиск рядом с меткой: до 120 символов/переводов строк после неё
    for lb in labels:
        m = re.search(lb + r"[^\d]{0,120}?" + _DATE_TOKEN, t, flags=re.I | re.S)
        if m:
            dd, mm, yy = m.group(1), m.group(2), m.group(3)
            if len(yy) == 2:
                yy = ("20" if int(yy) <= 49 else "19") + yy
            cand = f"{dd}.{mm}.{yy}"
            if not exclude or cand != exclude:
                return cand

    # 2) (опционально) общий поиск — только если явно разрешено
    if allow_fallback:
        for m2 in re.finditer(r"\b" + _DATE_TOKEN + r"\b", t):
            dd, mm, yy = m2.group(1), m2.group(2), m2.group(3)
            if len(yy) == 2:
                yy = ("20" if int(yy) <= 49 else "19") + yy
            cand = f"{dd}.{mm}.{yy}"
            if not exclude or cand != exclude:
                return cand
    return None


class PassportUZParser:
    def parse(
        self, lines: List[str], full_text: str, entities: list
    ) -> Optional[PassportUZ]:
        """
        Стратегия:
        1) Rule-based (твой parse_passport) → базовые поля/ФИО.
        2) MRZ-фолбэк по ФИО/датам, если в шапке плохо.
        3) Отчество дополняем через tesseract_patronymic при необходимости.
        4) Серия/номер из нормализованного blob (верх/низ).
        5) «Кем выдан» = предыдущая + текущая строка вокруг IIB/МВД.
        6) Даты выдачи/окончания из меток DATE OF ISSUE / DATE OF EXPIRY (в т.ч. формат "11 06 2024").
        """
        raw: Dict[str, str] = parse_passport(lines, full_text, entities) or {}

        # ---- ФИО
        fio = (raw.get("fio") or "").strip()
        surname = name = patronymic = None
        if fio:
            sp = _split_fio_anyorder(fio)
            if sp:
                surname, name, patronymic = sp
                patronymic = _sanitize_patronymic(patronymic)

        # ---- MRZ fallback (ФИО + даты рождения/окончания)
        if not (surname and name):
            mrz = parse_mrz(full_text or "")
            if mrz:
                surname = surname or (mrz.get("surname") or "").title()
                name = name or (mrz.get("name") or "").title()
                raw.setdefault("date_of_birth", _fmt_mrz_date(mrz.get("birth_date")))
                raw.setdefault("date_of_expiry", _fmt_mrz_date(mrz.get("expiry_date")))

        if not (surname and name):
            return None  # лучше «не распознано», чем мусор

        # ---- добор отчества точечно (если есть победивший кадр)
        if not patronymic and raw.get("variant_path"):
            patronymic = _sanitize_patronymic(tesseract_patronymic(raw["variant_path"]))

        # ---- серия/номер
        series = raw.get("doc_series")
        number = raw.get("doc_num")
        if not (series and number):
            s, n = _extract_series_number(full_text or "")
            series = series or s
            number = number or n

        # ---- кем выдан
        issuer = raw.get("issued_by") or raw.get("issuer")
        if not issuer:
            issuer = _extract_issuer(lines)

        # ---- даты выдачи/окончания (из текста, если нет)
        # ---- даты выдачи/окончания (из текста, если нет)
        issue_date = raw.get("date_of_issue")
        expiry_date = raw.get("date_of_expiry")
        dob = raw.get("date_of_birth") or ""

        if not issue_date:
            issue_date = _pick_date(
                full_text or "",
                labels=[r"(?:DATE OF ISSUE|BERILGAN SANASI|BERILGAN\s+SANASI)"],
                exclude=dob,
                allow_fallback=False,  # для issue тоже не берём «первую попавшуюся»
            )

        if not expiry_date:
            expiry_date = _pick_date(
                full_text or "",
                labels=[
                    r"(?:DATE OF EXPIRY|AMAL QILISH MUDDATI|AMAL\s+QILISH\s+MUDDATI)"
                ],
                exclude=dob,
                allow_fallback=False,  # для expiry запрещаем глобальный фолбэк вообще
            )

        # ---- гражданство (для шаблонов)
        nationality = raw.get("nationality")
        if not nationality:
            mnat = re.search(
                r"\b(UZB|UZBEKISTAN|RUS|RUSSIA|UZBEK)\b", (full_text or "").upper()
            )
            if mnat:
                nationality = mnat.group(1)

        return PassportUZ(
            surname=surname,
            name=name,
            patronymic=patronymic,
            birth_date=raw.get("date_of_birth") or "",
            issue_date=issue_date,
            expiry_date=expiry_date,
            issued_by=issuer,
            number=number,
            series=series,
            nationality=nationality,
            sex=raw.get("sex"),
            place_of_birth=raw.get("place_of_birth"),
        )
