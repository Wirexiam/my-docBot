# app/services/translit.py
import re

# Узбекистан/UZN латиница → кириллица (включая o‘/g‘, sh/ch/ng)
_MAP_MULTI = {
    "o‘": "ў",
    "g‘": "ғ",
    "o'": "ў",
    "g'": "ғ",
    "sh": "ш",
    "ch": "ч",
    "ng": "нг",
}
_MAP_SINGLE = {
    "a": "а",
    "b": "б",
    "c": "ц",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "ҳ",
    "i": "и",
    "j": "ж",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "қ",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "x": "х",
    "y": "й",
    "z": "з",
}


def _restore_case(src: str, dst: str) -> str:
    # восстанавливаем капс по словам: Aleksandr → Александр; RAYKOV → РАЙКОВ
    if src.isupper():
        return dst.upper()
    if src.istitle():
        return dst.capitalize()
    return dst


def uz_lat_to_cyr(text: str) -> str:
    # заменяем многобуквенные сочетания (регистр-агностично)
    t = text
    for lat, cyr in sorted(_MAP_MULTI.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(re.escape(lat), re.IGNORECASE)
        t = pattern.sub(lambda m: _restore_case(m.group(0), cyr), t)

    # посимвольная замена
    out = []
    for ch in t:
        low = ch.lower()
        if low in _MAP_SINGLE:
            out.append(_restore_case(ch, _MAP_SINGLE[low]))
        else:
            out.append(ch)
    s = "".join(out)

    # пост-правки для отчеств: -ovich/-ovna, o‘g‘li, qizi
    s = re.sub(r"(?i)\b([А-ЯЁа-яё\-]+)\s+o['‘’`ʼ]?g['‘’`ʼ]?li\b", r"\1 оглы", s)
    s = re.sub(r"(?i)\b([А-ЯЁа-яё\-]+)\s+qizi\b", r"\1 кизы", s)
    s = re.sub(r"(?i)ovich\b", "ович", s)
    s = re.sub(r"(?i)ovna\b", "овна", s)

    # нормальный капс по словам
    s = " ".join(w[:1].upper() + w[1:] if w else w for w in s.split())
    return s
