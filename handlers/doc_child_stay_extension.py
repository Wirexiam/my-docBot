from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from handlers.components.live_adress import handle_live_adress_input
from handlers.components.residence_reason_patent import func_residence_reason_patent
from keyboards.components.child_data import get_child_data_start_keyboard
from keyboards.registration_renewal import (
    get_registration_renewal_after_residence_reason_and_location_keyboard,
)
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from states.doc_child_stay_extension import DocChildStayExtensionStates
from states.components.passport_manual import PassportManualStates
from states.components.select_region_and_mvd import SelectRegionStates
from keyboards.doc_child_stay_extension import (
    get_doc_child_stay_extension_related_child_keyboard,
    get_doc_child_stay_extension_start_keyboard,
    get_doc_child_stay_extension_passport_start_keyboard, get_main_editor_keyboard, subkeyboard
)

from localization import _
from data_manager import SecureDataManager

doc_child_stay_extension_router = Router()
data_manager = SecureDataManager()


@doc_child_stay_extension_router.callback_query(F.data == "doc_child_stay_extension")
async def handle_doc_child_stay_extension_start(
    callback: CallbackQuery, state: FSMContext
):
    """Обработка нажатия кнопки начала процесса продления пребывания ребёнка (по патенту матери)"""

    # Установка состояния для начала процесса продления регистрации
    await state.set_state(
        DocChildStayExtensionStates.waiting_confirm_doc_child_stay_extension_start
    )
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="doc_child_stay_extension_after_mvd")
    # Отправка сообщения с инструкциями
    text = f"{_.get_text('doc_child_stay_extension_start.title', lang)}\n{_.get_text('doc_child_stay_extension_start.description', lang)}\n{_.get_text('doc_child_stay_extension_start.documents_to_prepare', lang)}"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_doc_child_stay_extension_start_keyboard(lang),
    )


@doc_child_stay_extension_router.callback_query(
    F.data == "doc_child_stay_extension_after_mvd"
)
async def handle_doc_child_stay_extension_after_mvd(
    callback: CallbackQuery, state: FSMContext
):
    """загрузка mvd_adress"""

    await state.set_state(DocChildStayExtensionStates.after_select_mvd)
    state_data = await state.get_data()
    lang = state_data["language"]
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")
    user_data = {
        "mvd_adress": mvd_adress,
    }
    data_manager.save_user_data(callback.from_user.id, session_id, user_data)

    text = f"{_.get_text('how_you_are_related_to_the_child.title', lang)}"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_doc_child_stay_extension_related_child_keyboard(lang),
    )


@doc_child_stay_extension_router.callback_query(
    DocChildStayExtensionStates.after_select_mvd
)
async def handle_doc_child_stay_extension_related_child(
    callback: CallbackQuery, state: FSMContext
):
    """загрузка 'кто вы ребёнку'"""
    state_data = await state.get_data()
    lang = state_data["language"]

    session_id = state_data.get("session_id")
    user_data = {
        "related_child": callback.data,
    }
    await state.update_data(**user_data)
    data_manager.save_user_data(callback.from_user.id, session_id, user_data)

    await state.update_data(
        from_action=DocChildStayExtensionStates.after_parent_passport,
        passport_title="registration_renewal_passport_title",
    )

    text = f"{_.get_text('registration_renewal_start_passport.title', lang)}\n{_.get_text('registration_renewal_start_passport.description', lang)}"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_doc_child_stay_extension_passport_start_keyboard(lang),
    )


@doc_child_stay_extension_router.message(
    DocChildStayExtensionStates.after_parent_passport
)
async def handle_live_adress_data(message: Message, state: FSMContext):
    """Запрос адреса"""

    await state.update_data(from_action=DocChildStayExtensionStates.after_adress)
    await state.update_data(passport_title="doc_child_stay_extension_passport_title")
    await handle_live_adress_input(message, state)


@doc_child_stay_extension_router.message(DocChildStayExtensionStates.after_adress)
async def handle_old_passport_data(message: Message, state: FSMContext):
    """Обработка начала передачи паспорта после выбора МВД и адреса"""
    state_data = await state.get_data()
    lang = state_data["language"]

    passport_data = state_data.get("passport_data", {})
    if "parent_passport_data" not in state_data.keys():
        passport_data["passport_issue_place"] = state_data["passport_issue_place"]
        parent_passport_data = passport_data

        print(parent_passport_data)
        passport_data = {}
        print(parent_passport_data)
        await state.update_data(passport_data=passport_data)
        user_data = {
            "passport_data": passport_data,
        }
        session_id = state_data.get("session_id")

        data_manager.save_user_data(message.from_user.id, session_id, user_data)
        user_data = {
            "parent_passport_data": parent_passport_data,
        }
        await state.update_data(parent_passport_data=parent_passport_data)
        data_manager.save_user_data(message.from_user.id, session_id, user_data)

        waiting_data = state_data.get("waiting_data", None)
        user_data = {
            waiting_data: message.text.strip(),
        }
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await state.update_data(
        from_action=DocChildStayExtensionStates.after_child_passport
    )
    text = f"{_.get_text("doc_child_stay_extension_child_data.message_0.title", lang)}"
    await message.answer(text, reply_markup=get_child_data_start_keyboard(lang))


@doc_child_stay_extension_router.message(
    DocChildStayExtensionStates.after_child_passport
)
async def handle_child_data(message: Message, state: FSMContext):
    """Обработка ввода данных нового паспорта ребёнка"""
    state_data = await state.get_data()
    await state.set_state(DocChildStayExtensionStates.child_cannot_leave)

    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)

    passport_data = state_data.get("passport_data")
    passport_data[waiting_data] = message.text.strip()

    child_data = passport_data
    passport_data = {}
    await state.update_data(passport_data=passport_data)
    user_data = {
        "passport_data": passport_data,
    }
    session_id = state_data.get("session_id")
    data_manager.save_user_data(message.from_user.id, session_id, user_data)
    user_data = {
        "child_data": child_data,
    }
    await state.update_data(child_data=child_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('doc_child_stay_extension_child_data.message_3.title', lang)}\n{_.get_text('doc_child_stay_extension_child_data.message_3.description', lang)}"
    await message.answer(text=text)


@doc_child_stay_extension_router.message(DocChildStayExtensionStates.child_cannot_leave)
async def handle_child_data(message: Message, state: FSMContext):
    """Обработка ввода данных нового паспорта ребёнка"""
    state_data = await state.get_data()

    session_id = state_data.get("session_id")
    user_data = {
        "child_cannot_leave_cause": message.text.strip(),
    }
    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await state.update_data(
        from_action=DocChildStayExtensionStates.after_phone_number,
        next_states=[PhoneNumberStates.phone_number_input],
    )
    await func_residence_reason_patent(
        message, state, "patent_mother_start_msg.description"
    )


@doc_child_stay_extension_router.message(DocChildStayExtensionStates.after_phone_number)
async def handle_child_data(message: Message, state: FSMContext):
    """Обработка ввода данных нового паспорта ребёнка"""
    state_data = await state.get_data()
    lang = state_data.get("language")
    waiting_data = state_data.get("waiting_data", None)
    # Сохранение адреса в менеджер данных
    session_id = state_data.get("session_id")
    user_data = {
        waiting_data: message.text.strip(),
    }
    await state.update_data({waiting_data: message.text.strip()})
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await state.set_state(DocChildStayExtensionStates.extend_child_stay)
    text = f"{_.get_text('extend_child_stay.title', lang)}\n{_.get_text('extend_child_stay.description', lang)}"
    await message.answer(text=text)


@doc_child_stay_extension_router.message(DocChildStayExtensionStates.extend_child_stay)
async def handle_child_data(message: Message, state: FSMContext):
    """Обработка ввода данных нового паспорта ребёнка"""
    state_data = await state.get_data()
    lang = state_data.get("language")
    waiting_data = "extend_child_stay_date"

    current_state = await state.get_state()
    if current_state == DocChildStayExtensionStates.extend_child_stay.state:
        # Сохранение адреса в менеджер данных
        session_id = state_data.get("session_id")
        user_data = {
            waiting_data: message.text.strip(),
        }
        await state.update_data(**user_data)
        data_manager.save_user_data(message.from_user.id, session_id, user_data)

    data = await state.get_data()
    pprint(data)
    child_data = (
        [
            f"{_.get_text('child_stay_extension.child_passport.full_name', lang)}{data['child_data']['full_name']}",
            f"{_.get_text('child_stay_extension.child_passport.citizenship', lang)}{data['child_data']['citizenship']}",
            f"{_.get_text('child_stay_extension.child_passport.document', lang)}{data['child_data']['passport_serial_number']}",
            f"{_.get_text('child_stay_extension.child_passport.issue_info', lang)}{data['child_data']['passport_issue_date']}, {data['child_data']['passport_issue_place']}",
            f"{_.get_text('child_stay_extension.child_passport.expiry_date', lang)}{data['child_data']['passport_expiry_date']}\n",
        ]
        if "passport_expiry_date" in data["child_data"].keys()
        else [
            f"{_.get_text('child_stay_extension.child_birth_cert.full_name', lang)}{data['child_data']['full_name']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.birth_date', lang)}{data['child_data']['birth_date']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.citizenship', lang)}{data['child_data']['citizenship']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.document', lang)}",
            f"{_.get_text('child_stay_extension.child_birth_cert.document_number', lang)}{data['child_data']['passport_serial_number']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.issue_info', lang)}{data['child_data']['passport_issue_date']}, {data['child_data']['passport_issue_place']}\n",
        ]
    )

    message_lines = [
        _.get_text("child_stay_extension.title", lang),
        _.get_text("child_stay_extension.mother_related", lang),
        f"{_.get_text('child_stay_extension.mother_full_name', lang)}{data['parent_passport_data']['full_name']}",
        f"{_.get_text('child_stay_extension.mother_citizenship', lang)}{data['parent_passport_data']['citizenship']}",
        f"{_.get_text('child_stay_extension.mother_document', lang)}{data['parent_passport_data']['passport_serial_number']}",
        f"{_.get_text('child_stay_extension.mother_issue_info', lang)}{data['parent_passport_data']['passport_issue_date']}, {data['parent_passport_data']['passport_issue_place']}",
        f"{_.get_text('child_stay_extension.mother_expiry_date', lang)}{data['parent_passport_data']['passport_expiry_date']}\n",
        _.get_text("child_stay_extension.basis_section", lang),
        f"{_.get_text('child_stay_extension.basis_patient', lang)}{data['patient_number']}",
        f"{_.get_text('child_stay_extension.basis_issue_date', lang)}{data['patient_date']}",
        f"{_.get_text('child_stay_extension.basis_issue_place', lang)}{data['patient_issue_place']}\n",
        _.get_text("child_stay_extension.child_section", lang),
        *child_data,
        _.get_text("child_stay_extension.address_section", lang),
        f" {data['live_adress']}\n",
        _.get_text("child_stay_extension.extend_section", lang),
        f" {data['extend_child_stay_date']}\n",
        _.get_text("child_stay_extension.mvd_section", lang),
        f" {data['mvd_adress']}\n",
        _.get_text("phone_number_text", lang),
        f" {data['phone_number']}",
    ]
    
    text = "\n".join(message_lines)
    await message.answer(
        text=text,
        reply_markup=get_registration_renewal_after_residence_reason_and_location_keyboard(
            lang
        ),
    )


@doc_child_stay_extension_router.callback_query(F.data=="registration_renewal_patient_check_data_change")
async def child_stay_editor(query: CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки Изменить"""

    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.set_state(DocChildStayExtensionStates.data_editor)

    text = _.get_text("change_menu.title", lang)

    await query.message.edit_text(
        text=text,
        reply_markup=get_main_editor_keyboard(lang)
    )


@doc_child_stay_extension_router.callback_query(F.data.startswith("cs_editor_"))
async def handler_main_editor(query: CallbackQuery, state: FSMContext):

    state_data = await state.get_data()
    lang = state_data.get("language")

    query_data = query.data.removeprefix("cs_editor_")

    if query_data in ["mother_related", "basis_section", "child_section", "address_section", "extend_section", "mvd_section", "phone_number_text"]:
        text = _.get_text("change_menu.title", lang)
        if query_data.startswith("basis_"):
            postfix = ["basis_issue_date", "basis_issue_place", "basis_patient"]
            await query.message.edit_text(
                text=text,
                reply_markup=subkeyboard(postfix, lang)
            )

        if query_data.startswith("mother_"):
            postfix = ["mother_full_name", "mother_citizenship", "mother_document", "mother_issue_info", "mother_expiry_date"]
            await query.message.edit_text(
                text=text,
                reply_markup=subkeyboard(postfix, lang)
            )

        if query_data.startswith("child_"):
            ...

        if query_data in ["address_section", "extend_section", "mvd_section", "phone_number_text"]:
            if query_data == "address_section":
                text = f"{_.get_text("live_adress.title", lang)}\n\n{_.get_text("live_adress.example", lang)}"
                await query.message.edit_text(
                    text=text, 
                    reply_markup=None
                )
                await state.update_data(field="live_adress")
                await state.set_state(DocChildStayExtensionStates.edit_fields)

            if query_data == "extend_section":
                text = f"{_.get_text("extend_child_stay.title", lang)}\n\n{_.get_text("extend_child_stay.description", lang)}"
                await query.message.edit_text(
                    text=text, 
                )
                await state.update_data(field="extend_child_stay_date")
                await state.set_state(DocChildStayExtensionStates.edit_fields)

            if query_data == "mvd_section":
                text = f"{_.get_text("region_start_msg.title", lang)}\n\n{_.get_text("region_start_msg.description")}"
                await query.message.edit_text(
                    text=text, 
                )
                await state.update_data(field="mvd_adress")
                await state.set_state(DocChildStayExtensionStates.edit_fields)

            if query_data == "phone_number_text":
                text = f"{_.get_text("phone_number.title", lang)}\n\n{_.get_text("phone_number.example_text", lang)}"

                await query.message.edit_text(
                    text=text, 
                )
                await state.update_data(field="phone_number")
                await state.set_state(DocChildStayExtensionStates.edit_fields)


@doc_child_stay_extension_router.message(DocChildStayExtensionStates.edit_fields)
async def edit_fields(message: Message, state: FSMContext):

    state_data = await state.get_data()

    field = state_data.get("field")
    dict_name = state_data.get("dict")

    msg = message.text.strip()

    if dict_name is None:
        await state.update_data({field: msg})
    else:
        target = state_data.get(dict_name, {})
        target[field] = msg
        await state.update_data({dict_name: target})

    await handle_child_data(message, state)

    # parent_passport_data 
    # child_data