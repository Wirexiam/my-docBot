import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from data_manager import SecureDataManager
from handlers.components.passport_photo import passport_photo_router

# Настройка логирования (без персональных данных)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Глобальные объекты
data_manager = SecureDataManager()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


async def cleanup_task():
    """Фоновая задача очистки"""
    while True:
        try:
            data_manager.cleanup_expired_sessions()
            await asyncio.sleep(1800)  # 30 минут
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
            await asyncio.sleep(300)  # 5 минут при ошибке


async def main():
    """Главная функция"""
    logger.info("Starting DocBot...")

    # Запускаем фоновую очистку
    cleanup_task_handle = asyncio.create_task(cleanup_task())

    try:
        # Регистрация роутеров
        from handlers.onboarding import onboarding_router
        from handlers.stamp_transfer import stamp_transfer_router
        from handlers.main_menu import main_menu
        from handlers.components.select_region_and_mvd import select_region_router
        from handlers.components.passport_manual import passport_manual_router
        from handlers.components.phone_number import phone_number_router
        from handlers.components.live_adress import live_adress_router

        from handlers.nortification_arrival import nortification_arrival
        from handlers.registration_renewal import registration_renewal_router
        from handlers.doc_child_stay_extension import doc_child_stay_extension_router
        from handlers.components.child_data import child_data_router
        from handlers.work_activity import work_activity_router
        from handlers.components.home_migr_data import home_migr_data
        from handlers.components.organization import organization_router
        from handlers.migrat_card import migration_manual_router
        from handlers.components.residence_reason_patent import (
            residence_reason_patient_router,
        )
        from handlers.components.residence_reason_child import (
            residence_reason_child_router,
        )
        from handlers.components.residence_reason_marriage import (
            residence_reason_marriage_router,
        )
        from handlers.doc_residence_notification import (
            doc_residence_notification_router,
        )
        from handlers.components.residence_permit import residence_permit_router
        from handlers.components.sema_components import sema_components_router
        from handlers.components.birth_certificate import birth_certificate_router
        from handlers.components.changing_data import changing_data_router
        from handlers.components.individual import individual_router
        from handlers.components.representative import representative_router
        from handlers.stay_prolong import stay_prolong_router

        dp.include_router(birth_certificate_router)
        dp.include_router(representative_router)
        dp.include_router(individual_router)
        dp.include_router(changing_data_router)
        dp.include_router(residence_reason_child_router)
        dp.include_router(residence_reason_patient_router)
        dp.include_router(residence_reason_marriage_router)
        dp.include_router(onboarding_router)
        dp.include_router(registration_renewal_router)
        dp.include_router(main_menu)
        dp.include_router(stamp_transfer_router)
        dp.include_router(select_region_router)
        dp.include_router(passport_manual_router)
        dp.include_router(passport_photo_router)  # ← OCR по фото
        dp.include_router(phone_number_router)
        dp.include_router(live_adress_router)
        dp.include_router(nortification_arrival)
        dp.include_router(migration_manual_router)
        dp.include_router(doc_child_stay_extension_router)
        dp.include_router(child_data_router)
        dp.include_router(work_activity_router)
        dp.include_router(home_migr_data)
        dp.include_router(organization_router)
        dp.include_router(doc_residence_notification_router)
        dp.include_router(residence_permit_router)
        dp.include_router(sema_components_router)
        dp.include_router(stay_prolong_router)

        await dp.start_polling(bot)

    finally:
        cleanup_task_handle.cancel()
        try:
            await cleanup_task_handle
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
