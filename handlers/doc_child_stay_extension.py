from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFileUnion
from aiogram.types import FSInputFile

from handlers.components.live_adress import handle_live_adress_input
from handlers.components.residence_reason_patent import func_residence_reason_patent
from keyboards.components.child_data import get_child_data_start_keyboard
from keyboards.registration_renewal import (
    get_registration_renewal_after_residence_reason_and_location_keyboard,
)
from pdf_generator.gen_pdf import create_user_doc
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from states.doc_child_stay_extension import DocChildStayExtensionStates
from states.components.passport_manual import PassportManualStates
from states.components.select_region_and_mvd import SelectRegionStates
from keyboards.doc_child_stay_extension import (
    get_doc_child_stay_extension_related_child_keyboard,
    get_doc_child_stay_extension_start_keyboard,
    get_doc_child_stay_extension_passport_start_keyboard, get_main_editor_keyboard, subkeyboard, get_doc_child_accept_data
)

from localization import _
from data_manager import SecureDataManager

doc_child_stay_extension_router = Router()
data_manager = SecureDataManager()

import logging

logger = logging.getLogger(__name__)

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
        # passport_data["passport_issue_place"] = state_data["passport_issue_place"]
        passport_data["passport_issue_place"] = passport_data["passport_issue_place"]
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
    logger.info(f"data in handle_child_data 1:{state_data}")
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

    patient_data = state_data.get("patient_data", {})

    if "patient_data.patient_issue_place" in state_data:
        patient_data["patient_issue_place"] = state_data["patient_data.patient_issue_place"]
        await state.update_data(patient_data=patient_data)

    user_data = {
        waiting_data: message.text.strip(),
    }
    await state.update_data({waiting_data: message.text.strip()})
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await state.set_state(DocChildStayExtensionStates.extend_child_stay)
    text = f"{_.get_text('extend_child_stay.title', lang)}\n{_.get_text('extend_child_stay.description', lang)}"
    await message.answer(text=text)
    logger.info(f"data in handle_child_data:{state_data}")


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
    # pprint(data)

    logger.info(data)
    child_data = (
        [
            f"{_.get_text('child_stay_extension.child_passport.full_name', lang)}{data['child_data']['full_name']}",
            f"{_.get_text('child_stay_extension.child_passport.citizenship', lang)}{data['child_data']['citizenship']}",
            f"{_.get_text('child_stay_extension.child_passport.document', lang)}{data['child_data']['passport_serial_number']}",
            f"{_.get_text('child_stay_extension.child_passport.issue_info', lang)}{data['child_data']['passport_issue_date']}, {data['child_data']['passport_data.passport_issue_place']}",
            f"{_.get_text('child_stay_extension.child_passport.expiry_date', lang)}{data['child_data']['passport_expiry_date']}\n",
        ]
        if "passport_expiry_date" in data["child_data"].keys()
        else [
            f"{_.get_text('child_stay_extension.child_birth_cert.full_name', lang)}{data['child_data']['full_name']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.birth_date', lang)}{data['child_data']['birth_date']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.citizenship', lang)}{data['child_data']['citizenship']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.document', lang)}",
            f"{_.get_text('child_stay_extension.child_birth_cert.document_number', lang)}{data['child_data']['passport_serial_number']}",
            f"{_.get_text('child_stay_extension.child_birth_cert.issue_info', lang)}{data['child_data']['passport_issue_date']}, {data['child_data']['passport_data.passport_issue_place']}\n",
        ]
    )

    patient_data = data.get("patient_data", {})
    message_lines = [
        _.get_text("child_stay_extension.title", lang),
        _.get_text("child_stay_extension.mother_related", lang),
        f"{_.get_text('child_stay_extension.mother_full_name', lang)}{data['parent_passport_data']['full_name']}",
        f"{_.get_text('child_stay_extension.mother_citizenship', lang)}{data['parent_passport_data']['citizenship']}",
        f"{_.get_text('child_stay_extension.mother_document', lang)}{data['parent_passport_data']['passport_serial_number']}",
        f"{_.get_text('child_stay_extension.mother_issue_info', lang)}{data['parent_passport_data']['passport_issue_date']}, {data['parent_passport_data']['passport_issue_place']}",
        f"{_.get_text('child_stay_extension.mother_expiry_date', lang)}{data['parent_passport_data']['passport_expiry_date']}\n",
        _.get_text("child_stay_extension.basis_section", lang),
        f"{_.get_text('child_stay_extension.basis_patient', lang)}{patient_data['patient_number']}",
        f"{_.get_text('child_stay_extension.basis_issue_date', lang)}{patient_data['patient_date']}",
        f"{_.get_text('child_stay_extension.basis_issue_place', lang)}{patient_data['patient_issue_place']}\n",
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
        reply_markup=get_doc_child_accept_data(lang)
    )

@doc_child_stay_extension_router.callback_query(F.data=="child_stay_accept")
async def child_get_pdf(query: CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки Верно"""

    state_data = await state.get_data()
    lang = state_data.get("language")
    parent = None

    if state_data.get('related_child', '') == "father":
        parent = "Отец"
    elif state_data.get('related_child', '') == "mother":
        parent = "Мать"
    else:
        parent = "Опекун"

    data = {
        'extend_child_stay_date': state_data.get("extend_child_stay_date", ''),
        'child_fio': state_data.get('child_data', '').get('full_name', ''),
        'child_ship': state_data.get('child_data', '').get('citizenship', ''),
        'child_date_birth': state_data.get('child_data', '').get('birth_date', ''),
        'child_passport_serial_number': state_data.get('child_data', '').get('passport_serial_number', ''),
        'child_passport_when_give': state_data.get('child_data', '').get('passport_issue_date', ''),
        'child_passport_who_where_give': state_data.get('child_data', '').get('passport_data.passport_issue_place', ''),
        'child_parent': parent,
        'patient_number': state_data.get('patient_data').get('patient_number', ''),
        'patient_date': state_data.get('patient_data').get('patient_date', ''),
        'live_adress': state_data.get('live_adress', ''),
        'reason': state_data.get('child_cannot_leave_cause', ''),
        'mvd_adress': state_data.get('mvd_adress', ''),
        'fio_parent': state_data.get('parent_passport_data', '').get('full_name', ''),
        'birth_data_parent': state_data.get('parent_passport_data', '').get('birth_date', ''),
        'citizenship_parent': state_data.get('parent_passport_data', '').get('citizenship', ''),
        'serial_number_parent': state_data.get('parent_passport_data', '').get('passport_serial_number', ''),
        'passport_issue_date_parent': state_data.get('parent_passport_data', '').get('passport_issue_date', ''),
        'passport_issue_place_parent': state_data.get('parent_passport_data', '').get('passport_issue_place', ''),
        'phone_parent': state_data.get('phone_number', ''),
        }
    
    doc = create_user_doc(context=data, template_name='template_patient_actual', user_path='pdf_generator')

    
    ready_doc = FSInputFile(doc, filename='document.pdf')
    await query.message.answer_document(
        document=ready_doc
    )


@doc_child_stay_extension_router.callback_query(F.data=="child_stay_data_edit")
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

    if query_data == "back_to_child_stay":
        await state.set_state(None)
        await query.message.delete()
        await handle_child_data(query.message, state)
        await query.message.delete()
        return

    if query_data in ["mother_related", "basis_section", "child_section", "address_section", "extend_section", "mvd_section", "phone_number_text"]:
        text = _.get_text("change_menu.title", lang)
        if query_data.startswith("basis_"):
            postfix = ["basis_issue_date", "basis_issue_place", "basis_patient"]
            await query.message.edit_text(
                text=text,
                reply_markup=subkeyboard(postfix, lang)
            )

        if query_data.startswith("mother_"):
            postfix = ["mother_full_name", "mother_citizenship", "mother_document", "mother_issue_info", "mother_expiry_date", "mother_issue_date"]
            await query.message.edit_text(
                text=text,
                reply_markup=subkeyboard(postfix, lang)
            )

        if query_data.startswith("child_"):
            child_fields = (
                [
                    "child_full_name",
                    "child_citizenship",
                    "child_document",
                    "child_issue_info",
                    "child_expiry_date",
                ]
                if "passport_expiry_date" in state_data["child_data"]
                else [
                    "child_full_name",
                    "child_birth_date",
                    "child_citizenship",
                    "child_document",
                    "child_document_number",
                    "child_issue_info",
                ]
            )
            await query.message.edit_text(
                text=text,
                reply_markup=subkeyboard(child_fields, lang)
            )


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


@doc_child_stay_extension_router.callback_query(F.data.startswith("cs_sub_editor_"))
async def sub_editor(query: CallbackQuery, state: FSMContext):

    state_data = await state.get_data()
    lang = state_data.get("language")


    query_data = query.data.removeprefix("cs_sub_editor_")

    if query_data == "back":
        await query.answer()
        await child_stay_editor(query, state)
        return

    if query_data.startswith("mother_"):
        data = query_data.removeprefix("mother_")
        fields_info = {
            "full_name": {
                "text": f"{_.get_text("stamp_transfer_start_new_passport.description", lang)}",
                "field": "full_name"
            },
            "citizenship": {
                "text": (
                    f"{_.get_text('passport_manual_citizenship.title', lang)}\n\n"
                    f"{_.get_text('passport_manual_citizenship.example_text', lang)}"
                ),
                "field": "citizenship"
            },
            "document": {
                "text": f"{_.get_text("passport_manual_serial_input.title", lang)}\n\n{_.get_text("passport_manual_serial_input.example_text", lang)}",
                "field": "passport_serial_number"
            },
            "expiry_date": {
                "text": (
                    f"{_.get_text('passport_manual_expire_date.title', lang)}\n\n"
                    f"{_.get_text('passport_manual_expire_date.example_text', lang)}"
                ),
                "field": "passport_expiry_date"
            },
            "issue_info": {
                "text": (
                    f"{_.get_text('passport_manual_issue_place.title', lang)}\n\n"
                    f"{_.get_text('passport_manual_issue_place.example_text', lang)}"
                ),
                "field": "passport_issue_place"
            },
            "issue_date": {
                "text": f"{_.get_text("passport_manual_issue_date.title", lang)}\n\n{_.get_text("passport_manual_issue_date.example_text", lang)}",
                "field": "passport_issue_date"
            }
        }
        if data in fields_info:
            await state.update_data(dict="parent_passport_data")
            await state.update_data(field=fields_info[data]["field"])
            await query.message.edit_text(text=fields_info[data]["text"])
            await state.set_state(DocChildStayExtensionStates.edit_fields)

    if query_data.startswith("basis_"):
        data = query_data.removeprefix("basis_")

        fields_info = {
            "patient": {
                "text": f"{_.get_text("residence_reason_manual_patient_messages.patient_number.title", lang)}\n\n{_.get_text("residence_reason_manual_patient_messages.patient_number.example_text", lang)}",
                "field": "patient_number"
            },
            "issue_date": {
                "text": f"{_.get_text("residence_reason_manual_patient_messages.patient_date.title", lang)}\n\n{_.get_text("residence_reason_manual_patient_messages.patient_date.example_text", lang)}",
                "field": "patient_date"
            },
            "issue_place": {
                "text": f"{_.get_text("residence_reason_manual_patient_messages.patient_issue_place.title", lang)}\n\n{_.get_text("residence_reason_manual_patient_messages.patient_issue_place.example_text", lang)}",
                "field": "patient_issue_place"
            }
        }

        if data in fields_info:
            await state.update_data(dict="patient_data")
            await state.update_data(field=fields_info[data]["field"])
            await query.message.edit_text(text=fields_info[data]["text"])
            await state.set_state(DocChildStayExtensionStates.edit_fields)


    if query_data.startswith("child_"):
        data = query_data.removeprefix("child_")


        fields_info = {
            "full_name": {
                "text": f"{_.get_text("stamp_transfer_start_new_passport.description", lang)}",
                "field": "full_name"
            },
            "citizenship": {
                "text": (
                    f"{_.get_text('passport_manual_citizenship.title', lang)}\n\n"
                    f"{_.get_text('passport_manual_citizenship.example_text', lang)}"
                ),
                "field": "citizenship"
            },
            "document": {
                "text": f"{_.get_text("passport_manual_serial_input.title", lang)}\n\n{_.get_text("passport_manual_serial_input.example_text", lang)}",
                "field": "passport_serial_number"
            },
            "expiry_date": {
                "text": (
                    f"{_.get_text('passport_manual_expire_date.title', lang)}\n\n"
                    f"{_.get_text('passport_manual_expire_date.example_text', lang)}"
                ),
                "field": "passport_expiry_date"
            },
            "birth_date": {
                "text": f"{_.get_text("residence_reason_manual_child_messages.child_birth_date.title", lang)}\n{_.get_text("residence_reason_manual_child_messages.child_birth_date.example_text", lang)}"

            },
            "issue_info": {
                "text": (
                    f"{_.get_text('passport_manual_issue_place.title', lang)}\n\n"
                    f"{_.get_text('passport_manual_issue_place.example_text', lang)}"
                ),
                "field": "passport_data.passport_issue_place"
            }
        }

        if data in fields_info:
            await state.update_data(dict="child_data")
            await state.update_data(field=fields_info[data]["field"])
            await query.message.edit_text(text=fields_info[data]["text"])
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

    await state.update_data(field=None)
    await state.update_data(dict=None)

    await handle_child_data(message, state)

    # parent_passport_data 
    # child_data