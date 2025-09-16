import base64
import json
import os
import random
import time
from typing import Any, Dict, List, Tuple, Optional

import httpx
from PIL import Image
import pytesseract
import re
import threading

# ---- Глобальный троттлинг OCR ----
_OCR_RPS_LIMIT = float(os.getenv("YC_OCR_RPS", "1"))  # поднимешь, когда Яндекс увеличит квоту
_MIN_INTERVAL = 1.0 / max(_OCR_RPS_LIMIT, 0.0001)

_rate_lock = threading.Lock()
_last_call_ts = 0.0

YC_OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"


# ---------------------- утилиты ----------------------

def _rate_limit_wait():
    """Гарантирует не более N запросов/сек на процесс."""
    global _last_call_ts
    with _rate_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL - (now - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.monotonic()

def _headers() -> Dict[str, str]:
    api_key = os.getenv("YC_VISION_API_KEY")
    folder = os.getenv("YC_FOLDER_ID")
    if not api_key:
        raise RuntimeError("YC_VISION_API_KEY не задан в .env")
    if not folder:
        raise RuntimeError("YC_FOLDER_ID не задан в .env")
    return {
        "Authorization": f"Api-Key {api_key}",
        "x-folder-id": folder,
        "Content-Type": "application/json",
    }

def _req_body(img_bytes: bytes, mime: str, model: Optional[str], langs: List[str]) -> Dict:
    body = {
        "content": base64.b64encode(img_bytes).decode("ascii"),
        "mimeType": mime,
        "languageCodes": langs,
        "folderId": os.getenv("YC_FOLDER_ID"),
    }
    if model:
        body["model"] = model
    return body

def _call(body: Dict, max_tries: int = 6) -> Dict:
    """
    HTTP вызов с троттлингом и ретраями.
    - Не более YC_OCR_RPS запросов в секунду (по умолчанию 1).
    - 429/5xx ретраим с экспоненциальным бэк-оффом и джиттером.
    """
    last_err: Optional[str] = None
    for attempt in range(1, max_tries + 1):
        _rate_limit_wait()
        try:
            with httpx.Client(timeout=60) as client:
                r = client.post(YC_OCR_URL, headers=_headers(), json=body)

            if r.status_code == 200:
                return r.json()

            if r.status_code == 429:
                last_err = f"OCR HTTP 429: {r.text[:400]}"
                backoff = (1.2 ** attempt) + random.uniform(0.2, 0.6)
                time.sleep(backoff)
                continue

            if 500 <= r.status_code < 600:
                last_err = f"OCR HTTP {r.status_code}: {r.text[:400]}"
                backoff = (1.2 ** attempt) + random.uniform(0.2, 0.6)
                time.sleep(backoff)
                continue

            raise RuntimeError(f"OCR HTTP {r.status_code}: {r.text}")

        except httpx.HTTPError as e:
            last_err = f"HTTPError: {e}"
            backoff = (1.2 ** attempt) + random.uniform(0.2, 0.6)
            time.sleep(backoff)

    raise RuntimeError(last_err or "OCR: неизвестная ошибка")

def _find_first_fulltext(node: Any) -> Optional[str]:
    """Рекурсивно найдём первое поле fullText (где бы оно ни лежало)."""
    if isinstance(node, dict):
        if "fullText" in node and isinstance(node["fullText"], str):
            return node["fullText"]
        for v in node.values():
            ft = _find_first_fulltext(v)
            if ft:
                return ft
    elif isinstance(node, list):
        for v in node:
            ft = _find_first_fulltext(v)
            if ft:
                return ft
    return None

def _find_entities(node: Any) -> List[Dict]:
    """Рекурсивно соберём первый встретившийся массив entities."""
    if isinstance(node, dict):
        if "entities" in node and isinstance(node["entities"], list):
            return node["entities"]
        for v in node.values():
            ents = _find_entities(v)
            if ents:
                return ents
    elif isinstance(node, list):
        for v in node:
            ents = _find_entities(v)
            if ents:
                return ents
    return []

def _extract_text_entities(resp: Dict) -> Tuple[str, List[Dict]]:
    """Вытащить fullText и entities из любого слоёного ответа Vision."""
    ta = resp.get("textAnnotation")
    if isinstance(ta, dict):
        ft = ta.get("fullText") or ""
        ents = ta.get("entities") or []
        if ft or ents:
            return ft, ents

    full = _find_first_fulltext(resp) or ""
    ents = _find_entities(resp) or []
    return full, ents

def _reencode_jpeg(img_bytes: bytes, quality: int = 85) -> bytes:
    """Перекодировать JPEG (на случай экзотических маркеров/слишком большого файла)."""
    try:
        import cv2, numpy as np
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return img_bytes
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return buf.tobytes() if ok else img_bytes
    except Exception:
        return img_bytes

def _recognize_safely(img: bytes, model: Optional[str], langs: List[str]) -> Dict:
    """
    1) как есть (langs)
    2) если пусто -> те же настройки, но langs=['*']
    3) если пусто -> без model (общий OCR) + langs
    4) если пусто -> без model + ['*'] + перекодированный JPEG
    Возвращает словарь {'fullText': str, 'entities': list, '_raw': original_json}
    """
    # 1) as-is
    r1 = _call(_req_body(img, "image/jpeg", model, langs))
    full1, ents1 = _extract_text_entities(r1)
    if full1 or ents1:
        return {"fullText": full1, "entities": ents1, "_raw": r1}

    # 2) auto-lang
    r2 = _call(_req_body(img, "image/jpeg", model, ["*"]))
    full2, ents2 = _extract_text_entities(r2)
    if full2 or ents2:
        return {"fullText": full2, "entities": ents2, "_raw": r2}

    # 3) no-model + langs
    r3 = _call(_req_body(img, "image/jpeg", None, langs))
    full3, ents3 = _extract_text_entities(r3)
    if full3 or ents3:
        return {"fullText": full3, "entities": ents3, "_raw": r3}

    # 4) no-model + ['*'] + reencode
    small = _reencode_jpeg(img, 85)
    r4 = _call(_req_body(small, "image/jpeg", None, ["*"]))
    full4, ents4 = _extract_text_entities(r4)
    return {"fullText": full4, "entities": ents4, "_raw": r4}

def _tess_text(path: str) -> str:
    try:
        return pytesseract.image_to_string(
            Image.open(path),
            lang="rus+eng+uzb+kaz",
            config="--oem 3 --psm 6"
        )
    except Exception:
        return ""

def _clean_len(s: str) -> int:
    return len(re.sub(r"[^0-9A-Za-zА-Яа-яЁё\n]+", "", s or ""))

def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# ---------------------- основной выбор «лучшего» варианта ----------------------

def _iter_variants(variants: List[Any]) -> List[Tuple[str, str]]:
    """
    Нормализуем вход: допускаем и ["path", ...], и [("path","tag"), ...].
    Возвращаем список (path, tag).
    """
    out: List[Tuple[str, str]] = []
    for i, v in enumerate(variants):
        if isinstance(v, (list, tuple)):
            if len(v) == 0:
                continue
            p = v[0]
            t = v[1] if len(v) > 1 else f"v{i}"
        elif isinstance(v, str):
            p = v
            # пытаемся сделать осмысленный тег из имени файла
            base = os.path.basename(v)
            t = os.path.splitext(base)[0] or f"v{i}"
        else:
            # неизвестный тип — пропускаем
            continue
        out.append((str(p), str(t)))
    return out

def ocr_best(variants: List[Any]) -> Dict[str, Any]:
    """
    variants: допускаются и ["path", ...], и [("path","tag"), ...]
    Возвращает:
      {
        "text": str,
        "entities": list,
        "variant_path": str,
        "engine_report": [{"engine":"yc-general|yc-passport|tesseract","variant":tag,"len":int}, ...]
      }
    """
    engine_report: List[Dict[str, Any]] = []
    best: Dict[str, Any] = {"text": "", "entities": [], "variant_path": ""}
    best_score = -10**9

    norm_variants = _iter_variants(variants)
    if not norm_variants:
        raise RuntimeError("OCR: список вариантов пуст или некорректен")

    for path, tag in norm_variants:
        img_bytes = _read_bytes(path)

        # 1) Yandex Vision: общий
        j1 = _recognize_safely(img_bytes, None, ["uz", "ru", "en"])
        txt1, ents1 = j1["fullText"], j1["entities"]
        engine_report.append({"engine": "yc-general", "variant": tag, "len": _clean_len(txt1)})

        # 2) Yandex Vision: паспортная модель
        j2 = _recognize_safely(img_bytes, "passport", ["uz", "ru", "en"])
        txt2, ents2 = j2["fullText"], j2["entities"]
        engine_report.append({"engine": "yc-passport", "variant": tag, "len": _clean_len(txt2)})

        txt_yc = txt1 if len(txt1) >= len(txt2) else txt2
        ents   = ents2 or ents1

        # 3) Скоринг по ключам + длина
        score = 0
        for nm in ("surname", "name", "middle_name", "birth_date", "issue_date", "expiration_date"):
            if any(e.get("name") == nm and e.get("text") and e["text"] != "-" for e in (ents2 or [])):
                score += 6
        score += _clean_len(txt_yc) // 200

        # 4) Fallback Tesseract при слабом тексте
        if score < 12 or _clean_len(txt_yc) < 400:
            t = _tess_text(path)
            engine_report.append({"engine": "tesseract", "variant": tag, "len": _clean_len(t)})
            txt_final = t if _clean_len(t) > _clean_len(txt_yc) else txt_yc
        else:
            txt_final = txt_yc

        candidate = {"text": txt_final, "entities": ents, "variant_path": path}
        if score > best_score or _clean_len(txt_final) > _clean_len(best["text"]):
            best, best_score = candidate, score

    if not best["text"] and not best["entities"]:
        raise RuntimeError("OCR: пустой результат")

    best["engine_report"] = engine_report
    return best
