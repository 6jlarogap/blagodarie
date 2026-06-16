import asyncio
from aiogram import Bot, Dispatcher, enums
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.session.aiohttp import AiohttpSession

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import logging
import settings
import me

storage = MemoryStorage()

async def main_():
    kwargs_bot = dict(
        token=settings.TOKEN,
        default=DefaultBotProperties(
            parse_mode=enums.ParseMode.HTML,
            link_preview_is_disabled=True,
    ))
    if settings.LOCAL_SERVER:
        kwargs_bot.update(
            session = AiohttpSession(
                api=TelegramAPIServer.from_base(settings.LOCAL_SERVER, is_local=True),
        ))
    elif settings.PROXY:
        kwargs_bot.update(
            session = AiohttpSession(proxy=settings.PROXY),
        )
    bot = Bot(**kwargs_bot)
    dp = Dispatcher(storage=storage)

    me.bot = bot
    me.dp = dp
    me.bot_data = await bot.get_me()
    from handler_bot import router as router_bot
    from handler_callbacks import router as router_callbacks
    from handler_group import router as router_group
    from handler_offer import router as router_offer
    from handler_sympas import router as router_sympas
    from handler_relatives import router as router_relatives

    schedule_start = False
    if settings.SCHEDULE_CRON:
        scheduler = AsyncIOScheduler()
        from common import Schedule
        for task in settings.SCHEDULE_CRON:
            if proc := getattr(Schedule, task, None):
                try:
                    if scheduler.add_job(proc, 'cron', **settings.SCHEDULE_CRON[task]):
                        schedule_start = True
                except:
                    pass
    if schedule_start:
        scheduler.start()

    dp.include_routers(
        router_bot,
        router_callbacks,
        router_group,
        router_offer,
        router_sympas,
        router_relatives,
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        polling_timeout=20,
    )

asyncio.run(main_())
