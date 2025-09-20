# secondary_ocr.py
# Tesseract-доборщик: пытается вытащить отчество (GENNADEVNA / O'G'LI / QIZI и пр.)
# из всего изображение или из верхней половины, если надо.

from typing import Optional
from PIL import Image, ImageOps
import pytesseract
import re
import unicodedata

import shutil, os

TESSERACT_BIN = os.getenv("TESSERACT_BIN") or shutil.which("tesseract")
if TESSERACT_BIN:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_BIN


# ===== утилки =====
def _only_letters(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"[^A-Za-zА-Яа-яЁёʼ’' -]+", "", s).strip()


def _norm_up(s: str) -> str:
    s = (s or "").replace("ʼ", "'").replace("’", "'").replace("ʻ", "'")
    return unicodedata.normalize("NFC", s).upper()


# RU суффиксы и UZ (o‘g‘li / qizi)
RX_PATRONYMIC_RU = re.compile(
    r"\b([A-Z'’`-]{3,}?(?:OVICH|EVICH|YEVICH|OVNA|EVNA|YEVNA))\b", re.I
)
RX_PATRONYMIC_UZ = re.compile(r"\b([A-Z'’`-]{3,}?(?:O['’`]G?LI|UGLI|QIZI))\b", re.I)


def _find_patronymic(text: str) -> Optional[str]:
    for rx in (RX_PATRONYMIC_RU, RX_PATRONYMIC_UZ):
        m = rx.search(text)
        if m:
            return _only_letters(m.group(1)).upper()
    return None


def _ocr_text(im: Image.Image) -> str:
    # лёгкая нормализация + OCR
    gray = ImageOps.exif_transpose(im).convert("L")
    gray = gray.point(lambda p: min(255, int(p * 1.18)))  # чуть контраста
    # eng+rus+uzb — самое полезное комбо
    return pytesseract.image_to_string(
        gray, lang="eng+rus+uzb", config="--oem 3 --psm 6"
    )


# ===== публичные функции =====
def tesseract_patronymic_full(img_path: str) -> Optional[str]:
    """OCR всей страницы и поиск отчества по суффиксам."""
    try:
        with Image.open(img_path) as im:
            txt = _ocr_text(im)
        return _find_patronymic(txt)
    except Exception:
        return None


def tesseract_patronymic_top(img_path: str) -> Optional[str]:
    """OCR верхней половины страницы (там обычно «OTASINING ISMI»)."""
    try:
        with Image.open(img_path) as im:
            w, h = im.size
            top = im.crop((0, 0, w, h // 2 + 30))
            txt = _ocr_text(top)
        return _find_patronymic(txt)
    except Exception:
        return None


def tesseract_patronymic(img_path: str) -> Optional[str]:
    """
    Комбо-режим: сначала верх, если не нашли — вся страница.
    Возвращает отчество ВЕРХНИМ РЕГИСТРОМ или None.
    """
    return tesseract_patronymic_top(img_path) or tesseract_patronymic_full(img_path)
