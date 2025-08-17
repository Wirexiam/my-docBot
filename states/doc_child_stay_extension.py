from aiogram.fsm.state import State, StatesGroup


class DocChildStayExtensionStates(StatesGroup):
    """States for stamp transfer process"""

    waiting_confirm_doc_child_stay_extension_start = State()
    after_select_mvd = State()
    after_parent_passport = State()
    after_adress = State()
    after_child_passport = State()
    child_cannot_leave = State()
    after_phone_number = State()
    extend_child_stay = State()

    data_editor = State()
    edit_fields = State()


