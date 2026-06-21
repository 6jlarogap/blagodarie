# telegram-bot/settings.py

# --------------------------------------------------------------
#
# Все параметры ниже могут, а некоторые даже должны быть переназначены в settings_local.py
#

DEBUG = False

# Токен бота в телеграме
#
TOKEN = 'secret'

# Webhook параметры
#
WEBHOOK_HOST = 'https://bot.doverabot.ru'
WEBHOOK_PATH = '/'
WEBAPP_HOST = '127.0.0.1'
WEBAPP_PORT = 3001

import logging
LOG_CONFIG = dict(
    level = logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
    datefmt='%d.%m.%y %H:%M:%S',

    # Могут быть и другие параметры для журнала,
    # например, для ротируемого журнала в файл
    # Тогда надо переопределить параметры LOG_CONFIG['handlers'] в
    # settings_local.py, например:
    # from logging.handlers import RotatingFileHandler
    # from settings import LOG_CONFIG
    # LOG_CONFIG['handlers'] = [
    #         StreamHandler(),
    #         RotatingFileHandler(
    #             filename='/home/user/tg-bot-log/tg-bot.log',
    #             maxBytes=10*1024*1024,
    #             backupCount=10,
    # )]
)


# secs
#
HTTP_TIMEOUT = 60

# Сообщение из многих валит одно за другим.
# Мы сначала одно за другим пишем в базу, потом просим апи
# выдать полученное. Т.е. этот максимальное время на обработку одного
# сообщения, + чтоб записать его в базу (но это мелочь по сравнению
# с получением длинного медиафайла).
#
MULTI_MESSAGE_TIMEOUT = 2

# URL апи, без завершающей/, :
#
API_HOST = 'https://api.doverabot.ru'

# Optional external STT adapter for rental voice search.
# Contract `organizm_hermes_v1` sends Telegram file metadata as JSON by default.
# settings_local.py can set RENTAL_STT_URL plus mode 'file_id' or 'download'.
RENTAL_STT_CONTRACT = 'organizm_hermes_v1'
RENTAL_STT_URL = ''
RENTAL_STT_TOKEN = ''
RENTAL_STT_MODE = 'file_id'
RENTAL_STT_LANGUAGE = 'ru'

# Optional geocoding adapter for rental addresses.
# Contract `doverabot_rental_geocoding_v1` sends {"query": "..."} JSON and
# accepts provider responses with result(s)/suggestion(s) containing lat/lon.
RENTAL_GEOCODING_CONTRACT = 'doverabot_rental_geocoding_v1'
RENTAL_GEOCODING_URL = ''
RENTAL_GEOCODING_TOKEN = ''
RENTAL_GEOCODING_LIMIT = 3
RENTAL_GEOCODING_SEARCH_DELTA = 0.05

# - домен, прописанный в боте
#
FRONTEND_HOST = 'https://doverabot.ru'

# Карта участников знакомств
#
MEET_HOST = FRONTEND_HOST

# Карта всех пользователей с кластеризацией.
# При других get параметрах карта предложений, доверий юзера и др.
#
MAP_HOST = 'https://map.doverabot.ru'

# Ссылка на пространство доверия
# И там находятся ресурсы: <GRAPH_HOST>/res/telegram-bot/*.txt
#
GRAPH_HOST = 'https://d3.doverabot.ru'

# Рисуем графики в формате '3d-force-graph' здесь
# для участников игры знакомств
#
GRAPH_MEET_HOST = 'https://mgraph.doverabot.ru'

# Ссылка на фронте, которая будет открываться там под авторизованным
# пользователем:
# <FRONTEND_HOST><FRONTEND_AUTH_PATH>?redirect_path=<frontend_path>
#
FRONTEND_AUTH_PATH = '/auth/telegram/'

SHORT_ID_LINK = 'doverabot.ru/t/%s'

# Админитраторы бота, их telegram ids
#
BOT_ADMINS = ()

# Выбираем из фото пользователей, которые шлют сообщения в бот, не меньше такого, в байтах:
#
PHOTO_MAX_SIZE = 320 * 320

# Загружаемые фото owned users, например, родственников
# Мб. Если 0 или None, без ограничений.
#
DOWNLOAD_PHOTO_MAX_SIZE = 10

# Минимальный размер сообщения для полнотекстового поиска:
#
MIN_LEN_SEARCHED_TEXT = 3

OFFER_MAX_NUM_ANSWERS = 9

# Подсказки в сообщении о необходимости авторизации для доменов
#
AUTH_PROMPT_FOR_DOMAIN = {
    'doverabot.ru': 'Для доступа к пространству Доверия требуется авторизация',
}

# Страница голосования по видео
#
VOTE_URL = 'https://6jlarogap.github.io/razum/'

REDIS_CONNECT =dict(
    # Параметры инициализации redis connection,
    # те же, что в redis.Redis()
    # https://redis-py.readthedocs.io/en/stable/connections.html
    #
    host='127.0.0.1',
    port=6379,
    db=2,
    decode_responses=True,
)

# Durable aiogram FSM storage. Redis keeps long rental conversations alive
# across bot restarts; settings_local.py may set BOT_FSM_STORAGE = 'memory'
# for local-only development.
BOT_FSM_STORAGE = 'redis'
BOT_FSM_REDIS_CONNECT = REDIS_CONNECT.copy()
BOT_FSM_REDIS_PREFIX = 'doverabot:fsm'
BOT_FSM_REDIS_FALLBACK_TO_MEMORY = False

# Время, после которого можно еще раз ставить симпатию
#
REDIS_SET_NEXT_SYMPA_WAIT = 3600

# Ид групп, в которые шлём карточки после сообщений участников, с параметрами.
# Например, в группе с таким ид показывать карточки после сообщений юзеров
# в топиках с message_thread_ids
# и хранить карточки keep_hours часов не не больше 48 часов (иначе telegram не удалит)!:
#   GROUPS_WITH_CARDS = {
#     -1001842039923: dict(keep_hours=24, message_thread_ids=(52,)),
#   }
# При bool(keep_hours) == False или при отсутствии keep_hours данные в redis для
# последующего удаления карточек не сохраняются и карточки не удаляются
#
GROUPS_WITH_CARDS = {}

BOT_CHAT = dict(href='https://t.me/+dpxYzCiAqN41MDEy', caption='Чат бота Доверия')

# Ид групп, в которых есть топик, куда кладут видео для их загрузки в youtube.
#
GROUPS_WITH_YOUTUBE_UPLOAD = {}
#
# Например:
# GROUPS_WITH_YOUTUBE_UPLOAD = {
#     # sevGroupTest
#     -1001842039923: dict(
#         auth_data=dict(
#             client_id='client_id',
#             client_secret='client_secret',
#             refresh_token='refresh_token'
#         ),
#         message_thread_id=-1234567890,
#         url_group='https://t.me/+LcTcCWzvjUJmMTMy'
# )}

# Каталог для временных файлов. Должен существовать
#
DIR_TMP = './tmp'

# Параметры времени запуска задач
#
SCHEDULE_CRON = dict(
    # задача:
    cron_remove_cards_in_group = dict(
        # время запуска
        day_of_week='mon-sun', hour=0, minute=1,
    )
)


# Запуск через Telegram API Server,
# например, 'http://localhost:8081'
#
LOCAL_SERVER = None
PROXY = None

try:
    from settings_local import *
except ModuleNotFoundError:
    pass

logging.basicConfig(**LOG_CONFIG)
