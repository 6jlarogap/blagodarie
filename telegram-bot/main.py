import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, enums
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.session.aiohttp import AiohttpSession

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import logging
import settings
import me


def _redis_key_builder(prefix):
    from aiogram.fsm.storage.redis import DefaultKeyBuilder

    try:
        return DefaultKeyBuilder(prefix=prefix, with_bot_id=True)
    except TypeError:
        return DefaultKeyBuilder(prefix=prefix)


def build_fsm_storage():
    storage_name = getattr(settings, 'BOT_FSM_STORAGE', 'redis')
    if storage_name == 'memory':
        logging.warning('Using volatile MemoryStorage for bot FSM')
        return MemoryStorage()
    if storage_name != 'redis':
        raise RuntimeError('Unsupported BOT_FSM_STORAGE: %s' % storage_name)

    try:
        import redis.asyncio as aioredis
        from aiogram.fsm.storage.redis import RedisStorage
    except Exception:
        if getattr(settings, 'BOT_FSM_REDIS_FALLBACK_TO_MEMORY', False):
            logging.exception('Redis FSM storage unavailable, falling back to MemoryStorage')
            return MemoryStorage()
        raise

    redis_connect = dict(getattr(settings, 'BOT_FSM_REDIS_CONNECT', settings.REDIS_CONNECT))
    redis_client = aioredis.Redis(**redis_connect)
    key_builder = _redis_key_builder(getattr(settings, 'BOT_FSM_REDIS_PREFIX', 'doverabot:fsm'))
    try:
        return RedisStorage(redis=redis_client, key_builder=key_builder)
    except TypeError:
        return RedisStorage(redis_client, key_builder=key_builder)


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
    dp = Dispatcher(storage=build_fsm_storage())

    me.bot = bot
    me.dp = dp
    me.bot_data = await bot.get_me()
    me.api_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=settings.HTTP_TIMEOUT))
    try:
        from handler_bot import router as router_bot
        from handler_callbacks import router as router_callbacks
        from handler_group import router as router_group
        from handler_offer import router as router_offer
        from handler_rental import router as router_rental
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
            router_rental,
            router_sympas,
            router_relatives,
        )

        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(
            bot,
            polling_timeout=20,
        )
    finally:
        await me.api_session.close()
        me.api_session = None

if __name__ == '__main__':
    asyncio.run(main_())
