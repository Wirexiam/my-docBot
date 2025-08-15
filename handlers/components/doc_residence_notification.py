from pprint import pprint
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter

from aiogram.fsm.context import FSMContext

from handlers.components.live_adress import handle_live_adress_input
from handlers.components.residence_permit import func_residence_permit
from handlers.components.residence_reason_patent import func_residence_reason_patent
from keyboards.components.child_data import get_child_data_start_keyboard
from keyboards.components.inline_keyboard import get_callback_btns
from keyboards.components.select_region_and_mvd import get_waiting_confirm_start_keyboard
from keyboards.registration_renewal import (
    get_registration_renewal_after_residence_reason_and_location_keyboard,
)
from states.components.live_adress import LiveAdress
from states.components.phone_number import PhoneNumberStates
from states.components.sema_components import WorkedLastYearStates
from states.doc_residence_notification import DocResidenceNotificationStates, IncomeLastYearStates, TravelOutsideRuStates
from states.components.passport_manual import PassportManualStates
from states.components.select_region_and_mvd import SelectRegionStates
from keyboards.doc_residence_notification import (
    get_doc_residence_notification_passport_start_keyboard,
    get_travel_outside_Ru_check_keyboard,
    get_travel_outside_Ru_keyboard,
)

from localization import _
from data_manager import SecureDataManager

doc_residence_notification_router = Router()
data_manager = SecureDataManager()





async def get_travel_outside_Ru_msg(callback, state):
    state_data = await state.get_data()
    lang = state_data.get("language")
    text = f"{_.get_text("travel_outside_Ru.message_1.title", lang)}\n{_.get_text('travel_outside_Ru.message_1.example_text', lang)}"
    await callback.message.edit_text(text)
    await state.set_state(TravelOutsideRuStates.date)

async def get_worked_last_year_msg(callback, state):
        state_data = await state.get_data()
        lang = state_data.get("language")
        await state.update_data(dismissal_date = 'по настоящее время')

        await state.update_data(**{'sema_components':{'state_obj':WorkedLastYearStates, 'end_hendler':end_worked_last_year}})
        await state.set_state(WorkedLastYearStates.hiring_date)
        text = f"{_.get_text("worked_last_year.hiring_date.title", lang)}"
        await callback.message.edit_text(text)

async def get_income_last_year_msg(callback, state):
    state_data = await state.get_data()
    lang = state_data.get("language")
    text = f"{_.get_text("income_last_year.message_1.title", lang)}"
    btns = {
                'income_last_year.message_1.form_3_NDFL_em':'form_3_NDFL',
                'income_last_year.message_1.form_2_NDFL_em':'form_2_NDFL',
                'income_last_year.message_1.btn_0':'btn_0',
                'income_last_year.message_1.btn_back':'btn_back',
            }
    await callback.message.edit_text(text, reply_markup=get_callback_btns(btns, lang))
    await state.set_state(IncomeLastYearStates.start)


@doc_residence_notification_router.callback_query(F.data == "doc_residence_notification")
async def handle_doc_residence_notification_start(
    callback: CallbackQuery, state: FSMContext
):
    
    """Обработка нажатия кнопки начала процесса продления пребывания ребёнка (по патенту матери)"""

    # Установка состояния для начала процесса продления регистрации
    await state.set_state(
        DocResidenceNotificationStates.waiting_confirm_start
    )
    # await state.set_state(TravelOutsideRuStates.date)

    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.update_data(from_action="doc_residence_notification_after_mvd")
    # Отправка сообщения с инструкциями
    text = f"{_.get_text('doc_residence_notification_start.title', lang)}\n{_.get_text('doc_residence_notification_start.description', lang)}\n{_.get_text('doc_residence_notification_start.documents_to_prepare', lang)}"
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
    """загрузка mvd_adress"""

    await state.set_state(DocResidenceNotificationStates.after_select_mvd)
    state_data = await state.get_data()
    lang = state_data["language"]
    mvd_adress = state_data.get("mvd_adress")
    session_id = state_data.get("session_id")
    user_data = {
        "mvd_adress": mvd_adress,
    }
    data_manager.save_user_data(callback.from_user.id, session_id, user_data)


    await state.update_data(
        from_action=DocResidenceNotificationStates.after_passport,
        passport_title="registration_renewal_passport_title",

    )

    text = f"{_.get_text('registration_renewal_start_passport.title', lang)}\n{_.get_text('registration_renewal_start_passport.description', lang)}"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_doc_residence_notification_passport_start_keyboard(lang),
    )


@doc_residence_notification_router.message(
    DocResidenceNotificationStates.after_passport
)
async def handle_live_adress_data(message: Message, state: FSMContext):
        """Обработка начала передачи паспорта после выбора МВД и адреса"""
        state_data = await state.get_data()
        lang = state_data["language"]

        passport_data = state_data.get("passport_data")
        passport_data["passport_issue_place"] = message.text.strip()

        user_data = {
            "passport_data": passport_data,
        }
        await state.update_data(**user_data)
        session_id = state_data.get("session_id")
        data_manager.save_user_data(message.from_user.id, session_id, user_data)


        state_data = await state.get_data()
        print(state_data)


        await state.update_data(
            from_action=DocResidenceNotificationStates.after_adress,
            next_states=[LiveAdress.adress],
        )
        await func_residence_permit(
            message, state
        )


@doc_residence_notification_router.message(DocResidenceNotificationStates.after_adress)
async def handle_after_adress(message: Message, state: FSMContext):
        state_data = await state.get_data()
        lang = state_data["language"]

        waiting_data = state_data.get("waiting_data", None)
        user_data = {
            waiting_data: message.text.strip(),
            'residence_permit': {
                'serial_number':state_data['RP_serial_number'],
                'issue_date':state_data['RP_issue_date'],
                'issue_place':state_data['RP_issue_place'],
            }
        }
        session_id = state_data.get("session_id")
        await state.update_data(**user_data)
        data_manager.save_user_data(message.from_user.id, session_id, user_data)

        text = f"{_.get_text("travel_outside_Ru.message_0.title", lang)}"
        await message.answer(text, reply_markup=get_travel_outside_Ru_keyboard(lang))
        
        


@doc_residence_notification_router.callback_query(F.data.startswith('travel_outside_Ru'))
async def handle_travel_outside_Ru(callback: CallbackQuery, state: FSMContext):
    is_travel_outside_Ru = callback.data.split('_')[-1]
    state_data = await state.get_data()
    await state.set_state(TravelOutsideRuStates.place)

    lang = state_data.get("language")

    if is_travel_outside_Ru =='y':
        await get_travel_outside_Ru_msg(callback, state)
    else:
            text = f"{_.get_text("worked_last_year.start.title", lang)}"
            btns = {
                'worked_last_year.start.btn_yes':'y',
                'worked_last_year.start.btn_no':'n',
            }
            await callback.message.edit_text(text, reply_markup=get_callback_btns(btns, lang))
            await state.set_state(WorkedLastYearStates.start)
    



@doc_residence_notification_router.message(TravelOutsideRuStates.date)
async def handle_travel_outside_Ru_date(message: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(TravelOutsideRuStates.place)

    lang = state_data.get("language")

   
    session_id = state_data.get("session_id")
    user_data = {
        "date": message.text.strip(),
    }
    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    text = f"{_.get_text('travel_outside_Ru.message_2.title', lang)}\n{_.get_text('travel_outside_Ru.message_2.example_text', lang)}"
    await message.answer(text=text)


@doc_residence_notification_router.message(TravelOutsideRuStates.place)
async def handle_travel_outside_Ru_place(message: Message, state: FSMContext):
    state_data = await state.get_data()

    lang = state_data.get("language")

   
    session_id = state_data.get("session_id")
    user_data = {
        "place": message.text.strip(),
    }
    await state.update_data(**user_data)
    data_manager.save_user_data(message.from_user.id, session_id, user_data)

    state_data = await state.get_data()

    info = [f'<b>{i}. {' — '.join(data)}</b>' for i, data in enumerate(state_data['travel_outside_Ru'].items(), 1)] if 'travel_outside_Ru' in state_data.keys() else []


    info += [f'<b>{len(info)+1}. {state_data['date']} — {state_data['place']}</b>']
    text = f"{_.get_text('travel_outside_Ru.message_3.title', lang)}\n{'\n'.join(info)}"
    await message.answer(text=text, reply_markup=get_travel_outside_Ru_check_keyboard(lang))




@doc_residence_notification_router.callback_query(F.data.startswith('ck_travel_outside_Ru'))
async def handle_travel_outside_Ru_callback(callback: CallbackQuery, state: FSMContext):
    is_travel_outside_Ru = callback.data.split('_')[-1]
    state_data = await state.get_data()

    lang = state_data.get("language")

    if is_travel_outside_Ru =='edit':
        await get_travel_outside_Ru_msg(callback, state)
    else:
        old_travel_outside_Ru = state_data.get('travel_outside_Ru')
        travel_outside_Ru = {state_data['date']:state_data['place']}

        if old_travel_outside_Ru:
            travel_outside_Ru.update(old_travel_outside_Ru)


        session_id = state_data.get("session_id")
        user_data = {
            "travel_outside_Ru": travel_outside_Ru,
        }
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)
        if is_travel_outside_Ru =='y':

            text = f"{_.get_text("worked_last_year.start.title", lang)}"
            btns = {
                'worked_last_year.start.btn_yes':'y',
                'worked_last_year.start.btn_no':'n',
            }
            await callback.message.edit_text(text, reply_markup=get_callback_btns(btns, lang))
            await state.set_state(WorkedLastYearStates.start)

        else:
            await get_travel_outside_Ru_msg(callback, state)

    
    

@doc_residence_notification_router.callback_query(WorkedLastYearStates.start, F.data)
async def worked_last_year_callback_hendler(callback: CallbackQuery, state: FSMContext):
    is_worked_last_year = callback.data.split('_')[-1]
    state_data = await state.get_data()
    lang = state_data.get("language")

    if is_worked_last_year =='n':
        worked_last_year = [
            {
                'org_name':'не работаю',
                'job_title':'не работаю',
                'hiring_date':state_data['residence_permit']['issue_date'],
                'dismissal_date':'по настоящее время',
                'work_adress':state_data['live_adress'],
             }
        ]
        session_id = state_data.get("session_id")
        user_data = {
            "worked_last_year": worked_last_year,
        }
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
    message_lines_1 = [
        f"{_.get_text('WorkedLastYearStates.org_name', lang)}{data['org_name']}",
        f"{_.get_text('WorkedLastYearStates.job_title', lang)}{data['job_title']}",
        f"{_.get_text('WorkedLastYearStates.hiring_date', lang)}{data['hiring_date']}",
        f"{_.get_text('WorkedLastYearStates.dismissal_date', lang)}{data['dismissal_date']}",
        f"{_.get_text('WorkedLastYearStates.work_adress', lang)}{data['work_adress']}",
    ]
    info = ["\n".join([
        f"{_.get_text('WorkedLastYearStates.org_name', lang)}{work['org_name']}",
        f"{_.get_text('WorkedLastYearStates.job_title', lang)}{work['job_title']}",
        f"{_.get_text('WorkedLastYearStates.hiring_date', lang)}{work['hiring_date']}",
        f"{_.get_text('WorkedLastYearStates.dismissal_date', lang)}{work['dismissal_date']}",
        f"{_.get_text('WorkedLastYearStates.work_adress', lang)}{work['work_adress']}",
    ]) for work in data['worked_last_year']] if 'worked_last_year' in state_data.keys() else []

    info+= ["\n".join(message_lines_1)]

    text = f"{_.get_text("WorkedLastYearStates.title", lang)}\n\n"+"\n\n".join(info)
    btns = {
                'WorkedLastYearStates.btn_add':'add',
                'WorkedLastYearStates.btn_yes':'y',
                'WorkedLastYearStates.btn_edit':'edit'
            }
    
    if edit_msg is None:
        await message.answer(text, reply_markup=get_callback_btns(btns, lang))
    else:
        await message.edit_text(text, reply_markup=get_callback_btns(btns, lang))



         



@doc_residence_notification_router.callback_query(DocResidenceNotificationStates.worked_last_year_data)
async def handle_worked_last_year_data(callback: CallbackQuery, state: FSMContext):
    worked_last_year_callback = callback.data
    state_data = await state.get_data()

    lang = state_data.get("language")

    if worked_last_year_callback =='edit':
        await get_worked_last_year_msg(callback, state)
    else:
        old_worked_last_year = state_data.get('worked_last_year')
        worked_last_year = [
            {
                'org_name':state_data['org_name'],
                'job_title':state_data['job_title'],
                'hiring_date':state_data['hiring_date'],
                'dismissal_date':state_data['dismissal_date'],
                'work_adress':state_data['work_adress'],
             }
        ]

        if old_worked_last_year:
            worked_last_year.extend(old_worked_last_year)


        session_id = state_data.get("session_id")
        user_data = {
            "worked_last_year": worked_last_year,
        }
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)
        if worked_last_year_callback =='y':
            await get_income_last_year_msg(callback, state)
        else:
            await get_worked_last_year_msg(callback, state)

    

    




@doc_residence_notification_router.callback_query(IncomeLastYearStates.start)
async def handle_income_last_year_start(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    state_data = await state.get_data()
    lang = state_data.get("language")


    if callback_data =='btn_back':
        old_worked_last_year = state_data.get('worked_last_year')
        
        if old_worked_last_year is None:
            text = f"{_.get_text("worked_last_year.start.title", lang)}"
            btns = {
                'worked_last_year.start.btn_yes':'y',
                'worked_last_year.start.btn_no':'n',
            }
            await callback.message.edit_text(text, reply_markup=get_callback_btns(btns, lang))
            await state.set_state(WorkedLastYearStates.start)

            return
        
        old_worked_last_year.pop()

        session_id = state_data.get("session_id")
        user_data = {
                "worked_last_year": old_worked_last_year,
            }
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)

        await end_worked_last_year(callback.message, state, 'edit_msg')

    elif callback_data =='btn_0':
        session_id = state_data.get("session_id")
        user_data = {
                "income_last_year": {'no': 0},
            }
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)
        await check_doc_residence_notification(callback, state)


    else:
        await state.update_data(form_NDFL=callback_data)
        text = f"{_.get_text("income_last_year.message_2.title", lang)}{_.get_text(f"income_last_year.message_1.{callback_data}", lang)}\n{_.get_text("income_last_year.message_2.description", lang)}\n{_.get_text("income_last_year.message_2.example_text", lang)}"
        btns = {
                    'income_last_year.message_1.btn_back':'btn_back',
                }
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


    
        info = [
            f'{_.get_text('income_last_year.message_3.source_amount', lang)}{_.get_text(f"income_last_year.message_1.{form_NDFL}", lang)}\n{_.get_text('income_last_year.message_3.income_amount', lang)}{income}'
            for form_NDFL, income in state_data['income_last_year'].items()
            ] if 'income_last_year' in state_data.keys() else []

        info += [
            f'{_.get_text('income_last_year.message_3.source_amount', lang)}{_.get_text(f"income_last_year.message_1.{state_data["form_NDFL"]}", lang)}\n{_.get_text('income_last_year.message_3.income_amount', lang)}{state_data["income"]} ₽'
            ]
        text = f"{_.get_text('income_last_year.message_3.title', lang)}\n\n{'\n\n'.join(info)}"

        btns = {
                'income_last_year.message_3.btn_add':'add',
                'income_last_year.message_3.btn_yes':'y',
                'income_last_year.message_3.btn_edit':'edit'
            }
        await message.answer(text, reply_markup=get_callback_btns(btns, lang))
        await state.set_state(IncomeLastYearStates.after_income)
    






@doc_residence_notification_router.callback_query(IncomeLastYearStates.after_income)
async def handle_income_last_year_after_income(callback: CallbackQuery, state: FSMContext):
    income_last_year_callback = callback.data
    state_data = await state.get_data()

    lang = state_data.get("language")

    if income_last_year_callback =='edit':
        await get_income_last_year_msg(callback, state)
    else:
        old_income_last_year = state_data.get('income_last_year')
        income_last_year = {state_data['form_NDFL']:state_data['income']}

        if old_income_last_year:
            income_last_year.update(old_income_last_year)


        session_id = state_data.get("session_id")
        user_data = {
            "income_last_year": income_last_year,
        }
        await state.update_data(**user_data)
        data_manager.save_user_data(callback.from_user.id, session_id, user_data)

        state_data = await state.get_data()
        print(state_data)

        if income_last_year_callback =='y':
            await check_doc_residence_notification(callback, state)
        else:
            await get_income_last_year_msg(callback, state)

    





async def check_doc_residence_notification(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    state_data = await state.get_data()
    lang = state_data.get("language")
    pprint(state_data)

    data = await state.get_data()



    passport = data['passport_data']
    rp = data['residence_permit']

    # Локализация для блоков работы
    jobs = '\n\n'.join([
        ''.join([
            f"{_.get_text('doc_residence_notification.work_place', lang)}{job.get('work_adress', '')}",
            f"{_.get_text('doc_residence_notification.work_place_separator', lang)}{job.get('org_name', '')}",
            f"{_.get_text('doc_residence_notification.work_place_separator', lang)}{job.get('job_title', '')}",
            f"{_.get_text('doc_residence_notification.work_start_date', lang)}{job.get('hiring_date', '')}",
            f"{_.get_text('doc_residence_notification.work_end_date', lang)}{job.get('dismissal_date', '')}"
        ]) for job in data['worked_last_year']
    ])

    # Локализация для доходов
    income_last_year = data['income_last_year']
    income_last_year_str = '\n'.join([
        f"{_.get_text(f'income_last_year.message_1.{form_ndfl}', lang)}, {income}" if income != 0 
        else _.get_text('doc_residence_notification.no_income', lang) 
        for form_ndfl, income in income_last_year.items()
    ])

    # Локализация для поездок
    travel = data.get('travel_outside_Ru')
    travel_str = (
        _.get_text('doc_residence_notification.no_travel', lang) if travel is None 
        else '\n'.join([f' {date} - {place}' for date, place in travel.items()])
    )

    # Формирование сообщения с локализацией
    message_lines = [
        _.get_text('doc_residence_notification.title', lang),
        f"{_.get_text('doc_residence_notification.full_name', lang)}{passport.get('full_name', '')}",
        f"{_.get_text('doc_residence_notification.birth_date', lang)}{passport.get('birth_date', '')}",
        f"{_.get_text('doc_residence_notification.citizenship', lang)}{passport.get('citizenship', '')}",
        (
            f"{_.get_text('doc_residence_notification.passport', lang)}{passport.get('passport_serial_number', '')}"
            f"{_.get_text('doc_residence_notification.passport_issue', lang)}{passport.get('passport_issue_place', '')} "
            f"{passport.get('passport_issue_date', '')}"
        ),
        (
            f"{_.get_text('doc_residence_notification.residence_permit_number', lang)}{rp.get('serial_number', '')}"
            f"{_.get_text('doc_residence_notification.residence_permit_issue', lang)}{rp.get('issue_date', '')}"
            f"{_.get_text('doc_residence_notification.comma_separator', lang)}{rp.get('issue_place', '')}"
        ),
        f"{_.get_text('doc_residence_notification.address', lang)}{data.get('live_adress', '')}",
        f"{_.get_text('doc_residence_notification.travel_periods', lang)}{travel_str}\n",
        jobs,
        f"\n{_.get_text('doc_residence_notification.income', lang)}{income_last_year_str}"
    ]


    text = "\n".join(message_lines)
    await callback.message.edit_text(
        text=text,
        reply_markup=get_registration_renewal_after_residence_reason_and_location_keyboard(
            lang
        ),
    )


