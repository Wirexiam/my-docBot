# parsers.py — умный гибридный парсер паспортов UZ/RU/EN + MRZ
import re
import unicodedata
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from ocr.parsing.mrz import parse_mrz



# --- политика регистра для ФИО ---
# варианты:
#   "title"    -> Имя Отчество Фамилия (Title Case)
#   "upper"    -> ИМЯ ОТЧЕСТВО ФАМИЛИЯ (всё КАПСОМ)
#   "mrz_caps" -> КАПС только если поле пришло из MRZ; иначе Title Case
CASE_POLICY = "title"

# плохие паттерны для токенов ФИО
BAD_NAME_PATTERNS = [
    re.compile(r"[0-9]"),                 # цифры в имени
    re.compile(r"[=+*/\\|]"),             # спецсимволы
    re.compile(r"[A-Z]{15,}"),            # слишком длинные "слова" без пробела
]
TAG_RX = re.compile(r"<[^>\n]{1,80}>")  # срежем любые текстовые "теги" в угловых скобках

# whitelist для отчества по-узбекски
VALID_PATRONYMIC_SUFFIX = re.compile(r"(O['’`]G?LI|UGLI|QIZI)$", re.I)


# ---------- базовые regex ----------
DATE_RX = re.compile(r"\b(\d{1,2})[.\-/ ](\d{1,2})[.\-/ ](\d{2,4})\b")

# слова/метки, которые не являются персональными значениями
BAD_TOKENS = {
    # системные/фоновые
    "shaxsiyimzo", "holderssignature", "holder'ssignature",
    "o'zbekistonrespublikasi", "uzbekistonrespublikasi", "respublikasi",
    "republicofuzbekistan", "republic",
    "passport", "pasport", "pasporti",
    # метки полей
    "familiyasi", "surname",
    "ismi", "givenname", "givennames", "name",
    "otasiningismi", "middlename", "fathersname",
    "tug'ilgansanasi", "tugilgan sanasi", "tugilgan", "sanasi",
    "dateofbirth", "date of birth",
    "tugilganjoyi", "tug'ilgan joyi", "tugilgan joyi", "joyi", "joy",
    "placeofbirth", "place of birth",
    "dateofbirth", "date of birth",
    "dateofissue", "date of issue",
    "dateofexpiry", "date of expiry",
    "jinsi", "sex",
    "fuqaroligi", "nationality",
    "berilgansanasi", "dateofissue",
    "amalqilishmuddati", "dateofexpiry",
    "davlatkodi", "countrycode",
    "statepersonalizationcentre", "personalizationcentre", "authorit", "centre",
    # справочное
    "uzbekistan", "uzbekiston", "uzb", "erkak", "erkek", "male", "female",
    # шум OCR / техтеги
    "hw", "h/w", "rot", "rot0", "rot90", "rot180", "rot270",

}

# слова и фразы, которые НИКОГДА не являются частями ФИО
STOPWORDS = {
    # подпись / служебные
    "signature", "holder", "holders", "imzo", "shaxsiy", "shaxsiyimzo",
    "personalization", "centre", "center", "state", "authority", "organ", "organi",
    "passport", "pasport", "type", "country", "code", "nationality",
    "male", "female", "erkak", "ayol",
    # общие «служебные» слова
    "republic", "uzbekistan", "uzbekiston", "respublikasi",
}

# карты заголовков
UZ_HEADINGS = {
    "surname": ["familiyasi"],
    "name": ["ismi", "ati", "ati'"],  # каракалпак: ATI'
    "mname": ["otasining ismi"],
    "dob": ["tug'ilgan sanasi", "tuwi'lg'an sanesi", "tugilgan sanasi"],
    "issue": ["berilgan sanasi", "berilgen waqti'"],
    "expiry": ["amal qilish muddati", "mu'ddetinin' piter waqti'"],
}

EN_HEADINGS = {
    "surname": ["surname"],
    "name": ["given names", "given name"],
    "mname": ["middle name"],
    "dob": ["date of birth"],
    "issue": ["date of issue"],
    "expiry": ["date of expiry"],
}

RU_HEADINGS = {
    "surname": ["фамилия"],
    "name": ["имя"],
    "mname": ["отчество"],
    "dob": ["дата рождения"],
    "issue": ["дата выдачи"],
    "expiry": ["действителен до", "срок действия"],
}

# ---------- утилиты нормализации ----------

_DIACRIT_MAP = str.maketrans({
    "Ä": "A", "Å": "A", "Á": "A", "Â": "A", "Ã": "A", "Ā": "A",
    "Ö": "O", "Ó": "O", "Ô": "O", "Õ": "O", "Ō": "O",
    "Ü": "U", "Ú": "U", "Û": "U", "Ū": "U",
    "É": "E", "È": "E", "Ê": "E", "Ē": "E",
    "Í": "I", "Ì": "I", "Î": "I", "Ī": "I",
    "Ç": "C", "Ñ": "N",
})

def _norm_unicode(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    return s.translate(_DIACRIT_MAP)

def _normalize_quotes(s: str) -> str:
    return _norm_unicode(s).replace("ʼ", "'").replace("ʻ", "'").replace("’", "'").replace("‘", "'")

def _compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize_quotes(s).lower())

def _contains_bad_token(s: str) -> bool:
    c = _compact(s)
    if not c:
        return False
    if c in BAD_TOKENS:
        return True
    # если внутри слитной строки есть любой токен/стоп-слово
    if any(tok in c for tok in BAD_TOKENS):
        return True
    low = _normalize_quotes(s).lower()
    if any(sw in low for sw in STOPWORDS):
        return True
    return False

def _only_letters(s: str) -> str:
    return re.sub(r"[^A-Za-zА-Яа-яЁёʼ’' -]+", "", _norm_unicode(s)).strip()

def _is_person_value(s: str) -> bool:
    t = _only_letters(s)
    if not t:
        return False
    if _contains_bad_token(t):   # ← стоп-слова/токены
        return False
    letters_only = re.sub(r"[^A-Za-zА-Яа-яЁё]", "", t)
    if len(letters_only) <= 2:   # одно-/двухбуквенные шумы
        return False
    if len(t) > 64:
        return False
    if VALID_PATRONYMIC_SUFFIX.search(t.upper()):
        return True
    for rx in BAD_NAME_PATTERNS:
        if rx.search(t.upper()):
            return False
    if t.count("'") > 1:
        return False
    return True

def _pretty_case(s: str, from_mrz: bool = False) -> str:
    """Форматирование регистра для ФИО согласно CASE_POLICY.
       - "title"    : всегда Title Case
       - "upper"    : всегда UPPER
       - "mrz_caps" : если from_mrz=True -> UPPER, иначе Title Case
    """
    if not s:
        return ""
    s = _norm_unicode(s).strip()
    policy = CASE_POLICY.lower()
    if policy == "upper":
        return s.upper()
    if policy == "title":
        return s.title()
    # mrz_caps (по умолчанию поведение «умное»)
    return s.upper() if from_mrz else s.title()

def _clean_line_soft(s: str) -> str:
    if not s:
        return ""
    words = [_only_letters(w) for w in s.split()]
    kept = [w for w in words if w and not _contains_bad_token(w)]
    return " ".join(kept).strip()


# ---------- даты ----------

def _norm_date_any(s: str) -> Optional[str]:
    if not s:
        return None
    m = DATE_RX.search(s.replace(",", " "))
    if not m:
        return None
    d = int(m.group(1)); mth = int(m.group(2)); y = int(m.group(3))
    if y < 100:
        y = 2000 + y if y <= 25 else 1900 + y
    try:
        _ = date(y, mth, d)
        return f"{d:02d}.{mth:02d}.{y:04d}"
    except Exception:
        return None

def _mrz_date(s: Optional[str]) -> Optional[str]:
    if not s or len(s) < 6:
        return None
    yy, mm, dd = s[0:2], s[2:4], s[4:6]
    y = int(yy); y += 2000 if y <= 25 else 1900
    try:
        _ = date(y, int(mm), int(dd))
        return f"{int(dd):02d}.{int(mm):02d}.{y:04d}"
    except Exception:
        return None

def _plausible(b: Optional[str], i: Optional[str], e: Optional[str]) -> Dict[str, bool]:
    def to_date(x: Optional[str]) -> Optional[date]:
        try:
            return datetime.strptime(x, "%d.%m.%Y").date() if x else None
        except Exception:
            return None
    bd, idt, ex = map(to_date, (b, i, e))
    ok = {"birth": False, "issue": False, "expiry": False}
    today = date.today()
    if bd and date(1900, 1, 1) <= bd < today:
        ok["birth"] = True
    if idt:
        low = date(bd.year + 14, bd.month, bd.day) if bd else date(1950, 1, 1)
        if low <= idt <= today:
            ok["issue"] = True
    if ex:
        up = date(bd.year + 100, bd.month, bd.day) if bd else date(2100, 12, 31)
        if (not idt or idt < ex) and date(1970, 1, 1) <= ex <= up:
            ok["expiry"] = True
    if ok["issue"] and ok["expiry"] and idt and ex and not (idt < ex):
        ok["expiry"] = False
    return ok

# ---------- работа с entities ----------

def _ent(entities: List[Dict], key: str) -> Optional[str]:
    for e in entities or []:
        if (e.get("name") or "").lower() == key:
            t = (e.get("text") or "").strip()
            if t and t != "-":
                t = _only_letters(t)
                return t if _is_person_value(t) else None
    return None

def _ent_date(entities: List[Dict], key: str) -> Optional[str]:
    for e in entities or []:
        if (e.get("name") or "").lower() == key:
            t = (e.get("text") or "").strip()
            x = _norm_date_any(t)
            if x:
                return x
    return None

# ---------- эвристики на ФИО ----------

_SURNAME_SUFFIXES = {
    "OV","OVA","EV","EVA","YEV","YEVA",
    "OVICH","OVNA","EVICH","EVNA","YEVICH","YEVNA",
    "LI","OVI","OVIY",
}

def _norm_up(s: str) -> str:
    return _normalize_quotes(_only_letters(s)).upper()

def _is_patronymic_uz(s: str) -> bool:
    t = _norm_up(s)
    return bool(re.search(r"(O['’`]G?LI|UGLI|QIZI)$", t))

def _is_patronymic_ru(s: str) -> bool:
    t = _norm_up(s)
    return t.endswith(("OVICH","EVICH","YEVICH","OVNA","EVNA","YEVNA"))

def _surname_score(s: str) -> int:
    t = _norm_up(s)
    if not _is_person_value(t):
        return 0
    score = 10
    if len(t) >= 4: score += 10
    if len(t) >= 6: score += 10
    if any(t.endswith(suf) for suf in _SURNAME_SUFFIXES): score += 35
    if " " not in t: score += 5
    return score

def _name_score(s: str) -> int:
    t = _norm_up(s)
    if not _is_person_value(t):
        return 0
    name_suffix_hits = any(t.endswith(end) for end in ("JON","BEK","BEKJON","IDDIN"))
    common = {"ISLOMDJON","ISLOM","ABDULLOH","MUHAMMAD","DILSHOD","SHERZOD","JASUR","KAMOL","ILHOM","RUSTAM","OGABEK"}
    score = 10 + (15 if name_suffix_hits else 0) + (20 if t in common else 0)
    if len(t) >= 3: score += 10
    return score

def _mname_score(s: str) -> int:
    t = _norm_up(s)
    if not _is_person_value(t):
        return 0
    score = 0
    if _is_patronymic_uz(t) or _is_patronymic_ru(t): score += 50
    if len(t) >= 6: score += 10
    return score

# ---------- извлечение по заголовкам ----------

def _has_heading(s: str, heads: List[str]) -> bool:
    low = _normalize_quotes(s).lower()
    return any(h in low for h in heads)

def _extract_after_heading(lines: List[str], heads: List[str]) -> Optional[str]:
    for i, raw in enumerate(lines):
        if _has_heading(raw, heads):
            for j in range(1, 3):  # смотрим до двух строк вперёд
                if i + j < len(lines):
                    cand = _clean_line_soft(lines[i + j])
                    cand = _only_letters(cand)
                    if _is_person_value(cand) and not _contains_bad_token(cand):
                        return cand
    return None

def _extract_date_by_headings(lines: List[str], heads: List[str]) -> Optional[str]:
    for i, raw in enumerate(lines):
        if _has_heading(raw, heads):
            for j in range(1, 4):  # ищем в радиусе 3 строк
                if i + j < len(lines):
                    x = _norm_date_any(lines[i + j])
                    if x:
                        return x
    return None

def _extract_surname_strict(lines: List[str]) -> Optional[str]:
    """
    Строго: ищем заголовок 'FAMILIYASI' / 'SURNAME' / 'ФАМИЛИЯ', берём ближайшие 3 строки ниже,
    из каждой берём первое валидное слово с максимальным surname-score.
    """
    all_heads = UZ_HEADINGS["surname"] + EN_HEADINGS["surname"] + RU_HEADINGS["surname"]
    best = None
    best_score = 0
    for i, raw in enumerate(lines):
        if _has_heading(raw, all_heads):
            for j in range(1, 4):
                k = i + j
                if k >= len(lines):
                    break
                line = _clean_line_soft(lines[k])
                if not line:
                    continue
                for w in line.split():
                    w = _only_letters(w)
                    if not w or not _is_person_value(w):
                        continue
                    sc = _surname_score(w)
                    if sc > best_score:
                        best, best_score = w, sc
            break
    return best

def _fallback_surname_global(lines: List[str]) -> Optional[str]:
    """
    Если ничего не нашли: пробегаем все строки и берём слово с максимальным surname-score.
    """
    best = None
    best_score = 0
    for raw in lines:
        soft = _clean_line_soft(raw)
        if not soft:
            continue
        for w in soft.split():
            w = _only_letters(w)
            if not w or not _is_person_value(w):
                continue
            sc = _surname_score(w)
            if sc > best_score:
                best, best_score = w, sc
    return best



# ---------- основной парсинг ----------

def _gather_candidates(lines: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Возвращает (surname_candidates, name_candidates, mname_candidates) из всех строк."""
    s_c, n_c, m_c = [], [], []
    for raw in lines:
        soft = _clean_line_soft(raw)
        if not soft:
            continue
        for w in soft.split():
            if not w or not _is_person_value(w):
                continue
            if _is_patronymic_uz(w) or _is_patronymic_ru(w):
                m_c.append(w)
            # оцениваем для всех ролей
            if _surname_score(w) >= 25:
                s_c.append(w)
            if _name_score(w) >= 20:
                n_c.append(w)
    return s_c, n_c, m_c



def _best(items: List[str], scorer) -> Optional[str]:
    if not items:
        return None
    return max(items, key=lambda x: scorer(x) or 0)

def _merge_with_mrz(person: Dict[str, Optional[str]], mrz: Optional[Dict[str, str]]) -> Dict[str, Optional[str]]:
    if not mrz:
        return person

    # MRZ надёжнее обычного OCR — но только если выглядит как реальное ФИО
    mrz_surname = _only_letters(mrz.get("surname", ""))
    mrz_name = _only_letters(mrz.get("name", ""))

    # Добавляем валидацию: не переписывать, если строка не похожа на персональную
    if mrz_surname and _is_person_value(mrz_surname):
        person["surname"] = mrz_surname
    if mrz_name and _is_person_value(mrz_name):
        person["name"] = mrz_name

    # Даты: используем MRZ как fallback
    mb = _mrz_date(mrz.get("birth_date"))
    me = _mrz_date(mrz.get("expiry_date"))
    if mb and not person.get("birth"):
        person["birth"] = mb
    if me and not person.get("expiry"):
        person["expiry"] = me
    return person



def parse_passport(lines: List[str], full_text: str, entities: List[Dict]) -> Dict[str, str]:
    """
    Вход:
      lines     — список строк full_text (по одной строке на элемент OCR)
      full_text — весь текст OCR
      entities  — список сущностей Yandex Vision (может быть пустой/частичный)

    Выход:
      {'fio': str, 'date_of_birth': str, 'date_of_issue': str, 'date_of_expiry': str}
    """

    # 0) Срезаем техтеги (<rot_180>, <hw_0> и пр.), они не встречаются в MRZ (в MRZ нет символа '>').
    full_text = TAG_RX.sub(" ", full_text or "")
    lines = [TAG_RX.sub(" ", ln or "") for ln in (lines or [])]

    # 1) Нормализованный список строк (без пустых)
    lines = [ln.strip() for ln in (lines or []) if (ln or "").strip()]

    # 2) Первый уровень — entities
    surname = _ent(entities, "surname")
    name = _ent(entities, "name")
    mname = _ent(entities, "middle_name")
    birth = _ent_date(entities, "birth_date")
    issue = _ent_date(entities, "issue_date")
    expiry = _ent_date(entities, "expiration_date") or _ent_date(entities, "expiry_date")

    # 3) Второй уровень — заголовки (UZ → EN → RU)
    if not surname:
        surname = (
            _extract_after_heading(lines, UZ_HEADINGS["surname"]) or
            _extract_after_heading(lines, EN_HEADINGS["surname"]) or
            _extract_after_heading(lines, RU_HEADINGS["surname"])
        )
    if not name:
        name = (
            _extract_after_heading(lines, UZ_HEADINGS["name"]) or
            _extract_after_heading(lines, EN_HEADINGS["name"]) or
            _extract_after_heading(lines, RU_HEADINGS["name"])
        )
    if not mname:
        mname = (
            _extract_after_heading(lines, UZ_HEADINGS["mname"]) or
            _extract_after_heading(lines, EN_HEADINGS["mname"]) or
            _extract_after_heading(lines, RU_HEADINGS["mname"])
        )
    if not birth:
        birth = (
            _extract_date_by_headings(lines, UZ_HEADINGS["dob"]) or
            _extract_date_by_headings(lines, EN_HEADINGS["dob"]) or
            _extract_date_by_headings(lines, RU_HEADINGS["dob"])
        )
    if not issue:
        issue = (
            _extract_date_by_headings(lines, UZ_HEADINGS["issue"]) or
            _extract_date_by_headings(lines, EN_HEADINGS["issue"]) or
            _extract_date_by_headings(lines, RU_HEADINGS["issue"])
        )
    if not expiry:
        expiry = (
            _extract_date_by_headings(lines, UZ_HEADINGS["expiry"]) or
            _extract_date_by_headings(lines, EN_HEADINGS["expiry"]) or
            _extract_date_by_headings(lines, RU_HEADINGS["expiry"])
        )

    # 4) Третий уровень — эвристики и кандидаты
    if not (surname and name):
        s_c, n_c, m_c = _gather_candidates(lines)
        if not surname:
            best_s = _best(s_c, _surname_score)
            if best_s:
                surname = best_s
        if not name:
            best_n = _best(n_c, _name_score)
            if best_n:
                name = best_n
        if not mname:
            best_m = _best(m_c, _mname_score)
            if best_m:
                mname = best_m

    # 5) MRZ-валидация / дополнение
    mrz = parse_mrz(full_text or "")
    person = {"surname": surname, "name": name, "mname": mname, "birth": birth, "issue": issue, "expiry": expiry}
    person = _merge_with_mrz(person, mrz)

    if not person.get("surname"):
        strict_s = _extract_surname_strict(lines)
        if strict_s:
            person["surname"] = strict_s
        else:
            glob_s = _fallback_surname_global(lines)
            if glob_s:
                person["surname"] = glob_s

    # 6) Форматируем ФИО по политике регистра
    surname_fmt = _pretty_case(person.get("surname"), from_mrz=bool(mrz and mrz.get("surname")))
    name_fmt = _pretty_case(person.get("name"), from_mrz=bool(mrz and mrz.get("name")))
    mname_fmt = _pretty_case(person.get("mname"), from_mrz=False)

    # 7) Даты: добираем из всего текста как последний резерв
    if not person.get("birth"):
        person["birth"] = _norm_date_any(full_text)
    if not person.get("issue") or not person.get("expiry"):
        all_dates = [m.group(0) for m in DATE_RX.finditer(full_text or "")]
        norm_dates = [d for d in (_norm_date_any(x) for x in all_dates) if d]
        if not person.get("issue") and norm_dates:
            person["issue"] = norm_dates[0]
        if not person.get("expiry") and len(norm_dates) > 1:
            person["expiry"] = norm_dates[1]

    birth = person.get("birth")
    issue = person.get("issue")
    expiry = person.get("expiry")

    # 8) Проверка правдоподобия дат
    ok = _plausible(birth, issue, expiry)
    if not ok["birth"]:
        birth = None
    if not ok["issue"]:
        issue = None
    if not ok["expiry"]:
        me = _mrz_date(mrz.get("expiry_date")) if mrz else None
        expiry = me or None

    # 9) Финальный FIO: Имя Отчество Фамилия
    def _dedup_and_clean(parts):
        out, seen = [], set()
        for w in parts:
            w = (w or "").strip()
            if not w:
                continue
            if _contains_bad_token(w):
                continue
            # ещё раз отсекаем одно-/двухбуквенные
            if len(re.sub(r"[^A-Za-zА-Яа-яЁё]", "", w)) <= 2:
                continue
            key = w.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(w)
        return out

    fio_parts = _dedup_and_clean([name_fmt, mname_fmt, surname_fmt])
    fio = " ".join(fio_parts).strip() if fio_parts else ""

    # ---- финальный возврат ----
    return {
        "fio": fio or "",
        "date_of_birth": birth or "",
        "date_of_issue": issue or "",
        "date_of_expiry": expiry or "",
        # поле не извлекаем в этом упрощённом варианте:
        "place_of_birth": "",
    }
