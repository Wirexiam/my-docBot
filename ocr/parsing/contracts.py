from typing import Protocol, Optional, List
from ocr.models.canonical import CanonicalDoc

class ParseResult(Protocol):
    def to_canonical(self) -> CanonicalDoc: ...

class Parser(Protocol):
    def parse(self, lines: List[str], full_text: str, entities: list) -> Optional[ParseResult]: ...
