# app/parsing/registry.py
from typing import Optional, List
from ocr.models.doc_types import DocType
from ocr.parsing.passport_parser import PassportUZParser
from ocr.parsing.passport_rus import PassportRUSParser


class CompositePassportParser:
    def __init__(self):
        self.uz = PassportUZParser()
        self.ru = PassportRUSParser()

    def parse(self, lines: List[str], full_text: str, entities: list):
        # 1) если в тексте явно UZB/UZBEKISTAN — сначала UZ
        t_up = (full_text or "").upper()
        prefer_uz = "UZB" in t_up or "UZBEK" in t_up
        order = (self.uz, self.ru) if prefer_uz else (self.ru, self.uz)

        best = None
        for p in order:
            try:
                m = p.parse(lines, full_text, entities)
                if m and (m.surname and m.name):
                    # простой скоринг: есть серия/номер/issuer → прибавим очков
                    score = 0
                    if m.series and m.number: score += 2
                    if m.issued_by: score += 1
                    if m.expiry_date: score += 1
                    if not best or score > best[0]:
                        best = (score, m)
            except Exception:
                continue
        return best[1] if best else None

_registry = {
    DocType.PASSPORT: CompositePassportParser(),
}

def get_parser(doc_type: DocType):
    return _registry.get(doc_type)
