from typing import Dict, Optional
from pydantic import BaseModel, Field
from .doc_types import DocType


class CanonicalDoc(BaseModel):
    doc_type: DocType
    person_fullname: Optional[str] = None
    person_surname: Optional[str] = None
    person_name: Optional[str] = None
    person_patronymic: Optional[str] = None
    birth_date: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    issuer: Optional[str] = None
    doc_id: Optional[str] = None
    extras: Dict[str, str] = Field(default_factory=dict)
