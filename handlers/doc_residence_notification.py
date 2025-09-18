from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.filters import StateFilter

from aiogram.fsm.context import FSMContext
from pdf_generator.gen_pdf import create_user_doc
from handlers.components.live_adress import handle_live_adress_input
from handlers.components.residence_permit import func_residence_permit
from handlers.components.residence_reason_patent import func_residence_reason_patent
from keyboards.components.child_data import get_child_data_start_keyboard
from keyboards.components.inline_keyboard import get_callback_btns
from keyboards.components.select_region_and_mvd import (
    get_waiting_confirm_start_keyboard,
)
from keyboards.registration_renewal import (
    get_registration_renewal_after_residence_reason_and_location_keyboard,
)
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from states.components.sema_components import WorkedLastYearStates
from states.doc_residence_notification import (
    DocResidenceNotificationStates,
    IncomeLastYearStates,
    TravelOutsideRuStates,
)
from states.components.passport_manual import PassportManualStates
from states.components.select_region_and_mvd import SelectRegionStates
from keyboards.doc_residence_notification import (
    get_check_data_before_gen,
    get_doc_residence_notification_passport_start_keyboard,
    get_travel_outside_Ru_check_keyboard,
    get_travel_outside_Ru_keyboard,
)

from localization import _
from data_manager import SecureDataManager

doc_residence_notification_router = Router()
data_manager = SecureDataManager()


async def get_travel_outside_Ru_msg(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    text = (
        f"{_.get_text('travel_outside_Ru.message_1.title', lang)}\n"
        f"{_.get_text('travel_outside_Ru.message_1.example_text', lang)}"
    )
    await callback.message.edit_text(text)
    await state.set_state(TravelOutsideRuStates.date)


async def get_worked_last_year_msg(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(dismissal_date="по настоящее время")

    await state.update_data(
        **{
            "sema_components": {
                "state_obj": WorkedLastYearStates,
                "end_hendler": end_worked_last_year,
            }
        }
    )
    await state.set_state(WorkedLastYearStates.hiring_date)
    text = f"{_.get_text('worked_last_year.hiring_date.title', lang)}"
    await callback.message.edit_text(text)


async def get_worked_last_year_msg_choose(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")

    text = f"{_.get_text('worked_last_year.start.title', lang)}"
    btns = {
        "worked_last_year.start.btn_yes": "y",
        "worked_last_year.start.btn_no": "n",
    }
    await callback.message.edit_text(text, reply_markup=get_callback_btns(btns, lang))
    await state.set_state(DocResidenceNotificationStates.start_worked_last_year)


async def get_income_last_year_msg(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    text = f"{_.get_text('income_last_year.message_1.title', lang)}"
    is_now_edit = state_data.get("is_now_edit")

    btns = {
        "income_last_year.message_1.form_3_NDFL_em": "form_3_NDFL",
        "income_last_year.message_1.form_2_NDFL_em": "form_2_NDFL",
        "income_last_year.message_1.btn_0": "btn_0",
    }

    if not is_now_edit:
        btns["income_last_year.message_1.btn_back"] = "btn_back"
    await callback.message.edit_text(text, reply_markup=get_callback_btns(btns, lang))
    await state.set_state(IncomeLastYearStates.start)


async def do_lists(old_list, new_list, id_):
    if old_list:
        if id_ is None:
            old_list.extend(new_list)
        else:
            old_list.insert(id_, *new_list)
        return old_list
    return new_list


@doc_residence_notification_router.callback_query(
    F.data == "doc_residence_notification"
)
async def handle_doc_residence_notification_start(
    callback: CallbackQuery, state: FSMContext
):
    """Старт сценария «Уведомление о проживании по ВНЖ» из главного меню"""
    await state.set_state(DocResidenceNotificationStates.waiting_confirm_start)

    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="doc_residence_notification_after_mvd")

    text = (
        f"{_.get_text('doc_residence_notification_start.title', lang)}\n"
        f"{_.get_text('doc_residence_notification_start.description', lang)}\n"
        f"{_.get_text('doc_residence_notification_start.documents_to_prepare', lang)}"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_waiting_confirm_start_keyboard(lang),
    )

@doc_residence_notification_router.callback_query(
    F.data == "doc_residence_notification_after_mvd"
)
async def handle_doc_residence_notification_after_mvd(
    callback: CallbackQuery, state: FSMContext
):
    """Сохраняем адрес подразделения МВД и показываем шаг паспорта (фото/вручную)"""
    await state.set_state(DocResidenceNotificationStates.after_select_mvd)
    state_data = await state.get_data()
    lang = state_data["language"]
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")

    data_manager.save_user_data(callback.from_user.id, session_id, {"mvd_adress": mvd_adress})

    # Критично: метки для фото-компонента паспорта
    await state.update_data(
        from_action=DocResidenceNotificationStates.after_passport,
        passport_title="registration_renewal_passport_title",
        ocr_flow="drn",  # чтобы passport_photo.new_ok отрисовал кнопку "перейти к ВНЖ"
    )

    text = (
        f"{_.get_text('registration_renewal_start_passport.title', lang)}\n"
        f"{_.get_text('registration_renewal_start_passport.description', lang)}"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_doc_residence_notification_passport_start_keyboard(lang),
    )


@doc_residence_notification_router.callback_query(F.data == "drn_after_passport")
async def drn_after_passport(cb: CallbackQuery, state: FSMContext):
    """
    Паспорт подтверждён (OCR) → запускаем сбор ВНЖ.
    Ничего, что относится к адресу, пока НЕ трогаем.
    """
    # 1) Куда вернёмся ПОСЛЕ завершения ВНЖ
    await state.update_data(
        from_action=DocResidenceNotificationStates.after_adress,
        # 2) Очистим возможные «хвосты» от прошлых шагов
        waiting_data=None,
        is_now_edit=False,
        change_id=None,
        # 3) Важно: НЕ устанавливаем next_states и НЕ ставим live_adress_conf здесь
        ocr_flow=None,
    )

    # 4) Переходим в общий компонент ВНЖ (серия/дата/кем выдан ВНЖ)
    await func_residence_permit(cb.message, state)



@doc_residence_notification_router.message(DocResidenceNotificationStates.after_passport)
async def handle_live_adress_data(message: Message, state: FSMContext):
    """
    РУЧНОЙ сценарий (без OCR): на этом шаге пользователь присылает 'кем выдан'.
    После этого — к блоку ВНЖ.
    """
    state_data = await state.get_data()
    lang = state_data["language"]

    passport_data = state_data.get("passport_data", {}) or {}
    passport_data["passport_issue_place"] = message.text.strip()

    session_id = state_data.get("session_id")
    await state.update_data(passport_data=passport_data)
    data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": passport_data})

    await state.update_data(
        from_action=DocResidenceNotificationStates.after_adress,
        next_states=[LiveAdress.adress],
        live_adress_conf=True,
    )
    await func_residence_permit(message, state)

@doc_residence_notification_router.message(DocResidenceNotificationStates.after_adress)
async def handle_after_adress(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data["language"]

    waiting_data = state_data.get("waiting_data", None)

    # Достаём уже собранный блок ВНЖ
    rp = state_data.get("residence_permit", {})

    user_data = {
        waiting_data: message.text.strip(),
        "residence_permit": {
            "serial_number": rp.get("serial_number", ""),
            "issue_date": rp.get("issue_date", ""),
            "issue_place": rp.get("issue_place", ""),
        },
    }

    session_id = state_data.get("session_id")
    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    await state.set_state(TravelOutsideRuStates.start)
    text = f"{_.get_text('travel_outside_Ru.message_0.title', lang)}"
    await message.answer(text, reply_markup=get_travel_outside_Ru_keyboard(lang))


@doc_residence_notification_router.callback_query(
    F.data.startswith("travel_outside_Ru"), TravelOutsideRuStates.start
)
async def handle_travel_outside_Ru(callback: CallbackQuery, state: FSMContext):
    is_travel_outside_Ru = callback.data.split("_")[-1]
    state_data = await state.get_data()
    await state.set_state(TravelOutsideRuStates.place)

    lang = state_data.get("language")

    if is_travel_outside_Ru == "y":
        await get_travel_outside_Ru_msg(callback, state)
    else:
        await get_worked_last_year_msg_choose(callback, state)


@doc_residence_notification_router.message(TravelOutsideRuStates.date)
async def handle_travel_outside_Ru_date(message: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(TravelOutsideRuStates.place)

    lang = state_data.get("language")

    session_id = state_data.get("session_id")
    user_data = {"date": message.text.strip()}
    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = (
        f"{_.get_text('travel_outside_Ru.message_2.title', lang)}\n"
        f"{_.get_text('travel_outside_Ru.message_2.example_text', lang)}"
    )
    await message.answer(text=text)


@doc_residence_notification_router.message(TravelOutsideRuStates.place)
async def handle_travel_outside_Ru_place(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")

    session_id = state_data.get("session_id")
    user_data = {"place": message.text.strip()}
    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    state_data = await state.get_data()

    info = (
        [
            f"<b>{i}. {data['date']} — {data['place']}</b>"
            for i, data in enumerate(state_data["travel_outside_Ru"], 1)
        ]
        if "travel_outside_Ru" in state_data.keys()
        else []
    )
    info += [f"<b>{len(info)+1}. {state_data['date']} — {state_data['place']}</b>"]

    text = f"{_.get_text('travel_outside_Ru.message_3.title', lang)}\n{'\n'.join(info)}"
    await message.answer(text=text, reply_markup=get_travel_outside_Ru_check_keyboard(lang))


@doc_residence_notification_router.callback_query(
    F.data.startswith("ck_travel_outside_Ru")
)
async def handle_travel_outside_Ru_callback(callback: CallbackQuery, state: FSMContext):
    is_travel_outside_Ru = callback.data.split("_")[-1]
    state_data = await state.get_data()
    id_ = state_data.get("change_id")
    is_now_edit = state_data.get("is_now_edit")

    lang = state_data.get("language")

    if is_travel_outside_Ru == "edit":
        await get_travel_outside_Ru_msg(callback, state)
    else:
        old_travel_outside_Ru = state_data.get("travel_outside_Ru")
        travel_outside_Ru = [{"date": state_data["date"], "place": state_data["place"]}]

        travel_outside_Ru = await do_lists(old_travel_outside_Ru, travel_outside_Ru, id_)
        await state.update_data(change_id=None)

        session_id = state_data.get("session_id")
        user_data = {"travel_outside_Ru": travel_outside_Ru}
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)

        if is_travel_outside_Ru == "y":
            if is_now_edit:
                await state.update_data(is_now_edit=False)
                await check_doc_residence_notification(callback, state)
            else:
                await get_worked_last_year_msg_choose(callback, state)
        else:
            await get_travel_outside_Ru_msg(callback, state)


@doc_residence_notification_router.callback_query(
    DocResidenceNotificationStates.start_worked_last_year, F.data
)
async def worked_last_year_callback_hendler(callback: CallbackQuery, state: FSMContext):
    is_worked_last_year = callback.data.split("_")[-1]
    state_data = await state.get_data()
    lang = state_data.get("language")

    if is_worked_last_year == "n":
        worked_last_year = [
            {
                "org_name": "не работаю",
                "job_title": "не работаю",
                "hiring_date": state_data["residence_permit"]["issue_date"],
                "dismissal_date": "по настоящее время",
                "work_adress": state_data["live_adress"],
            }
        ]
        session_id = state_data.get("session_id")
        user_data = {"worked_last_year": worked_last_year}
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)

        await get_income_last_year_msg(callback, state)
    else:
        await get_worked_last_year_msg(callback, state)


async def end_worked_last_year(message: Message, state: FSMContext, edit_msg=None):
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(DocResidenceNotificationStates.worked_last_year_data)

    data = await state.get_data()
    pprint(data)
    message_lines_1 = [
        f"{_.get_text('WorkedLastYearStates.org_name', lang)}{data['org_name']}",
        f"{_.get_text('WorkedLastYearStates.job_title', lang)}{data['job_title']}",
        f"{_.get_text('WorkedLastYearStates.hiring_date', lang)}{data['hiring_date']}",
        f"{_.get_text('WorkedLastYearStates.dismissal_date', lang)}{data['dismissal_date']}",
        f"{_.get_text('WorkedLastYearStates.work_adress', lang)}{data['work_adress']}",
    ]
    info = (
        [
            "\n".join(
                [
                    f"{_.get_text('WorkedLastYearStates.org_name', lang)}{work['org_name']}",
                    f"{_.get_text('WorkedLastYearStates.job_title', lang)}{work['job_title']}",
                    f"{_.get_text('WorkedLastYearStates.hiring_date', lang)}{work['hiring_date']}",
                    f"{_.get_text('WorkedLastYearStates.dismissal_date', lang)}{work['dismissal_date']}",
                    f"{_.get_text('WorkedLastYearStates.work_adress', lang)}{work['work_adress']}",
                ]
            )
            for work in data.get('worked_last_year', [])
        ]
        if "worked_last_year" in state_data.keys()
        else []
    )

    info += ["\n".join(message_lines_1)]

    text = f"{_.get_text('WorkedLastYearStates.title', lang)}\n\n" + "\n\n".join(info)
    btns = {
        "WorkedLastYearStates.btn_add": "add",
        "WorkedLastYearStates.btn_yes": "y",
        "WorkedLastYearStates.btn_edit": "edit",
    }

    if edit_msg is None:
        await message.answer(text, reply_markup=get_callback_btns(btns, lang))
    else:
        await message.edit_text(text, reply_markup=get_callback_btns(btns, lang))


@doc_residence_notification_router.callback_query(
    DocResidenceNotificationStates.worked_last_year_data
)
async def handle_worked_last_year_data(callback: CallbackQuery, state: FSMContext):
    worked_last_year_callback = callback.data
    state_data = await state.get_data()

    lang = state_data.get("language")
    id_ = state_data.get("change_id")
    is_now_edit = state_data.get("is_now_edit")

    if worked_last_year_callback == "edit":
        await get_worked_last_year_msg(callback, state)
    else:
        old_worked_last_year = state_data.get("worked_last_year")
        worked_last_year = [
            {
                "org_name": state_data["org_name"],
                "job_title": state_data["job_title"],
                "hiring_date": state_data["hiring_date"],
                "dismissal_date": state_data["dismissal_date"],
                "work_adress": state_data["work_adress"],
            },
        ]
        worked_last_year = await do_lists(old_worked_last_year, worked_last_year, id_)
        await state.update_data(change_id=None)

        session_id = state_data.get("session_id")
        user_data = {"worked_last_year": worked_last_year}
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)
        if worked_last_year_callback == "y":
            if is_now_edit:
                await state.update_data(is_now_edit=False)
                await check_doc_residence_notification(callback, state)
            else:
                await get_income_last_year_msg(callback, state)
        else:
            await get_worked_last_year_msg(callback, state)


@doc_residence_notification_router.callback_query(IncomeLastYearStates.start)
async def handle_income_last_year_start(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    state_data = await state.get_data()
    lang = state_data.get("language")

    if callback_data == "btn_back":
        old_worked_last_year = state_data.get("worked_last_year")
        org_name = state_data.get("org_name")

        if old_worked_last_year is None or org_name is None:
            await get_worked_last_year_msg_choose(callback, state)
            return

        old_worked_last_year.pop()

        session_id = state_data.get("session_id")
        user_data = {"worked_last_year": old_worked_last_year}
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)

        await end_worked_last_year(callback.message, state, "edit_msg")

    elif callback_data == "btn_0":
        session_id = state_data.get("session_id")
        user_data = {"income_last_year": [{"form_NDFL": "no", "income": 0}]}
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)
        await check_doc_residence_notification(callback, state)

    else:
        is_now_edit = state_data.get("is_now_edit")

        await state.update_data(form_NDFL=callback_data)
        text = (
            f"{_.get_text('income_last_year.message_2.title', lang)}"
            f"{_.get_text(f'income_last_year.message_1.{callback_data}', lang)}\n"
            f"{_.get_text('income_last_year.message_2.description', lang)}\n"
            f"{_.get_text('income_last_year.message_2.example_text', lang)}"
        )
        btns = {"income_last_year.message_1.btn_back": "btn_back"}
        if is_now_edit:
            await callback.message.edit_text(text)
        else:
            await callback.message.edit_text(text, reply_markup=get_callback_btns(btns, lang))

        await state.set_state(IncomeLastYearStates.income)


@doc_residence_notification_router.callback_query(IncomeLastYearStates.income)
async def handle_income_last_year_income(callback: CallbackQuery, state: FSMContext):
    await get_income_last_year_msg(callback, state)


@doc_residence_notification_router.message(IncomeLastYearStates.income)
async def handle_income_last_year_income(message: Message, state: FSMContext):
    await state.update_data(income=message.text.strip())
    state_data = await state.get_data()
    lang = state_data.get("language")

    rows = state_data.get("income_last_year", [])
    info = []
    for row in rows:
        src = _.get_text(f"income_last_year.message_1.{row['form_NDFL']}", lang)
        info.append(
            f"{_.get_text('income_last_year.message_3.source_amount', lang)}{src}\n"
            f"{_.get_text('income_last_year.message_3.income_amount', lang)}{row['income']}"
        )

    src_cur = _.get_text(f"income_last_year.message_1.{state_data['form_NDFL']}", lang)
    info.append(
        f"{_.get_text('income_last_year.message_3.source_amount', lang)}{src_cur}\n"
        f"{_.get_text('income_last_year.message_3.income_amount', lang)}{state_data['income']} ₽"
    )
    text = f"{_.get_text('income_last_year.message_3.title', lang)}\n\n" + "\n\n".join(info)

    btns = {
        "income_last_year.message_3.btn_add": "add",
        "income_last_year.message_3.btn_yes": "y",
        "income_last_year.message_3.btn_edit": "edit",
    }
    await message.answer(text, reply_markup=get_callback_btns(btns, lang))
    await state.set_state(IncomeLastYearStates.after_income)


@doc_residence_notification_router.callback_query(IncomeLastYearStates.after_income)
async def handle_income_last_year_after_income(callback: CallbackQuery, state: FSMContext):
    income_last_year_callback = callback.data
    state_data = await state.get_data()
    id_ = state_data.get("change_id")
    is_now_edit = state_data.get("is_now_edit")

    lang = state_data.get("language")

    if income_last_year_callback == "edit":
        await get_income_last_year_msg(callback, state)
    else:
        old_income_last_year = state_data.get("income_last_year")
        income_last_year = [
            {"form_NDFL": state_data["form_NDFL"], "income": state_data["income"]}
        ]

        income_last_year = await do_lists(old_income_last_year, income_last_year, id_)
        await state.update_data(change_id=None)

        session_id = state_data.get("session_id")
        user_data = {"income_last_year": income_last_year}
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)

        if income_last_year_callback == "y":
            if is_now_edit:
                await state.update_data(is_now_edit=False)
                await check_doc_residence_notification(callback, state)
            else:
                await check_doc_residence_notification(callback, state)
        else:
            await get_income_last_year_msg(callback, state)

@doc_residence_notification_router.callback_query(
    F.data == "check_doc_residence_notification"
)
async def check_doc_residence_notification(
    event: CallbackQuery | Message, state: FSMContext
):
    await state.set_state(None)
    state_data = await state.get_data()
    lang = state_data.get("language")

    await state.update_data(
        from_action=DocResidenceNotificationStates.check_data,
        change_data_from_check="check_doc_residence_notification",
    )

    data = await state.get_data()
    pprint(data)

    passport = data["passport_data"]
    rp = data["residence_permit"]

    # Блок работы
    jobs = "\n\n".join(
        [
            "".join(
                [
                    f"{_.get_text('doc_residence_notification.work_place', lang)}{job.get('work_adress', '')}",
                    f"{_.get_text('doc_residence_notification.work_place_separator', lang)}{job.get('org_name', '')}",
                    f"{_.get_text('doc_residence_notification.work_place_separator', lang)}{job.get('job_title', '')}",
                    f"{_.get_text('doc_residence_notification.work_start_date', lang)}{job.get('hiring_date', '')}",
                    f"{_.get_text('doc_residence_notification.work_end_date', lang)}{job.get('dismissal_date', '')}",
                ]
            )
            for job in data["worked_last_year"]
        ]
    )

    # Доходы
    income_last_year = data["income_last_year"]
    income_last_year_str = "\n".join(
        [
            (
                f"{_.get_text(f'income_last_year.message_1.{row['form_NDFL']}', lang)}, {row['income']}"
                if row["income"] != 0
                else _.get_text("doc_residence_notification.no_income", lang)
            )
            for row in income_last_year
        ]
    )

    # Поездки
    travel = data.get("travel_outside_Ru")
    travel_str = (
        _.get_text("doc_residence_notification.no_travel", lang)
        if travel is None
        else "\n".join([f" {row['date']} - {row['place']}" for row in travel])
    )

    message_lines = [
        _.get_text("doc_residence_notification.title", lang),
        f"{_.get_text('doc_residence_notification.full_name', lang)}{passport.get('full_name', '')}",
        f"{_.get_text('doc_residence_notification.birth_date', lang)}{passport.get('birth_date', '')}",
        f"{_.get_text('doc_residence_notification.citizenship', lang)}{passport.get('citizenship', '')}",
        (
            f"{_.get_text('doc_residence_notification.passport', lang)}{passport.get('passport_serial_number', '')}"
            f"{_.get_text('doc_residence_notification.passport_issue', lang)}{passport.get('passport_issue_place', '')} "
            f"{passport.get('passport_issue_date', '')}{_.get_text('doc_residence_notification.expiry_date', lang)}{passport.get('passport_expiry_date', '')}"
        ),
        (
            f"{_.get_text('doc_residence_notification.residence_permit_number', lang)}{rp.get('serial_number', '')}"
            f"{_.get_text('doc_residence_notification.residence_permit_issue', lang)}{rp.get('issue_date', '')}"
            f"{_.get_text('doc_residence_notification.comma_separator', lang)}{rp.get('issue_place', '')}"
        ),
        f"{_.get_text('doc_residence_notification.address', lang)}{data.get('live_adress', '')}",
        f"{_.get_text('doc_residence_notification.travel_periods', lang)}{travel_str}\n",
        jobs,
        f"\n{_.get_text('doc_residence_notification.income', lang)}{income_last_year_str}",
        f"{_.get_text('doc_residence_notification.mvd_adress', lang)} {data['mvd_adress']}",
    ]

    text = "\n".join(message_lines)
    msg_obj = {"text": text, "reply_markup": get_check_data_before_gen(lang)}

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(**msg_obj)
    else:
        await event.answer(**msg_obj)


@doc_residence_notification_router.message(DocResidenceNotificationStates.check_data)
async def edit_doc_residence_notification(message: Message, state: FSMContext):
    state_data = await state.get_data()
    waiting_data = state_data.get("waiting_data", None)
    lang = state_data.get("language")
    session_id = state_data.get("session_id")

    if "." in waiting_data:
        primary_key, secondary_key = waiting_data.split(".", 1)
        primary_key_data = state_data.get(primary_key) or {}
        primary_key_data[secondary_key] = message.text.strip()
        await state.update_data({primary_key: primary_key_data})
    else:
        await state.update_data({waiting_data: message.text.strip()})
        data_manager.save_user_data(message.from_user.id, session_id, {waiting_data: message.text.strip()})

    await check_doc_residence_notification(message, state)


@doc_residence_notification_router.callback_query(F.data == "all_true_in_doc_residence_notification")
async def generate_doc_residence_notification(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    mvd_adress = state_data.get("mvd_adress", "")
    mvd_adress_short_1 = mvd_adress[:38]
    mvd_adress_split_1 = mvd_adress[38:]
    mvd_adress_short_2 = mvd_adress[:44]
    mvd_adress_split_2 = mvd_adress[44:]
    live_adress = state_data.get("live_adress", "")
    live_adress_short = live_adress[:75]
    live_adress_split = live_adress[75:]
    worked_last_year = state_data.get("worked_last_year", [])
    working_start_1 = worked_last_year[0].get("hiring_date", "") if len(worked_last_year) > 0 else ""
    working_start_2 = worked_last_year[1].get("hiring_date", "") if len(worked_last_year) > 1 else ""
    working_start_3 = worked_last_year[2].get("hiring_date", "") if len(worked_last_year) > 2 else ""
    working_end_1 = worked_last_year[0].get("dismissal_date", "") if len(worked_last_year) > 0 else ""
    working_end_2 = worked_last_year[1].get("dismissal_date", "") if len(worked_last_year) > 1 else ""
    working_end_3 = worked_last_year[2].get("dismissal_date", "") if len(worked_last_year) > 2 else ""
    working_org_1 = worked_last_year[0].get("org_name", "") if len(worked_last_year) > 0 else ""
    working_org_2 = worked_last_year[1].get("org_name", "") if len(worked_last_year) > 1 else ""
    working_org_3 = worked_last_year[2].get("org_name", "") if len(worked_last_year) > 2 else ""
    working_job_1 = worked_last_year[0].get("job_title", "") if len(worked_last_year) > 0 else ""
    working_job_2 = worked_last_year[1].get("job_title", "") if len(worked_last_year) > 1 else ""
    working_job_3 = worked_last_year[2].get("job_title", "") if len(worked_last_year) > 2 else ""

    if working_org_1 == "не работаю":
        working_place_1 = "не работаю"
    else:
        working_place_1 = f"{working_org_1}, {working_job_1}" if len(worked_last_year) > 0 else ""
    if working_org_2 == "не работаю":
        working_place_2 = "не работаю"
    else:
        working_place_2 = f"{working_org_2}, {working_job_2}" if len(worked_last_year) > 1 else ""
    if working_org_3 == "не работаю":
        working_place_3 = "не работаю"
    else:
        working_place_3 = f"{working_org_3}, {working_job_3}" if len(worked_last_year) > 2 else ""

    working_adress_1 = worked_last_year[0].get("work_adress", "") if len(worked_last_year) > 0 else ""
    working_adress_2 = worked_last_year[1].get("work_adress", "") if len(worked_last_year) > 1 else ""
    working_adress_3 = worked_last_year[2].get("work_adress", "") if len(worked_last_year) > 2 else ""

    outside_ru = state_data.get("travel_outside_Ru", [])
    outside_country_1 = outside_ru[0].get("place", "") if len(outside_ru) > 0 else ""
    outside_country_2 = outside_ru[1].get("place", "") if len(outside_ru) > 1 else ""
    outside_country_3 = outside_ru[2].get("place", "") if len(outside_ru) > 2 else ""
    outside_time_1 = outside_ru[0].get("date", "") if len(outside_ru) > 0 else ""
    outside_time_2 = outside_ru[1].get("date", "") if len(outside_ru) > 1 else ""
    outside_time_3 = outside_ru[2].get("date", "") if len(outside_ru) > 2 else ""

    income_last_year = state_data.get("income_last_year", [])
    source_of_income_1 = income_last_year[0].get("form_NDFL", "") if len(income_last_year) > 0 else ""
    source_of_income_2 = income_last_year[1].get("form_NDFL", "") if len(income_last_year) > 1 else ""
    source_of_income_3 = income_last_year[2].get("form_NDFL", "") if len(income_last_year) > 2 else ""
    source_of_income_4 = income_last_year[3].get("form_NDFL", "") if len(income_last_year) > 3 else ""
    source_of_income_5 = income_last_year[4].get("form_NDFL", "") if len(income_last_year) > 4 else ""
    salary_of_income_1 = income_last_year[0].get("income", "") if len(income_last_year) > 0 else ""
    salary_of_income_2 = income_last_year[1].get("income", "") if len(income_last_year) > 1 else ""
    salary_of_income_3 = income_last_year[2].get("income", "") if len(income_last_year) > 2 else ""
    salary_of_income_4 = income_last_year[3].get("income", "") if len(income_last_year) > 3 else ""
    salary_of_income_5 = income_last_year[4].get("income", "") if len(income_last_year) > 4 else ""

    ndfl_values = {
        "form_3_NDFL": "Декларация по форме 3-НДФЛ",
        "form_2_NDFL": "Справка по форме 2-НДФЛ",
        "no": "Нет дохода",
    }

    data = {
        "mvd_adress_short_1": mvd_adress_short_1,
        "mvd_adress_split_1": mvd_adress_split_1,
        "mvd_adress": mvd_adress,
        "mvd_adress_short_2": mvd_adress_short_2,
        "mvd_adress_split_2": mvd_adress_split_2,
        "full_name": state_data.get("passport_data", {}).get("full_name", ""),
        "live_adress": live_adress,
        "live_adress_short": live_adress_short,
        "live_adress_split": live_adress_split,
        "working_start_1": working_start_1,
        "working_start_2": working_start_2,
        "working_start_3": working_start_3,
        "working_end_1": working_end_1,
        "working_end_2": working_end_2,
        "working_end_3": working_end_3,
        "working_place_1": working_place_1,
        "working_place_2": working_place_2,
        "working_place_3": working_place_3,
        "working_adress_1": working_adress_1,
        "working_adress_2": working_adress_2,
        "working_adress_3": working_adress_3,
        "outside_country_1": outside_country_1,
        "outside_country_2": outside_country_2,
        "outside_country_3": outside_country_3,
        "outside_time_1": outside_time_1,
        "outside_time_2": outside_time_2,
        "outside_time_3": outside_time_3,
        "pass_num": state_data.get("passport_data", {}).get("passport_serial_number", ""),
        "pass_isp": state_data.get("passport_data", {}).get("passport_issue_place", ""),
        "pas_isd": state_data.get("passport_data", {}).get("passport_issue_date", ""),
        "pas_exp": state_data.get("passport_data", {}).get("passport_expiry_date", ""),
        "residence_permit_serial_number": state_data.get("residence_permit", {}).get("serial_number", ""),
        "residence_permit_issue_date": state_data.get("residence_permit", {}).get("issue_date", ""),
        "residence_permit_issue_place": state_data.get("residence_permit", {}).get("issue_place", ""),
        "source_of_income_1": ndfl_values.get(source_of_income_1, ""),
        "source_of_income_2": ndfl_values.get(source_of_income_2, ""),
        "source_of_income_3": ndfl_values.get(source_of_income_3, ""),
        "source_of_income_4": ndfl_values.get(source_of_income_4, ""),
        "source_of_income_5": ndfl_values.get(source_of_income_5, ""),
        "salary_of_income_1": salary_of_income_1,
        "salary_of_income_2": salary_of_income_2,
        "salary_of_income_3": salary_of_income_3,
        "salary_of_income_4": salary_of_income_4,
        "salary_of_income_5": salary_of_income_5,
    }

    doc = create_user_doc(context=data, template_name="check_living_vnj", user_path="pdf_generator")
    ready_doc = FSInputFile(doc, filename="Уведомление о подтверждении проживания по ВНЖ.docx")
    await state.clear()

    text = f"{_.get_text('ready_to_download_doc', lang)}\n"
    await callback.message.edit_text(text=text)
    await callback.message.answer_document(document=ready_doc)
