# app/models/doc_types.py
from enum import Enum

class DocType(str, Enum):
    PASSPORT = "passport"
    VNZH_RESIDENCE_NOTICE = "vnzh_residence_notice"
    MIG_ARRIVAL_NOTICE = "mig_arrival_notice"
    WORK_PATENT_NOTICE = "work_patent_notice"
    EXTEND_STAY_FAMILY = "extend_stay_family_patent"
    EXTEND_STAY_CHILD = "extend_stay_child_patent"
    VNZH_STAMP_MOVE_APP = "vnzh_stamp_move_application"
