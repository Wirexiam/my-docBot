from typing import Optional
from pydantic import BaseModel, constr
from .canonical import CanonicalDoc
from .doc_types import DocType

class PassportUZ(BaseModel):
    surname: constr(strip_whitespace=True, min_length=1)
    name: constr(strip_whitespace=True, min_length=1)
    patronymic: Optional[str] = None
    birth_date: constr(strip_whitespace=True)               # "DD.MM.YYYY"
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    issued_by: Optional[str] = None
    number: Optional[str] = None
    series: Optional[str] = None
    nationality: Optional[str] = None
    sex: Optional[str] = None
    place_of_birth: Optional[str] = None

    def to_canonical(self) -> CanonicalDoc:
        fio = " ".join([p for p in [self.name, self.patronymic, self.surname] if p])
        return CanonicalDoc(
            doc_type=DocType.PASSPORT,
            person_fullname=fio,
            person_surname=self.surname,
            person_name=self.name,
            person_patronymic=self.patronymic,
            birth_date=self.birth_date,
            issue_date=self.issue_date,
            expiry_date=self.expiry_date,
            issuer=self.issued_by,
            doc_id=((self.series or "") + (self.number or "")) or None,
            extras={
                "nationality": self.nationality or "",
                "sex": self.sex or "",
                "place_of_birth": self.place_of_birth or "",
            }
        )
