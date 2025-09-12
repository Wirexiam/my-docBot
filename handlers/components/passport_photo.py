from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.components.passport_photo import PassportPhotoStates
from localization import _
from data_manager import SecureDataManager
from ocr.service import PassbotOcrService, OcrError

passport_photo_router = Router()
data_manager = SecureDataManager()
ocr_service = PassbotOcrService()

@passport_photo_router.callback_query(F.data == "passport_photo_start")
async def on_passport_photo_start(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("language")
    await state.set_state(PassportPhotoStates.waiting_passport_photo)
    title = _.get_text("ocr.passport.send_photo.title", lang)
    hint  = _.get_text("ocr.passport.send_photo.hint",  lang)
    await callback.message.edit_text(f"{title}\n\n{hint}")

@passport_photo_router.message(PassportPhotoStates.waiting_passport_photo, F.photo)
async def on_passport_photo(message: Message, state: FSMContext):
    state_data = await state.get_data()
    lang       = state_data.get("language")
    session_id = state_data.get("session_id")

    f = await message.bot.get_file(message.photo[-1].file_id)
    file_bytes = await message.bot.download_file(f.file_path)
    img_path = data_manager.save_file(message.from_user.id, session_id, file_bytes.read(), filename="passport.jpg")

    progress = _.get_text("ocr.passport.progress", lang)
    note_msg = await message.answer(progress)

    try:
        result = await ocr_service.process_passport(img_path)

        await state.update_data(passport_data=result.passport_data)
        data_manager.save_user_data(message.from_user.id, session_id, {"passport_data": result.passport_data})

        prev_tpl = _.get_text("ocr.passport.success.preview", lang)
        preview = prev_tpl.format(
            full_name   = result.passport_data.get("full_name", "—"),
            birth_date  = result.passport_data.get("birth_date", "—"),
            citizenship = result.passport_data.get("citizenship", "—"),
            doc_id      = result.passport_data.get("passport_serial_number", result.passport_data.get("doc_id", "—")),
            issued_by   = result.passport_data.get("passport_issue_place", "—"),
            issue_date  = result.passport_data.get("passport_issue_date", "—"),
            expiry_date = result.passport_data.get("passport_expiry_date", "—"),
        )
        success_title = _.get_text("ocr.passport.success.title", lang)
        await note_msg.edit_text(f"{success_title}\n\n{preview}")

        from_action = state_data.get("from_action")
        if from_action:
            await state.set_state(from_action)
            await message.answer("Теперь укажите место выдачи паспорта (строкой).")

    except OcrError as e:
        fail_title = _.get_text("ocr.passport.fail.title", lang)
        fail_hint  = _.get_text("ocr.passport.fail.hint",  lang)
        await note_msg.edit_text(f"{fail_title}\n\n{fail_hint}\n\n{e.user_message}")
