# docBot/ocr/service.py

from dataclasses import dataclass
from typing import Dict, List

from ocr.preprocess import enhance_save_variants
from ocr.yandex_vision import ocr_best
from ocr.secondary_ocr import tesseract_patronymic
from ocr.parsing.registry import get_parser
from ocr.models.doc_types import DocType
from ocr.models.canonical import CanonicalDoc
from ocr.services.translit import uz_lat_to_cyr


import os
import re

@dataclass
class OcrResult:
    passport_data: Dict[str, str]
    engine_report: str


class OcrError(Exception):
    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


class PassbotOcrService:
    """
    Адаптер для docBot:
    - принимает путь к изображению
    - прогоняет через OCR (Yandex Vision)
    - парсит паспорт (UZ/RU) через CompositePassportParser
    - возвращает dict passport_data для FSM
    """

    async def process_passport(self, image_path: str) -> OcrResult:
        # 1) Препроцессинг
        variants_dir = os.path.join(os.path.dirname(image_path), "variants")
        os.makedirs(variants_dir, exist_ok=True)
        variants = enhance_save_variants(image_path, out_dir=variants_dir)

        # 2) OCR
        raw = ocr_best(variants)  # dict: {text, entities, variant_path, engine_report}
        full_text: str = raw.get("text") or ""
        entities: List[dict] = raw.get("entities") or []
        lines: List[str] = [ln for ln in full_text.splitlines() if ln.strip()]
        engine_items: List[Dict] = raw.get("engine_report") or []
        engine_report = self._format_engine_report(engine_items)

        if not full_text.strip():
            raise OcrError("Текст не распознан")

        # 3) Парсинг
        parser = get_parser(DocType.PASSPORT)
        model = parser.parse(lines, full_text, entities)
        if not model:
            raise OcrError("Не удалось надёжно распознать паспорт")

        # 4) Добор отчества через secondary_ocr (если надо)
        if not getattr(model, "patronymic", None) and raw.get("variant_path"):
            mid = tesseract_patronymic(raw["variant_path"])
            if mid:
                model.patronymic = mid

        # 5) Канонизация
        canon: CanonicalDoc = model.to_canonical()

        # 6) Приведение к passport_data
        pd = self._to_passport_data(canon)

        return OcrResult(passport_data=pd, engine_report=engine_report)

    def _format_engine_report(self, items: List[Dict]) -> str:
        if not items:
            return "нет отчёта"
        return "\n".join(
            f"• {it.get('engine','?')}: {it.get('len',0)} символов ({it.get('variant','?')})"
            for it in items
        )

    # ───────────────────── ФИО: приводим к «Фамилия Имя Отчество» ─────────────────────
    def _normalize_fullname_fio(self, doc) -> str:
        """
        Порядок полей:
        1) если парсер дал готовое fio_cyr → берём его
        2) если есть surname/name/patronymic в extras → склеиваем 'Ф И О'
        3) иначе пытаемся переупорядочить из одной строки (И О Ф → Ф И О)
        """
        ex = (getattr(doc, "extras", None) or {})
        fio_cyr = ex.get("fio_cyr")
        if fio_cyr:
            return fio_cyr.strip()

        sur = ex.get("surname") or ""
        nam = ex.get("name") or ""
        pat = ex.get("patronymic") or ""
        parts = [p for p in [sur, nam, pat] if p]
        if parts:
            return " ".join(parts)

        # fallback: пытаемся распознать порядок в плоской строке
        base = (getattr(doc, "person_fullname", "") or "").strip()
        if not base:
            return ""

        # если это «Имя Отчество Фамилия» (как часто даёт MRZ/латиница), развернём в «Фамилия Имя Отчество»
        tokens = re.findall(r"[A-Za-zА-Яа-яЁё’'`ʻʼ-]+", base)
        if len(tokens) == 3:
            i, o, f = tokens[0], tokens[1], tokens[2]
            fio = f"{f} {i} {o}"
        elif len(tokens) == 2:
            i, f = tokens[0], tokens[1]
            fio = f"{f} {i}"
        else:
            fio = base

        fio = fio.strip()
        if fio:
            fio = uz_lat_to_cyr(fio)
        return fio

    # ───────────────────── Кем выдан: UZ → RU нормализация ─────────────────────
    def _normalize_issuer_uz_to_ru(self, issuer_raw: str) -> str:
        """
        Примеры:
        'TOSHKENT SHAHAR MIRZO-ULUG'BEK TUMANI IIB'
          → 'ГУ МВД Узбекистана, г. Ташкент, Мирзо-Улугбекский р-н'
        Работает токенами, не ломает прочий текст.
        """
        if not issuer_raw:
            return ""

        s = issuer_raw.upper()

        # Базовые замены по структуре
        s = s.replace("IIB", "ГУ МВД УЗБЕКИСТАНА")  # Ichki Ishlar Bo'limi → МВД Узбекистана
        s = s.replace("IIV", "ГУ МВД УЗБЕКИСТАНА")  # иногда пишут IIV

        # Гео-токены
        repl = {
            "TOSHKENT": "Ташкент",
            "TASHKENT": "Ташкент",
            "SAMARQAND": "Самарканд",
            "BUXORO": "Бухара",
            "NAMANGAN": "Наманган",
            "ANDIJON": "Андижан",
            "FARG'ONA": "Фергана",
            "QASHQADARYO": "Кашкадарья",
            "SURXONDARYO": "Сурхандарья",
            "XORAZM": "Хорезм",
            "NAVOIY": "Навои",
            "QORAQALPOG'ISTON": "Каракалпакстан",
            "QORAQALPOGISTON": "Каракалпакстан",
            "SIRDARYO": "Сырдарья",
            "JIZZAX": "Джизак",
        }
        for k, v in repl.items():
            s = re.sub(rf"\b{k}\b", v, s)

        # Адм. единицы
        s = s.replace("SHAHAR", "г.")
        s = s.replace("TUMANI", "р-н")
        s = s.replace("TUMAN", "р-н")

        # Районы Ташкента (несколько частых)
        s = s.replace("MIRZO-ULUG'BEK", "Мирзо-Улугбекский")
        s = s.replace("YAKKASAROY", "Яккасарайский")
        s = s.replace("CHILONZOR", "Чиланзарский")
        s = s.replace("MIROBOD", "Мирабадский")
        s = s.replace("SHAIKHONTOKHUR", "Шайхантахурский")
        s = s.replace("SERGELI", "Сергелийский")
        s = s.replace("UCHTEPA", "Учтепинский")
        s = s.replace("BEKTEMIR", "Бектемирский")
        s = s.replace("YUNUSOBOD", "Юнусабадский")
        s = s.replace("OLMAZOR", "Алмазарский")

        # Почистим пробелы и дефисы
        s = re.sub(r"\s+", " ", s).strip()

        # Форматируем: «ГУ МВД Узбекистана, г. Ташкент, Мирзо-Улугбекский р-н»
        # Если нет запятых – проставим их красиво.
        # Разделим на ведомство + гео + район по шаблону
        parts = []
        # ведомство
        if "ГУ МВД УЗБЕКИСТАНА" in s:
            parts.append("ГУ МВД Узбекистана")
            s = s.replace("ГУ МВД УЗБЕКИСТАНА", "").strip(",;: ")
        # Остальное: уже преобразованные гео-токены/адм.ед.
        s = s.replace(" ,", ",").strip(",;: ")
        if s:
            parts.append(s)

        return ", ".join(parts)

    def _to_passport_data(self, doc: CanonicalDoc) -> Dict[str, str]:
        series = (doc.extras or {}).get("series") or ""
        number = (doc.extras or {}).get("number") or ""
        doc_id = (f"{series} {number}".strip() if (series or number) else (doc.doc_id or "")).strip()

        full_name = self._normalize_fullname_fio(doc)
        issuer_ru = self._normalize_issuer_uz_to_ru(doc.issuer or "")

        # гражданство: если парсер вернул ISO/краткое — приведём к понятному виду
        nationality = (doc.extras or {}).get("nationality") or ""
        if nationality.upper() in {"RUS", "RU", "RUSSIA", "РОССИЯ"}:
            nationality = "Россия"
        elif nationality.upper() in {"UZB", "UZ", "UZBEKISTAN"}:
            nationality = "Узбекистан"

        return {
            "full_name": full_name,  # ← теперь ФИО
            "birth_date": doc.birth_date or "",
            "citizenship": nationality,
            "passport_serial_number": doc_id,
            "passport_issue_date": doc.issue_date or "",
            "passport_expiry_date": doc.expiry_date or "",
            "passport_issue_place": issuer_ru,  # ← нормализуем «кем выдан»
            "doc_id": doc_id,
        }

