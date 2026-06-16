import os, re, hmac, hashlib, json, time, datetime, copy, string, random
import redis, html
from uuid import uuid4
import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse

from ged4py.parser import GedcomReader

from django.shortcuts import render, redirect
from django.db import transaction, IntegrityError, connection
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.query_utils import Q
from django.db.models import Prefetch, F
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.utils import ProgrammingError
from django.core.validators import URLValidator
from django.views.generic.base import View
from django.db.models.functions import Lower, Collate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied

from app.utils import ServiceException, SkipException, FrontendMixin, FromToCountMixin
from app.models import UnclearDate, PhotoModel, GenderMixin

from django.contrib.auth.models import User
from users.models import Oauth, CreateUserMixin, IncognitoUser, Profile, TgGroup, \
    TempToken, UuidMixin, TelegramApiMixin, \
    TgPoll, TgPollAnswer, Offer, OfferAnswer, TgDesc, \
    OfferRefJournal, OfferRefState, ApiDonateUser
from contact.models import Key, KeyType, CurrentState, OperationType, Wish, Ability, \
                           ApiAddOperationMixin, Journal, TgMessageJournal
from wote.models import Video, Vote

class ApiTokenAuthDataMixin(object):
    """
    Константы, используемые при создании 
    """
    TOKEN_AUTHDATA_PREFIX = 'authdatatoken'
    TOKEN_AUTHDATA_SEP = '~'

    def make_authdata_token(self, auth_data):
        """
        Сделать токен из куки авторизации
        """
        token = None
        if r := redis.Redis(**settings.REDIS_TOKEN_CONNECT):
            token = str(uuid4())
            r.set(
                name=self.TOKEN_AUTHDATA_PREFIX + self.TOKEN_AUTHDATA_SEP + token,
                value=json.dumps(auth_data),
                ex=settings.TOKEN_AUTHDATA_EXPIRE,
            )
            r.close()
        return token


class ApiGetProfileInfo(UuidMixin, APIView):

    def get(self, request):
        """
        Получение информации о профиле пользователя

        Возвращает информацию о пользователе, заданным get- параметром
        uuid: ФИО, фото, известность, общее количество благодарностей,
        количество утрат доверия и др.
        Если в запросе присутствует токен авторизации, то нужно вернуть и
        текущее состояние между пользователем, который запрашивает информацию,
        и пользователем, о котором он запрашивает информацию.

        Пример вызова:
        /api/getprofileinfo?uuid=9e936638-3c48-4e7b-bab4-7f968824acd5
        /api/getprofileinfo : для авторизованного пользователя

        Пример возвращаемых данных:
        {
            "first_name": "Иван",
            "middle_name": "Иванович",
            "last_name": "Иванов",
            "photo": "photo/url",
            "sum_thanks_count": 300,
            "fame": 3,
            "mistrust_count": 1,
            "is_notified": True,
            "trust_count": 3,
            "acq_count": 1,
            "is_active": true,
        }
        """

        try:
            uuid=request.GET.get('uuid')
            if uuid:
                user, profile = self.check_user_uuid(uuid)
            else:
                if request.user.is_authenticated:
                    user = request.user
                    profile = user.profile
                else:
                    raise ServiceException("Не задан uuid или пользователь не вошел в систему")
            data = profile.data_dict(request)
            status_code = 200
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_get_profileinfo = ApiGetProfileInfo.as_view()

class ApiDownloadApkDetails(APIView):
    """
    Получить с github каталога данные о последней версии мобильного приложения
    """

    def post(self, request):
        try:
            header_signature = 'X-Hub-Signature'
            encoding_eq_signature = request.headers.get('X-Hub-Signature')
            if not encoding_eq_signature:
                raise ServiceException('No "%s" header with signature' % header_signature)
            encoding_eq_signature = encoding_eq_signature.lower()
            payload = request.body
            # Do not use any request.data stuff after that!

            # Example of encoding_signature:
            # 'sha1=5aaabbbcccdddeeefff11122233344455fffaaaa'
            #
            m = re.search(r'^([^\=]+)\=([^\=]+)$', encoding_eq_signature)
            if not m:
                raise ServiceException('Invalid "%s" header' % header_signature)
            encoding = getattr(hashlib, m.group(1), None)
            if not encoding:
                raise ServiceException('No "<encoding>=" in "%s" header' % header_signature)
            key = settings.GITHUB_WEBHOOK_SECRET
            key = key.encode('utf-8')
            if hmac.new(key, payload, encoding).hexdigest().lower() != m.group(2):
                raise ServiceException('Request is not properly signed')

            try:
                req = urllib.request.Request(settings.APK_OPTIONS_URL)
                response = urllib.request.urlopen(req, timeout=20)
                raw_data = response.read()
            except urllib.error.HTTPError as excpt:
                raise ServiceException('HTTPError: %s' % settings.APK_OPTIONS_URL)
            except urllib.error.URLError as excpt:
                raise ServiceException('URLError: %s' % settings.APK_OPTIONS_URL)
            fname = os.path.join(settings.MEDIA_ROOT, settings.APK_OPTIONS_DOWNLOAD)
            try:
                with open(fname, 'wb') as f:
                    f.write(raw_data)
            except IOError:
                raise ServiceException('Ошибка настройки сервера, не удалось записать в файл: %s' % fname)
            data = dict(message='Success: downloaded %s into %s' % (
                settings.APK_OPTIONS_URL,
                fname,
            ))
            status_code = 200
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_download_apk_details = ApiDownloadApkDetails.as_view()

class ApiGetLatestVersion(APIView):

    def get(self, request):
        """
        Получить последнюю версию кода апк

        Запрос возвращает последнюю версию кода апк,
        а также анонимный публичный ключ пользователя и
        таймштамп публичного ключа,
        соответствующих полученного приватному ключу
        в get параметре incognito_private_key
        """
        try:
            data = dict(
                url=settings.APK_URL,
                incognito_public_key=None,
                incognito_public_key_timestamp=None,
            )
            try:
                with open(os.path.join(settings.MEDIA_ROOT, settings.APK_OPTIONS_DOWNLOAD), 'r') as f:
                    raw_output = f.read()
            except IOError:
                raise ServiceException('Не нашел, не смог прочитать output.json')
            try:
                output = json.loads(raw_output)
            except ValueError:
                raise ServiceException('Неверные данные в output.json')
            try:
                data.update(
                    version_code=output['elements'][0]['versionCode'],
                    version_name=output['elements'][0]['versionName'],
                    google_play_url=settings.GOOGLE_PLAY_URL,
                    google_play_update=settings.GOOGLE_PLAY_UPDATE,
                )
            except (KeyError, IndexError,):
                raise ServiceException('Не нашел данные о версии мобильного приложения в output.json')
            private_key = request.GET.get('incognito_private_key')
            if private_key:
                try:
                    incognitouser = IncognitoUser.objects.get(private_key=private_key)
                    public_key = incognitouser.public_key
                    if public_key:
                        data['incognito_public_key'] = public_key
                        data['incognito_public_key_timestamp'] = incognitouser.update_timestamp
                except IncognitoUser.DoesNotExist:
                    pass
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 500
        return Response(data=data, status=200)

api_latest_version = ApiGetLatestVersion.as_view()

class ApiDownloadRatingApkDetails(APIView):
    """
    Получить с github каталога данные о последней версии мобильного приложения rating
    """

    def post(self, request):
        try:
            header_signature = 'X-Hub-Signature'
            encoding_eq_signature = request.headers.get('X-Hub-Signature')
            if not encoding_eq_signature:
                raise ServiceException('No "%s" header with signature' % header_signature)
            encoding_eq_signature = encoding_eq_signature.lower()
            payload = request.body
            # Do not use any request.data stuff after that!

            # Example of encoding_signature:
            # 'sha1=5aaabbbcccdddeeefff11122233344455fffaaaa'
            #
            m = re.search(r'^([^\=]+)\=([^\=]+)$', encoding_eq_signature)
            if not m:
                raise ServiceException('Invalid "%s" header' % header_signature)
            encoding = getattr(hashlib, m.group(1), None)
            if not encoding:
                raise ServiceException('No "<encoding>=" in "%s" header' % header_signature)
            key = settings.RATING_GITHUB_WEBHOOK_SECRET
            key = key.encode('utf-8')
            if hmac.new(key, payload, encoding).hexdigest().lower() != m.group(2):
                raise ServiceException('Request is not properly signed')

            try:
                ref = json.loads(payload)['ref']
            except (ValueError, KeyError,):
                raise ServiceException('No ref element in payload or invalid payload')
            m = re.search(r'^refs/heads/(%s)$' % settings.RATING_APK_BRANCHES, ref)
            if not m:
                raise ServiceException('Invalid ref element in payload or invalid branch value in ref')
            branch = m.group(1)

            apk_options_url = settings.RATING_APK_OPTIONS_URL % dict(
                branch=branch,
                build='debug' if branch == 'dev' else 'release',
            )
            apk_options_download = settings.RATING_APK_OPTIONS_DOWNLOAD % dict(branch=branch)
            try:
                req = urllib.request.Request(apk_options_url)
                response = urllib.request.urlopen(req, timeout=20)
                raw_data = response.read()
            except urllib.error.HTTPError as excpt:
                raise ServiceException('HTTPError: %s' % apk_options_url)
            except urllib.error.URLError as excpt:
                raise ServiceException('URLError: %s' % apk_options_url)
            fname = os.path.join(settings.MEDIA_ROOT, apk_options_download)
            try:
                with open(fname, 'wb') as f:
                    f.write(raw_data)
            except IOError:
                raise ServiceException('Ошибка настройки сервера, не удалось записать в файл: %s' % fname)
            data = dict(message='Success: downloaded %s into %s' % (
                apk_options_url,
                fname,
            ))
            status_code = 200
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_download_rating_apk_details = ApiDownloadRatingApkDetails.as_view()

class ApiGetRatingLatestVersion(APIView):

    def get(self, request):
        """
        Получить последнюю версию кода апк Rating
        """
        rating_apk_options_download = settings.RATING_APK_OPTIONS_DOWNLOAD % dict(
            branch=settings.RATING_APK_BRANCH,
        )
        try:
            try:
                with open(os.path.join(settings.MEDIA_ROOT, rating_apk_options_download), 'r') as f:
                    raw_output = f.read()
            except IOError:
                raise ServiceException('Не нашел, не смог прочитать output-metadata.json')
            try:
                output = json.loads(raw_output)
            except ValueError:
                raise ServiceException('Неверные данные в output-metadata.json')
            try:
                apk_fname = output['elements'][0]['outputFile']
                rating_apk_url = settings.RATING_APK_URL % dict(
                    branch=settings.RATING_APK_BRANCH,
                    apk_fname=apk_fname,
                    build='debug' if settings.RATING_APK_BRANCH == 'dev' else 'release',
                )
                data = dict(
                    path=rating_apk_url,
                    version_code=output['elements'][0]['versionCode'],
                    version_name=output['elements'][0]['versionName'],
                    rating_google_play_update=settings.RATING_GOOGLE_PLAY_UPDATE,
                )
            except (KeyError, IndexError,):
                raise ServiceException('Не нашел данные о версии мобильного приложения в output.json')
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 500
        return Response(data=data, status=200)

api_rating_latest_version = ApiGetRatingLatestVersion.as_view()

class ApiAuthSignUpIncognito(APIView):

    @transaction.atomic
    def post(self, request):
        """
        Создание анонимного пользователя

        На вход поступает, например:
        {
            "incognito": {
                "private_key": "becd79d8-9741-4d23-88fe-9c6a75ac881e",
                "public_key": "cf81884f-be1e-401e-a90b-1f70e2295a73"
            }
        }
        Возвращает:
        {
            "incognito_user_id": 12345
        }
        В таблице IncognitoUser создает запись с полученными ключами,
        если таковой не существует, либо, если запись с таким private_key уже существует,
        и при этом public_key пуст, то устанавливает public_key равным полученному значению
        """
        try:
            incognito = request.data.get('incognito')
            if not incognito or not incognito.get('private_key'):
                raise ServiceException('Не задан incognito ии incognito.private_key')
            try:
                incognito_user, created_ = IncognitoUser.objects.get_or_create(
                    private_key=incognito['private_key'].lower(),
                    defaults = dict(
                        public_key=incognito.get('public_key') and incognito['public_key'].lower() or None,
                ))
                if not created_ and 'public_key' in incognito:
                    public_key = incognito['public_key'] and incognito['public_key'].lower() or None
                    if incognito_user.public_key != public_key:
                        incognito_user.public_key = public_key
                        incognito_user.save()
                data = dict(
                    incognito_user_id = incognito_user.pk,
                )
                status_code = 200
            except IntegrityError:
                raise ServiceException('Не выполнено условие уникальности ключа')
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_auth_signup_incognito = ApiAuthSignUpIncognito.as_view()

class ApiAuthTelegram(CreateUserMixin, TelegramApiMixin, FrontendMixin, ApiTokenAuthDataMixin, APIView):
    """
    Callback функция авторизации через telegram

     Принимает, при post запросе:
     {
        "id": 78342834,
        "first_name": Иван",
        "last_name": "Петров",
        "username": "petrov",
        "photo_url": "https://t.me/i/userpic/320/92dcFhXhdjdjdjFwsiBzo1_M9HT-fyfAxJhoY.jpg",
        "auth_date": 1615848699,
        "hash": "bfdd33573729c511ad5bb969487b2e2ce9714e88cd8268929c010711ede3ed5d"
        # необязательно
        "redirect_path: путь к <frontend-url>/, например "/profile/id=....'
     }
     При get запросе: аналогичные данные в строке запроса

    Проверяет правильность данных по hash,
    создает нового пользователя из telegram с id, при необходимости,

    Возвращает:
        при отсутствии redirect_path:
            {
                "user_uuid": <uuid пользователеля>,
                "auth_token": <его токен авторизации>,
            }
        при наличиии дополнительного параметра redirect_path, который подставляет не телеграм,
        а фронт, который может вызывать этот метод:
            перенаправляет на:
                <frontend>/<redirect_path>, если redirect_path не начинается с http,
                redirect_path, если это https://...,
            подставляя в redirect_path дополнительно параметр:
                authdata_token=....,
                в котором зашита кука авторизации
        при наличиии дополнительного параметра keep_user_data, который подставляет не телеграм,
        а фронт, который может вызывать этот метод:
            данные пользователя (фио, фото) не меняются в профиле (Profile, User) пользователя.
            Это требуется, когда метод вызывается при авторизации, иницированной login url
            из бота телеграма. В боте пользователь может изменить и своё фио в таблице User,
            и свое фото в таблице Profile, зачем же здесь переписывать его сведения.
            Некоторое исключение для фото: если фото не было задано в Profile, оно таки заносится.
    """

    def check_input(self, request):
        if request.method == 'POST':
            rd = request.data
        elif request.method == 'GET':
            rd = request.GET
        msg_invalid_request = 'Неверный запрос'
        try:
            if not rd or not rd.get('auth_date') or not rd.get('hash') or not rd.get('id'):
                raise ServiceException(msg_invalid_request)
        except AttributeError:
            raise ServiceException(msg_invalid_request)
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ServiceException('В системе не определен TELEGRAM_BOT_TOKEN')

        request_data = rd.copy()
        unix_time_now = int(time.time())
        unix_time_auth_date = int(rd['auth_date'])
        if unix_time_now - unix_time_auth_date > settings.TELEGRAM_AUTH_DATA_OUTDATED:
            raise ServiceException('Неверный запрос, данные авторизации устарели')

        request_data.pop("hash", None)
        for parm in ('redirect_path', 'keep_user_data',):
            try:
                request_data.pop(parm, None)
            except KeyError:
                pass
        request_data_alphabetical_order = sorted(request_data.items(), key=lambda x: x[0])
        data_check_string = []
        for data_pair in request_data_alphabetical_order:
            key, value = data_pair[0], data_pair[1]
            data_check_string.append(key + "=" + str(value))
        data_check_string = "\n".join(data_check_string)
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        calculated_hash = hmac.new(
            secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if calculated_hash != rd['hash']:
            raise ServiceException('Неверный запрос, данные не прошли проверку на hash')
        return rd

    def process_input(self, rd):
        photo_url = rd.get('photo_url', '')
        try:
            oauth = Oauth.objects.select_related('user', 'user__profile').get(
                provider = Oauth.PROVIDER_TELEGRAM,
                uid=rd['id'],
            )
            # При повторном логине проверяется, не изменились ли данные пользователя
            #
            user = oauth.user
            profile = user.profile
            keep_user_data = rd.get('keep_user_data')

            oauth_tg_field_map = dict(
                last_name='last_name',
                first_name='first_name',
                username='username',
                photo='photo_url',
            )
            changed = False
            for f in oauth_tg_field_map:
                if getattr(oauth, f) != rd.get(oauth_tg_field_map[f], ''):
                    changed = True
                    break
            if changed:
                for f in oauth_tg_field_map:
                    setattr(oauth, f, rd.get(oauth_tg_field_map[f], ''))
                oauth.update_timestamp = int(time.time())
                oauth.save()

            was_not_active = False
            if not user.is_active:
                changed = True
                user.is_active = True
                was_not_active = True
            if user.last_name != '':
                user.last_name = ''
                changed = True
            if was_not_active or not keep_user_data:
                first_name = Profile.make_first_name(rd['last_name'], rd['first_name'])
                if user.first_name != first_name:
                    user.first_name = first_name
                    changed = True
            if changed:
                user.save()

            if was_not_active and profile.is_notified:
                fio = profile.user.first_name or 'Без имени'
                message = "Cвязанный профиль '%s' восстановлен" % fio
                self.send_to_telegram(message, user=user)

        except Oauth.DoesNotExist:
            last_name = rd.get('last_name', '')
            first_name = rd.get('first_name', '')
            user = self.create_user(
                last_name=last_name,
                first_name=first_name,
            )
            profile = user.profile
            oauth = Oauth.objects.create(
                provider = Oauth.PROVIDER_TELEGRAM,
                uid=rd['id'],
                user=user,
                last_name=last_name,
                first_name=first_name,
                username=rd.get('username', ''),
                photo=photo_url,
            )
        token, created_token = Token.objects.get_or_create(user=user)

        if photo_url:
            put_photo_from_url = False
            if not profile.photo:
                put_photo_from_url = True
            elif not keep_user_data and oauth.photo != photo_url:
                put_photo_from_url = True
            if put_photo_from_url:
                profile.put_photo_from_url(photo_url)
        return dict(
            user_id=user.pk,
            user_uuid=str(user.profile.uuid),
            auth_token=token.key,
        )

    def do_redirect(self, request, rd, data):
        redirect_path = rd.get('redirect_path')
        if redirect_path:
            if redirect_path.lower().startswith('http'):
                redirect_to = redirect_path
            else:
                redirect_to = self.get_frontend_url(
                request=request,
                path=redirect_path,
            )
            auth_data = dict(provider=Oauth.PROVIDER_TELEGRAM, )
            auth_data.update(data)
            token = self.make_authdata_token(auth_data)
            urlparse_result = urlparse(redirect_to)
            if urlparse_result.query:
                query_new = urlparse_result.query + '&authdata_token=' + token
            else:
                query_new = 'authdata_token=' + token
            urlparse_result = urlparse_result._replace(query=query_new)
            redirect_to = urlparse_result.geturl()
            response = redirect(redirect_to)
            return response
        else:
            return None

    @transaction.atomic
    def process_request(self, request):
        try:
            # request data, got by GET or POST
            #
            rd = self.check_input(request)

            # output data
            #
            data = self.process_input(rd)

            # redirect with output data as cookie или return output data
            #
            redirected_response = self.do_redirect(request, rd, data)
            if redirected_response:
                return redirected_response

            status_code = 200
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

    def get(self, request):
        return self.process_request(request)

    def post(self, request):
        return self.process_request(request)

api_auth_telegram = ApiAuthTelegram.as_view()

class ApiOauthCallback(FrontendMixin, CreateUserMixin, APIView):

    OAUTH_PROVIDERS = {
        Oauth.PROVIDER_YANDEX: {
            # В вызове от провайдера могут прийти get параметры
            # имена которых для разных провайдеров могут отличаться
            #   'm_error': 'error',
            #   'm_error_description': 'error_description',

            # Имена полей для запроса токена, если они
            # отличаются от стандартных:
            #   't_grant_type': 'grant_type',
            #   't_authorization_code' = 'authorization_code',
            #   't_code': 'code',
            #   't_client_id': 'client_id',
            #   't_client_secret': 'client_secret',

            # Куда идём за токеном:
            #
            'request_token_url': 'https://oauth.yandex.ru/token',

            # Как идём за токеном, GET или POST
            #
            # 'request_token_method': 'POST',

            # Нужно ли добавлять redirect_uri и как может называться
            # redirect_uri.
            # Если не задан или пуст, то redirect_uri=<redirect_uri>
            # не добавляется в запрос токена
            #   't_redirect_uri': None,

            # В ответ ожидаем 'access_token': ..., но имя параметра
            # может отличаться
            #
            #   't_access_token': 'access_token',
        },
        Oauth.PROVIDER_VKONTAKTE: {
            'request_token_url': 'https://oauth.vk.com/access_token',
            'request_token_method': 'GET',
            't_redirect_uri': 'redirect_uri',
        },
        Oauth.PROVIDER_ODNOKLASSNIKI: {
            'request_token_url': 'https://api.ok.ru/oauth/token.do',
            't_redirect_uri': 'redirect_uri',
        },
    }

    @transaction.atomic
    def get(self, request, provider):
        """
        Callback функция для различных Oauth2 провайдеров (yandex, vk...)
        """
        try:
            s_provider = settings.OAUTH_PROVIDERS.get(provider)
            d_provider = self.OAUTH_PROVIDERS.get(provider)
            if not s_provider or not d_provider:
                return redirect(self.get_frontend_url(request) + '?error=provider_not_implemetnted')

            redirect_from_callback = self.get_frontend_url(request, settings.REDIRECT_FROM_CALLBACK)

            m_error = d_provider.get('m_error') or 'error'
            m_error_description = d_provider.get('m_error_description') or 'error_description'
            s_error = request.GET.get(m_error)
            if s_error:
                s_errors = '?error=%s' % urllib.parse.quote_plus(s_error)
                s_error_description = request.GET.get(m_error_description)
                if s_error_description:
                    s_errors += '&' + 'error_description=%s' % urllib.parse.quote_plus(s_error_description)
                return redirect(redirect_from_callback + s_errors)

            code = request.GET.get('code')
            if not code:
                return redirect(redirect_from_callback + '?error=no_code_received_in_callback')

            d_post_for_token = {}
            if provider in (Oauth.PROVIDER_YANDEX, Oauth.PROVIDER_ODNOKLASSNIKI):
                t_grant_type = d_provider.get('t_grant_type') or 'grant_type'
                t_authorization_code = d_provider.get('t_authorization_code') or 'authorization_code'
                d_post_for_token[t_grant_type] = t_authorization_code

            t_code = d_provider.get('t_code') or 'code'
            d_post_for_token[t_code] = code
            t_client_id = d_provider.get('t_client_id') or 'client_id'
            d_post_for_token[t_client_id] = s_provider['client_id']
            t_client_secret = d_provider.get('t_client_secret') or 'client_secret'
            d_post_for_token[t_client_secret] = s_provider['client_secret']

            t_redirect_uri = d_provider.get('t_redirect_uri')
            if t_redirect_uri:
                redirect_uri = request.build_absolute_uri()
                redirect_uri = re.sub(r'\?.*$', '', redirect_uri)
                d_post_for_token[t_redirect_uri] = redirect_uri

            t_request_token_method = d_provider.get('t_request_token_method') or 'POST'
            d_post_for_token = urllib.parse.urlencode(d_post_for_token)
            d_post_for_token = d_post_for_token.encode()
            if t_request_token_method == 'POST':
                req_post_for_token = urllib.request.Request(
                    d_provider['request_token_url'],
                    d_post_for_token
                )
            else:
                # GET, для vk
                req_post_for_token = urllib.request.Request(
                    d_provider['request_token_url'] + '?' + \
                    d_post_for_token
                )

            s_errors = '?error=error_getting_token_from_%s' %provider
            t_access_token = d_provider.get('t_access_token') or 'access_token'
            try:
                response_post_for_token = urllib.request.urlopen(req_post_for_token)
                raw_data = response_post_for_token.read().decode(
                    response_post_for_token.headers.get_content_charset('utf-8')
                )
                data = json.loads(raw_data)
                access_token = data.get(t_access_token)
                if not access_token:
                    return redirect(redirect_from_callback + s_errors)
            except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
                return redirect(redirect_from_callback + s_errors)

            oauth_dict = dict(
                provider=provider,
                token=access_token,
            )

            oauth_result = Oauth.check_token(oauth_dict)
            if oauth_result['message']:
                s_errors = '?error=error_getting_user_data_by_token'
                s_errors += '&' + 'error_description=%s' % \
                        urllib.parse.quote_plus(oauth_result['message'])
                return redirect(redirect_from_callback + s_errors)

            try:
                oauth = Oauth.objects.select_related(
                    'user',
                    'user__profile',
                    'user__auth_token',
                ).get(
                    provider=provider,
                    uid=oauth_result['uid'],
                )
                user = oauth.user
            except Oauth.DoesNotExist:
                user = self.create_user()
                oauth = Oauth.objects.create(
                    provider=provider,
                    uid=oauth_result['uid'],
                    user=user,
                )
                Token.objects.create(user=user)
            self.update_oauth(oauth, oauth_result)

            response = redirect(redirect_from_callback)
            to_cookie = dict(
                provider=provider,
                user_id=user.pk,
                user_uuid=str(user.profile.uuid),
                auth_token=user.auth_token.key
            )
            response.set_cookie(
                key='auth_data',
                value=json.dumps(to_cookie),
                max_age=600,
                path='/',
                domain=self.get_frontend_name(request),
            )
            return response
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = 400
            return Response(data=data, status=status_code)

api_oauth_callback = ApiOauthCallback.as_view()

class ApiUpdateFrontendSite(APIView):
    """
    Получить с github каталога сигнал об обновлении ветки frontend site и обновить эту ветку
    """

    def post(self, request):
        try:
            header_signature = 'X-Hub-Signature'
            encoding_eq_signature = request.headers.get('X-Hub-Signature')
            if not encoding_eq_signature:
                raise ServiceException('No "%s" header with signature' % header_signature)
            encoding_eq_signature = encoding_eq_signature.lower()
            payload = request.body
            # Do not use any request.data stuff after that!

            # Example of encoding_signature:
            # 'sha1=5aaabbbcccdddeeefff11122233344455fffaaaa'
            #
            m = re.search(r'^([^\=]+)\=([^\=]+)$', encoding_eq_signature)
            if not m:
                raise ServiceException('Invalid "%s" header' % header_signature)
            encoding = getattr(hashlib, m.group(1), None)
            if not encoding:
                raise ServiceException('No "<encoding>=" in "%s" header' % header_signature)
            key = settings.FRONTEND_GITHUB_WEBHOOK_SECRET
            key = key.encode('utf-8')
            if hmac.new(key, payload, encoding).hexdigest().lower() != m.group(2):
                raise ServiceException('Request is not properly signed')

            try:
                ref = json.loads(payload)['ref']
            except (ValueError, KeyError,):
                raise ServiceException('No ref key in payload or invalid payload')
            m = re.search(r'^refs/heads/([\w\-]+)$', ref)
            if not m:
                raise ServiceException("Invalid 'ref' value")
            branch = m.group(1)
            script = settings.FRONTEND_UPDATE_SCRIPT.get(branch)
            if not script:
                raise ServiceException("Unknown branch '%s' in frontend github repository" % branch)
            rc = os.system(script)
            if rc:
                raise ServiceException("Update script '%s' failed, rc = %s" % (script, rc,))
            data = dict(message="Success: updated branch '%s'" % branch)
            status_code = 200
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_update_frontend_site = ApiUpdateFrontendSite.as_view()

class ApiInviteGetToken(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        token = TempToken.create(
            type_=TempToken.TYPE_INVITE,
            obj=request.user,
            ttl=86400*31,
        )
        token.save(force_insert=True)
        data = dict(token=token.token)
        status_code = status.HTTP_200_OK
        return Response(data=data, status=status_code)

api_invite_get_token = ApiInviteGetToken.as_view()

class ApiProfile(CreateUserMixin, UuidMixin, GenderMixin, FrontendMixin, TelegramApiMixin, ApiAddOperationMixin, APIView):
    """
    Получить своих родственников (без связей), добавить/править/обезличить родственника. Правка своего профиля.

    GET
        Не требует авторизации
        без параметров:
            получить всех родственников авторизованного пользователя,
            массив json структур в формате, см. метод PUT.
            Возможны параметры для пагинации запроса: from (по умолчанию 0):
            с какого начинать, number (по умолчанию 50) сколько на странице.
            На любой странице будут еще данные авторизованного пользователя,
            если запрос авторизован.
        с параметром uuid=...
            получить данные по одному пользователю, необязательно родственнику,
        с параметром username=... (short id)
            получить данные по одному пользователю по его username
        с параметром tg_uid=...
            получить данные по пользователю телеграма
        с параметром tg_uids=...
            получить данные по пользователям телеграма, список с разделителями
            запятой, более короткая выборка, нежели по одному tg_uid
        с параметром owner_uuid=...
            получить массив данных по всем собственным профилям того uuid
                если еще параметр name_iexact:
                    пустой массив или содержащий данные собственного
                    профиля с first_name = name_exact
        с одним из параметров query, query_ability, query_wish, query_person:
            получить список профилей пользователей,
                - найденных по фио и ключам (query_person),
                - возможностям (query_ability),
                - потребностям (query_wish)
                - или по фио и ключам (query)
                При этом возможны еще параметры:
                from
                    (default 0), начиная с какой записи
                number.
                    Сколько записей отдавать. По умолчанию без ограничений
                thumb_size
                    если не пустой, то включать еще и thumb_url, квадрат этой ширины и длины.
                    Thumbnail можем делать только от файлов, которые лежат в апи.
                    Если фото имеется только от других источников (телеграм, google),
                    то берется оттуда полное фото
                operation: and или or, искать по И или ИЛИ
        с параметром tg_username:
            Это строка telegram @usernames (без @ вначале), разделенных запятой
            например, username1,username2 ...
            Ищем у нас в базе все эти телеграм- usernames, возвращаем
            "карточки пользователей", включая их telegram id
            заодно вернуть abilities, wishes, keys

    PUT
        Править родственника или себя.
        Если задан верный tg_token: токен бота, то не требует авторизации.
        Иначе требует авторизации
        На входе:
        form-data. Или multipart/form-data при наличии файла фото.
        При отсутствии файла photo можно передать в json структуре
            uuid:
                # обязательно
                # остальные поля могут отсутствовать. По отсутствующим полям
                # правка профиля не производится
            last_name
            first_name
            middle_name
            gender
            dob: дата рождения
                # гггг-мм-дд, гггг-мм, гггг или пустая строка (удаляет дату)
            dob: дата смерти
                # гггг-мм-дд, гггг-мм, гггг или пустая строка (удаляет дату)
            photo:
                # файл фото или строка:
                    - base64 encoded строка,
                    - файл с base64-encoded содержимым,
                    - “обычный” файл фото.
                  Размер строки/файла не должен превышать 10Мб
                  (для base64- строки/файла - не более 10Мб *4/3).
                    - или пустая строка, тогда текущее фото, если имеется, то удаляется
    POST
        * Добавить активного пользователя из бота телеграма.
            Не требует авторизации.
            На входе:
            Обязательны:
                tg_token: токен бота. Такой же записан в настройках АПИ
                tg_uid: uid пользователя в телеграме
                В этом случае не обязательны:
                    last_name
                    first_name
                    username
                        пользователя в телеграме
                    photo
                        путь, который можно включить в ссылку (действует 1 час):
                        https://api.telegram.org/file/bot<tg_token>/<tg_photo_path>,
                        скачать фото, записать в фото профиля.
                    activate
                        активировать пользователя, если был обезличен

        * Добавить родственника.
            - если из телеграм бота, обязательны:
                tg_token: токен бота. Такой же записан в настройках АПИ
                owner_id: id пользователя, владельца
            - иначе требует авторизации.
        На входе:
        form-data. Или multipart/form-data при наличии файла фото.
        При отсутствии файла photo можно передать в json структуре
            last_name
            first_name
                # Наличие last_name или first_name обязательно
                # остальные поля могут отсутствовать. По отсутствующим полям
                # заносятся пустые или null значения
            middle_name
            gender
            dob: дата рождения
                # гггг-мм-дд, гггг-мм, гггг или пустая строка (дата отсутствует)
            dob: дата смерти
                # гггг-мм-дд, гггг-мм, гггг или пустая строка (дата отсутствует)
            photo:
                # файл фото или строка:
                    - base64 encoded строка,
                    - файл с base64-encoded содержимым,
                    - “обычный” файл фото.
                  Размер строки/файла не должен превышать 10Мб
                  (для base64- строки/файла - не более 10Мб *4/3).

        Возможно вместе с созданием родственника сразу указать степень его родства
        к существующему пользователю (или пользователю - родственнику)

        link_id (id или uuid)
            родитель или ребенок создаваемого профиля, должен существовать.
        link_relation, одно из:
            new_is_father: создаваемый родич является папой по отношению к link_id
            new_is_mother: создаваемая родственница является мамой по отношению к link_id
            link_is_father: link_id – это папа создаваемого родственника (создаваемой родственницы)
            link_is_mother: link_id – это мама создаваемого родственника (создаваемой родственницы)

        Если заданы link_id & link_relation, то новый пользователь становится прямым
        родственником по отношению к link_id. Вид родства, см. link_relation.
        Задать таким образом родство можно или если link_id
        это сам авторизованный пользователь или его родственник
        (владелец link_id - авторизованный пользователь).
        Иначе ошибка, а если нет недоверия между авторизованным пользователем и
        владельцем link_id или самим link_id, если им никто не владеет,
        то еще и уведомление в телеграм, что кто-то предлагает link_id назначить родственика

    DELETE
        uuid:
            # обязательно
    """

    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def check_dates(self, request):
        dob = request.data.get('dob')
        dod = request.data.get('dod')
        m = UnclearDate.check_safe_str(dob)
        if m:
            raise ServiceException('Дата рождения. %s' % m)
        m = UnclearDate.check_safe_str(dod)
        if m:
            raise ServiceException('Дата смерти. %s' % m)
        dob = UnclearDate.from_str_safe(dob)
        dod = UnclearDate.from_str_safe(dod)
        today = datetime.datetime.now().date()
        if dob is not None and dob > today:
            raise ServiceException(f'Дата рождения: {dob} позже текущей')
        if dod is not None and dod > today:
            raise ServiceException(f'Дата смерти: {dod} позже текущей')
        if dob is not None and dod is not None and dob > dod:
            raise ServiceException(f'Дата рождения: {dob}, позже даты смерти: {dod}')
        return dob, dod

    def get(self, request):
        try:
            data = dict()
            if request.GET.get('tg_uid'):
                try:
                    oauth = Oauth.objects.select_related(
                            'user', 'user__profile', 'user__profile__ability'
                        ).get(uid=request.GET['tg_uid'])
                except Oauth.DoesNotExist:
                    raise ServiceException('Telegram user with uid=%s not found' % request.GET['tg_uid'])
                profile = oauth.user.profile
                data = profile.data_dict(request)
                data.update(tg_data=profile.tg_data())
            elif request.GET.get('uuid'):
                user, profile = self.check_user_uuid(
                    request.GET['uuid'],
                    related=('user', 'ability','owner','owner__profile'),
                )
                data = profile.data_dict(request)
                data.update(profile.parents_dict(request))
                data.update(profile.data_WAK())
                data.update(profile.owner_dict())
                data.update(tg_data=profile.tg_data())
                if request.GET.get('with_owner_tg_data') and profile.owner:
                    data['owner'].update(tg_data=profile.owner.profile.tg_data())
            elif request.GET.get('username'):
                user, profile = self.check_user_username(
                    request.GET['username'],
                    related=('user', 'ability','owner','owner__profile'),
                )
                data = profile.data_dict(request)
                data.update(profile.parents_dict(request))
                data.update(profile.data_WAK())
                data.update(profile.owner_dict())
                data.update(tg_data=profile.tg_data())
                if request.GET.get('with_owner_tg_data') and profile.owner:
                    data['owner'].update(tg_data=profile.owner.profile.tg_data())
            elif request.GET.get('tg_uids'):
                data = []
                uids = request.GET['tg_uids'].split(',')
                user_pks = set()
                for oauth in Oauth.objects.select_related(
                            'user', 'user__profile'
                        ).filter(
                            provider=Oauth.PROVIDER_TELEGRAM,
                            uid__in=uids,
                   ):
                    user = oauth.user
                    if user.pk not in user_pks:
                        # Учтём возможные два тг аккаунта у одного юзера
                        profile = user.profile
                        item = profile.data_dict(request)
                        item.update(tg_data=dict(tg_uid=oauth.uid, tg_username=oauth.username,))
                        data.append(item)
                        user_pks.add(user.pk)
            elif request.GET.get('tg_username'):
                data = []
                usernames = request.GET['tg_username'].split(',')
                user_pks = set()
                q = Q()
                for username in usernames:
                    q |= Q(username__iexact=username)
                q &= Q(provider=Oauth.PROVIDER_TELEGRAM)
                for oauth in Oauth.objects.select_related(
                            'user', 'user__profile'
                    ).filter(q):
                    user = oauth.user
                    if user.pk not in user_pks:
                        # Учтём возможные два тг аккаунта у одного юзера
                        profile = user.profile
                        item = profile.data_dict(request)
                        item.update(profile.parents_dict(request))
                        item.update(profile.data_WAK())
                        item.update(profile.owner_dict())
                        item.update(tg_data=profile.tg_data())
                        data.append(item)
                        user_pks.add(user.pk)
            elif request.GET.get('query_ability') or \
                 request.GET.get('query_wish') or \
                 request.GET.get('query_person') or \
                 request.GET.get('query'):
                data = []
                if request.GET.get('query_ability'):
                    query = request.GET['query_ability']
                    fields = ('ability__text',)
                    mode = 'fulltext'
                elif request.GET.get('query_wish'):
                    query = request.GET['query_wish']
                    fields = ('wish__text',)
                    mode = 'fulltext'
                elif request.GET.get('query_person'):
                    query = request.GET['query_person']
                    fields = ('first_name', )
                    mode = 'icontains'
                else:
                    # аналог query_person
                    query = request.GET['query']
                    fields = ('first_name', )
                    mode = 'icontains'
                if len(query) >= settings.MIN_LEN_SEARCHED_TEXT:
                    operation = request.GET.get('operation', 'and')
                    if operation not in ('and', 'or'):
                        # default:
                        operation = 'and'
                    words = query.split()
                    if mode == 'fulltext':
                        sep = ' & ' if operation == 'and' else ' | '
                        query = sep.join(words)
                    else:
                        # icontains
                        for i, word in enumerate(words):
                            words[i] = re.escape(words[i].lower().replace('ё', 'е')).replace('е','[её]')
                            for j, field in enumerate(fields):
                                dict_regex = {('%s__iregex' % fields[j]): words[i]}
                                if j == 0:
                                    q_word = Q(**dict_regex)
                                else:
                                    q_word |= Q(**dict_regex)
                            if i == 0:
                                q_icontains = q_word
                            else:
                                if operation == 'and':
                                    q_icontains &= q_word
                                else:
                                    q_icontains |= q_word
                    try:
                        from_ = int(request.GET.get('from', 0) or 0)
                    except (ValueError, TypeError,):
                        from_ = 0
                    try:
                        number = int(request.GET.get('number', 0) or 0)
                    except (ValueError, TypeError,):
                        number = 0
                    try:
                        thumb_size = int(request.GET.get('thumb_size', 0) or 0)
                    except (ValueError, TypeError,):
                        thumb_size = 0
                    try:
                        q_active = Q(is_superuser=False) & (Q(is_active=True) | Q(profile__owner__isnull=False))
                        select_related = ('profile',)
                        if mode == 'fulltext':
                            search_vector = SearchVector(*fields, config='russian')
                            search_query = SearchQuery(query, search_type="raw", config='russian')
                            users = User.objects.annotate(
                                search=search_vector
                            ).select_related(*select_related).filter(q_active, search=search_query)
                        else:
                            # icontains
                            users = User.objects.filter(q_active, q_icontains
                            ).select_related(*select_related)
                        # Collate & Lower: чтоб 'Бапинаева Карина' не была рашьше 'Бапинаев Сулейман'
                        users = users.order_by(
                                F('profile__dob').asc(nulls_first=True), Collate(Lower('first_name'), 'C')
                            ).distinct()
                        if number:
                            users = users[from_:from_ + number]
                        for user in users:
                            profile = user.profile
                            item = profile.data_dict(request)
                            if thumb_size:
                                item.update(thumb_url=profile.choose_thumb(
                                    request, width=thumb_size, height=thumb_size,
                                    put_default_avatar=False,
                                ))
                            data.append(item)
                    except ProgrammingError:
                        raise
                        raise ServiceException(
                            'Неверная строка поиска',
                            'programming_error'
                        )
            elif request.GET.get('uuid_owner'):
                data = []
                q_uuid_owner = Q(owner__profile__uuid=request.GET['uuid_owner'])
                if request.GET.get('name_iexact'):
                    q_uuid_owner &= Q(user__first_name__iexact=request.GET['name_iexact'])
                users_selected = Profile.objects.filter(q_uuid_owner). \
                    select_related('user', 'ability',). \
                    order_by(F('dob').asc(nulls_first=True), Collate(Lower('user__first_name'), 'C'))
                for profile in users_selected:
                    data_item = profile.data_dict(request)
                    data_item.update(profile.owner_dict())
                    data.append(data_item)
            else:
                if not request.user.is_authenticated:
                    raise NotAuthenticated
                my_data = [request.user.profile.data_dict(request)]
                try:
                    from_ = abs(int(request.GET.get("from")))
                except (ValueError, TypeError, ):
                    from_ = 0
                try:
                    number_ = abs(int(request.GET.get("number")))
                except (ValueError, TypeError, ):
                    number_ = settings.PAGINATE_USERS_COUNT
                users_selected = Profile.objects.filter(owner=request.user). \
                    select_related('user', 'ability',).order_by(
                        '-user__date_joined',
                    )[from_:from_ + number_]
                data = my_data + [p.data_dict(request) for p in users_selected]
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            try:
                code=excpt.args[1]
            except IndexError:
                code=''
            data.update(code=code)
            status_code = 400
        return Response(data=data, status=status_code)

    def save_photo(self, request, profile):
        if request.data.get('photo'):
            photo_content = request.data.get('photo_content', 'base64')
            photo = PhotoModel.get_photo(
                request=request,
                photo_content=photo_content,
            )
            profile.delete_from_media()
            profile.photo.save(getattr(request.data['photo'], 'name', PhotoModel.DEFAULT_FNAME), photo)

    def post_tg_data(self, request):
        """
        Сделать, если не существует, нового пользователя по telegram id
        """
        profile = None
        data = dict()
        if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
            raise ServiceException('Неверный токен телеграм бота')
        last_name=request.data.get('last_name', '')
        first_name=request.data.get('first_name', '')
        try:
            oauth = Oauth.objects.get(
                provider=Oauth.PROVIDER_TELEGRAM,
                uid=request.data['tg_uid'],
            )
            user = oauth.user
            profile = user.profile
            if user.is_active or request.data.get('activate'):
                save_ = False
                for f in ('last_name', 'first_name', 'username', ):
                    input_val = request.data.get(f, '')
                    if getattr(oauth, f) != input_val:
                        setattr(oauth, f, input_val)
                        save_ = True
                if save_:
                    oauth.update_timestamp = int(time.time())
                    oauth.save()

        except Oauth.DoesNotExist:
            user = self.create_user(
                last_name=last_name,
                first_name=first_name,
            )
            profile = user.profile
            oauth = Oauth.objects.create(
                provider = Oauth.PROVIDER_TELEGRAM,
                uid=request.data.get('tg_uid'),
                user=user,
                last_name=last_name,
                first_name=first_name,
                username=request.data.get('username', ''),
            )
            token, created_token = Token.objects.get_or_create(user=user)
            self.save_photo(request, profile)
            data.update(created=True)

        if request.data.get('did_bot_start') and not profile.did_bot_start:
            # Если пустой did_bot_start, то он не сбрасывается в профиле юзера
            profile.did_bot_start = True
            profile.save(update_fields=('did_bot_start',))

        if not user.is_active and request.data.get('activate'):
            token, created_token = Token.objects.get_or_create(user=user)
            user.last_name = ''
            user.first_name = Profile.make_first_name(last_name, first_name)
            user.is_active = True
            user.save()

        data.update(profile.data_dict(request))
        data.update(profile.parents_dict(request))
        data.update(tg_data=profile.tg_data())
        data.update(profile.owner_dict())
        data.update(profile.data_WAK())
        return data

    @transaction.atomic
    def post(self, request):
        try:
            got_tg_token = False
            status_code = status.HTTP_200_OK
            if request.data.get('tg_token') and request.data.get('tg_uid'):
                data = self.post_tg_data(request)
                raise SkipException

            # Запрос на создание owned user из телеграма ?:
            if request.data.get('tg_token') and request.data.get('owner_id'):
                if request.data['tg_token'] != settings.TELEGRAM_BOT_TOKEN:
                    raise ServiceException('Неверный токен телеграм бота')
                try:
                    owner = User.objects.select_related('profile').get(pk=request.data['owner_id'])
                    owner_profile = owner.profile
                    got_tg_token = True
                except User.DoesNotExist:
                    raise ServiceException('Неверный ид пользователя владельца, для создания owned profile, из телеграм- бота')
            elif not request.user.is_authenticated:
                raise NotAuthenticated
            else:
                owner = request.user
                owner_profile = owner.profile
            if not request.data.get('last_name') and not request.data.get('first_name'):
                raise ServiceException('Фамилия или имя обязательно для нового')
            dob, dod =self.check_dates(request)
            is_dead = bool(request.data.get('is_dead'))
            if dod:
                is_dead = True
            self.check_gender(request)
            link_id = request.data.get('link_id')
            if link_id:
                if self.is_uuid(link_id):
                    link_user, link_profile = self.check_user_uuid(link_id)
                else:
                    link_user, link_profile = self.check_user_id(link_id)
                relation = request.data.get('link_relation', '')
                if relation not in ('new_is_father', 'new_is_mother', 'link_is_father', 'link_is_mother'):
                    raise ServiceException('При заданном link_id не получен или получен неправильный link_relation')
                if not (link_profile.owner == owner or link_user == owner):
                    if link_profile.owner:
                        msg_user_to = link_profile.owner
                    else:
                        msg_user_to = link_user
                    if not CurrentState.objects.filter(
                        user_from__in=(owner, msg_user_to,),
                        user_to__in=(owner, msg_user_to,),
                        user_to__isnull=False,
                        attitude=CurrentState.MISTRUST,
                       ).exists():
                        if link_profile.owner:
                            msg = '%s предлагает указать родственника для %s' % (
                                self.profile_link(request, owner_profile),
                                self.profile_link(request, link_profile),
                            )
                        else:
                            msg = '%s предлагает указать для Вас родственника' % self.profile_link(request, owner_profile)
                        self.send_to_telegram(msg, msg_user_to)
                    raise ServiceException('У Вас нет права указывать родственника к этому профилю')

            gender_new = request.data.get('gender', '').lower() or None
            if link_id:
                msg_female_is_father = 'Женщина не может быть папой'
                msg_male_is_mother = 'Мужчина не может быть мамой'
                gender_link = link_profile.gender or None
                if gender_new is not None:
                    if relation == 'new_is_father' and gender_new == self.GENDER_FEMALE:
                        raise ServiceException(msg_female_is_father)
                    if relation == 'new_is_mother' and gender_new == self.GENDER_MALE:
                        raise ServiceException(msg_male_is_mother)
                if gender_link is not None:
                    if relation == 'link_is_father' and gender_link == self.GENDER_FEMALE:
                        raise ServiceException(msg_female_is_father)
                    if relation == 'link_is_mother' and gender_link == self.GENDER_MALE:
                        raise ServiceException(msg_male_is_mother)

            user = self.create_user(
                last_name=request.data.get('last_name', ''),
                first_name=request.data.get('first_name', ''),
                middle_name=request.data.get('middle_name', ''),
                owner=owner,
                dob=dob,
                is_dead=is_dead,
                dod=dod,
                is_active=False,
                gender=gender_new,
                latitude=request.data['latitude'] if 'latitude' in request.data else None,
                longitude=request.data['longitude'] if 'longitude' in request.data else None,
                is_org = bool(request.data['is_org']) if 'is_org' in request.data else False,
                comment=request.data.get('comment') or None,
            )

            if link_id:
                if relation == 'new_is_father':
                    is_father = True
                    link_user_from = link_user
                    link_user_to = user
                elif relation == 'new_is_mother':
                    is_father = False
                    link_user_from = link_user
                    link_user_to = user
                elif relation == 'link_is_father':
                    is_father = True
                    link_user_from = user
                    link_user_to = link_user
                elif relation == 'link_is_mother':
                    is_father = False
                    link_user_from = user
                    link_user_to = link_user

                if got_tg_token:
                    operationtype_id = OperationType.SET_FATHER if is_father else OperationType.SET_MOTHER
                else:
                    operationtype_id = OperationType.FATHER if is_father else OperationType.MOTHER
                self.add_operation(
                    link_user_from,
                    link_user_to.profile,
                    operationtype_id = operationtype_id,
                    comment = None,
                    insert_timestamp = int(time.time()),
                )

            profile = user.profile
            self.save_photo(request, profile)
            fmt = request.data.get('fmt')
            if link_id and fmt == '3d-force-graph':
                data = profile.data_dict(request, fmt=fmt, thumb=dict(mark_dead=True))
            else:
                data = profile.data_dict(request)
                data.update(profile.owner_dict())
                data.update(tg_data=profile.tg_data())
                data.update(profile.data_WAK())
                data.update(profile.parents_dict(request))
                if got_tg_token and link_id and relation in ('new_is_father', 'new_is_mother',):
                    user_from = link_user_from
                    profile_from = user_from.profile
                    profile_from_data=profile_from.data_dict(request)
                    profile_from_data.update(profile_from.owner_dict())
                    profile_from_data.update(tg_data=profile_from.tg_data())
                    profile_from_data.update(profile_from.data_WAK())
                    profile_from_data.update(profile_from.parents_dict(request))
                    data.update(
                        profile_from=profile_from_data,
                    )
        except SkipException:
            pass
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

    @transaction.atomic
    def put(self, request):
        status_code = 200
        try:
            got_tg_token = False
            if request.data.get('tg_token'):
                if request.data['tg_token'] != settings.TELEGRAM_BOT_TOKEN:
                    raise ServiceException('Неверный токен телеграм бота')
                got_tg_token = True
                user, profile = self.check_user_uuid(request.data.get('uuid'))
            elif not request.user.is_authenticated:
                raise NotAuthenticated
            else:
                user, profile = self.check_user_or_owned_uuid(request, need_uuid=True)

            bool_fields = ('did_bot_start',)
            for f in bool_fields:
                if f in request.data:
                    setattr(profile, f, bool(request.data[f]))

            owner_uuid = request.data.get('owner_uuid')
            if owner_uuid:
                new_owner, new_owner_profile = self.check_user_uuid(owner_uuid)
                if not profile.owner:
                    raise ServiceException('Нельзя назначать владельца профилю зарегистрированного пользователя')
                if new_owner_profile.owner:
                    raise ServiceException('Нельзя делать владельцем профиль, которым кто-то владеет')
                profile.owner = new_owner
            dob, dod =self.check_dates(request)
            self.check_gender(request)
            if 'dob' in request.data:
                profile.dob = dob or None
            if 'is_dead' in request.data:
                profile.is_dead = bool(request.data['is_dead'])
            if 'dod' in request.data:
                profile.dod = dod or None
                if dod:
                    profile.is_dead = True

            if request.data.get('last_name') or request.data.get('first_name'):
                first_name = Profile.make_first_name(
                    request.data.get('last_name', ''),
                    request.data.get('first_name', ''),
                    request.data.get('middle_name', ''),
                )
                user.last_name = ''
                user.first_name = first_name

            # Поля с возможным null, может прийти 'значение' или ''
            for f in ('comment', 'gender',):
                if f in  request.data:
                    setattr(profile, f, request.data[f] or None)
            # Булевы поля, может прийти '1' или ''
            for f in ('is_org',):
                if f in  request.data:
                    setattr(profile, f, bool(request.data[f]))
            if 'latitude' in request.data and 'longitude' in request.data:
                latitude = longitude = None
                try:
                    latitude = float(request.data['latitude'])
                    longitude = float(request.data['longitude'])
                except (ValueError, TypeError,):
                    pass
                profile.put_geodata(latitude, longitude, save=False)
            if 'is_notified' in request.data and user == request.user:
                profile.is_notified = bool(request.data.get('is_notified'))
            if 'photo' in request.data:
                if request.data.get('photo'):
                    self.save_photo(request, profile)
                else:
                    profile.delete_from_media()
                    profile.photo = None
                    profile.photo_original_filename = ''
            if 'bank' in request.data:
                keytype_id = KeyType.BANKING_DETAILS_ID
                Key.objects.filter(type__pk=keytype_id, owner=user).delete()
                key, created_ = Key.objects.get_or_create(
                    type_id=keytype_id,
                    value=request.data['bank'],
                    defaults=dict(
                        owner=user,
                ))
                if not created_:
                    raise ServiceException(f'Реквизиты платежей "{value}" есть уже у другого человека')
            if 'tgdesc' in request.data:
                tgdesc_dict = request.data['tgdesc']
                if request.data.get('is_first'):
                    profile.tgdesc.filter(
                        ~Q(uuid_pack=tgdesc_dict['uuid_pack'])
                    ).delete()
                tgdesc = TgDesc.objects.create(**tgdesc_dict)
                profile.tgdesc.add(tgdesc)
            if 'did_meet' in request.data:
                did_meet = request.data.get('did_meet')
                unix_time_now = int(time.time())
                user_inviter = None
                if username_inviter := request.data.get('username_inviter'):
                    try:
                        user_inviter = User.objects.get(username=username_inviter)
                    except User.DoesNotExist:
                        pass
                if did_meet:
                    profile.did_meet = unix_time_now
                    if user_inviter and user_inviter != user:
                        self.add_operation(
                            # Именно так: от user_inviter из телеги идет приглашение
                            # к текущему юзеру с профилем profile
                            user_inviter,
                            profile,
                            operationtype_id=OperationType.DID_MEET,
                            comment=None,
                            insert_timestamp = unix_time_now,
                        )
                    else:
                        # Вошел в игру не по приглашению или нажал на ссылку на себя
                        Journal.objects.create(
                            user_from=user,
                            operationtype_id=OperationType.DID_MEET,
                            insert_timestamp=unix_time_now,
                            user_to=None
                            )
                else:
                    profile.did_meet = None
                    Journal.objects.create(
                        user_from=user,
                        operationtype_id=OperationType.REVOKED_MEET,
                        insert_timestamp=unix_time_now,
                        user_to=user_inviter
                        )

            user.save()
            profile.save()
            data = profile.data_dict(request)
            data.update(profile.parents_dict(request))
            data.update(profile.data_WAK())
            data.update(profile.owner_dict())
            if got_tg_token:
                data.update(tg_data=profile.tg_data())
        except SkipException:
            pass
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

    @transaction.atomic
    def delete(self, request):
        """
        Деактивировать профиль пользователя (обезличить) или удалить собственного

        Если из телеграма, задан tg_token, то в принимаемых данных:
            - нужен uuid, свой или удаляемого собственного
            - еще owner_id, в любом случе id удаляющего юзера
        Иначе должен быть авторизован

        Обезличить активного:
        Устанавливаются:
            ФИО: Обезличен
        Удаляются:
            фото - в профиле и во всех профилях соцсетей
            ключи
            возможности
            желания
            токен авторизации
            широта, долгота,
            пол
        Отметить а auth_user пользователя is_active = False
        """
        try:
            tg_token = request.data.get('tg_token')
            if tg_token:
                if tg_token != settings.TELEGRAM_BOT_TOKEN:
                    raise ServiceException('Неверный токен телеграм бота')
                owner_id = request.data.get('owner_id')
                if not owner_id:
                    raise ServiceException('Не задан owner_id')
                user, profile = self.check_user_uuid(request.data.get('uuid'), related=('user',))
                if profile.owner:
                    try:
                        owner = User.objects.get(pk=owner_id)
                    except User.DoesNotExist:
                        raise ServiceException('Не верен owner_id')
                    if str(profile.owner.pk) != str(owner_id):
                        raise ServiceException(
                            "owner_id %s не имеет прав на профиль '%s'" % (owner_id, profile.uuid,)
                        )
                else:
                    if str(owner_id) != str(user.pk):
                        ServiceException('Вы не тот, за кого себя выдаете')
            else:
                if not request.user.is_authenticated:
                    raise NotAuthenticated
                user, profile = self.check_user_or_owned_uuid(request, need_uuid=False)
            if profile.owner:
                profile.tgdesc.all().delete()
                profile.delete()
                user.delete()
                data = {}
            else:

                if profile.r_sympa:
                    profile_sympa = Profile.objects.filter(user=profile.r_sympa).update(
                        r_sympa=None,
                    )
                profile.tgdesc.all().delete()
                CurrentState.objects.filter(Q(user_from=user) | Q(user_to=user)).update(
                    is_sympa=False,
                    is_sympa_reverse=False,
                    is_sympa_confirmed=False,
                    update_timestamp=int(time.time()),
                )
                for f in ('middle_name',):
                        setattr(profile, f, '')
                for f in ('latitude', 'longitude', 'ability', 'comment', 'address', 'dob', 'dod', 'did_meet', 'r_sympa',):
                    setattr(profile, f, None)
                profile.is_dead = False
                profile.delete_from_media()
                profile.photo_original_filename = ''
                profile.photo = None
                profile.save()

                Key.objects.filter(owner=user).delete()
                Ability.objects.filter(owner=user).delete()
                Wish.objects.filter(owner=user).delete()

                CurrentState.objects.filter(
                    (Q(user_from=user) | Q(user_to=user)) & (Q(is_father=True) | Q(is_mother=True))
                ).update(is_father=False, is_mother=False, is_child=False)

                for oauth in Oauth.objects.filter(user=user):
                    for f in ('last_name', 'first_name', 'display_name', 'email', 'photo', 'username'):
                        setattr(oauth, f, '')
                    oauth.update_timestamp = int(time.time())
                    oauth.save()
                for f in ('last_name', 'email'):
                    setattr(user, f, '')
                user.first_name = "Обезличен"
                user.is_active = False
                user.save()

                data = profile.data_dict(request)
                data.update(profile.owner_dict())
                data.update(profile.parents_dict(request))
                data.update(profile.data_WAK())
                if tg_token:
                    data.update(tg_data=profile.tg_data())
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_profile = ApiProfile.as_view()

class ApiUserRelations(UuidMixin, APIView):
    """
    Как user_id_to относится к user_id_from, включая симпатии

    Пример:
        api/user/relations?user_id_to=...&user_id_from=...я все ключи
    Возвращает
        {
        "from_to": {
            "attitude": 't',
            "thanks_count": 2,
            "is_sympa_confirmed": true
            },
        "to_from": {
            "attitude": null,
            "thanks_count": 0,
            "is_sympa_confirmed": false
            },
        }
    """
    def get(self, request):
        try:
            status_code = status.HTTP_200_OK
            user_from, profile_from = self.check_user_uuid(
                request.GET.get('user_id_from'),
                comment='user_id_from. ',
            )
            user_to, profile_to = self.check_user_uuid(
                request.GET.get('user_id_to'),
                comment='user_id_to. ',
            )
            data = dict(
                from_to=dict(attitude=None, thanks_count=0, is_sympa_confirmed=False),
                to_from=dict(attitude=None, thanks_count=0, is_sympa_confirmed=False),
            )
            users = (user_from, user_to,)
            for cs in CurrentState.objects.filter(
                user_from__in=users,
                user_to__in=users,
                is_reverse=False,
                ):
                if cs.user_from == user_from:
                    data['from_to']['attitude'] = cs.attitude
                    data['from_to']['thanks_count'] = cs.thanks_count
                elif cs.user_from == user_to:
                    data['to_from']['attitude'] = cs.attitude
                    data['to_from']['thanks_count'] = cs.thanks_count
            for cs in CurrentState.objects.filter(
                user_from__in=users,
                user_to__in=users,
                is_sympa_reverse=False,
                ):
                if cs.user_from == user_from:
                    data['from_to']['is_sympa_confirmed'] = cs.is_sympa_confirmed
                elif cs.user_from == user_to:
                    data['to_from']['is_sympa_confirmed'] = cs.is_sympa_confirmed
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_user_relations = ApiUserRelations.as_view()

class ApiTestGoToLink(FrontendMixin, APIView):

    """
    Тест для проверки авторизованного get запроса с временным токеном
    """
    def get(self, request, temp_token):
        try:
            try:
                user = User.objects.get(auth_token__key=temp_token)
            except User.DoesNotExist:
                raise NotFound()
            uuid = request.GET.get('uuid')
            if uuid:
                path = '/profile/?id=%s' % uuid
            else:
                path = '/'
            provider = Oauth.PROVIDER_TELEGRAM
            redirect_from_callback = self.get_frontend_url(
                request,
                path,
            )
            response = redirect(redirect_from_callback)
            to_cookie = dict(
                provider=provider,
                user_id=user.pk,
                user_uuid=str(user.profile.uuid),
                auth_token=user.auth_token.key
            )
            response.set_cookie(
                key='auth_data',
                value=json.dumps(to_cookie),
                max_age=600,
                path='/',
                domain=self.get_frontend_name(request),
            )
            return response
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

test_goto_auth_link = ApiTestGoToLink.as_view()

class ApiBotStat(APIView):
    """
    Статистика по пользователям для бота

    Количество пользователей - всего в нашей базе
    Всего сколько нажало старт
    Всего с заданными координатами
    """
    def get(self, request):
        data = {
            'active': Profile.objects.filter(user__is_superuser=False, owner__isnull=True).count(),
            'owned': Profile.objects.filter(owner__isnull=False).count(),
            'did_bot_start': Profile.objects.filter(did_bot_start=True, owner__isnull=True).count(),
            'with_geodata': Profile.objects.filter(latitude__isnull=False, owner__isnull=True).count(),
            'relations': CurrentState.objects.filter(is_child=True).count(),
            'trusts': CurrentState.objects.filter(is_reverse=False, attitude=CurrentState.TRUST).count(),
            'mistrusts': CurrentState.objects.filter(is_reverse=False, attitude=CurrentState.MISTRUST).count(),
            'acqs': CurrentState.objects.filter(is_reverse=False, attitude=CurrentState.ACQ).count(),
        }
        return Response(data=data, status=status.HTTP_200_OK)

api_bot_stat = ApiBotStat.as_view()

class ApiBotGroupMixin(APIView):

    def group_post(self, data):
        """
        Создать, если необходимо группу из ее данных, data
        """
        title = data.get('title', '')
        type_ = data.get('type', '')
        tg_group, created_ = TgGroup.objects.get_or_create(
            chat_id = data['chat_id'],
            defaults={
                'title': title,
                'type': type_,
        })
        if not created_:
            do_save = False
            if title and tg_group.title != title:
                do_save = True
                tg_group.title = title
            if type_ and tg_group.type != type_:
                do_save = True
                tg_group.type = type_
            if do_save:
                tg_group.save()
        status_code = status.HTTP_200_OK
        return tg_group, created_

class ApiBotGroup(ApiBotGroupMixin, APIView):
    """
    Записать в таблицу TgGroup информацию о группе. Или удалить из таблицы
    """

    def get(self, request):
        """
        Получить информацию о группе/каналу по chat_id
        """
        data = {}
        status_code = 404
        try:
            chat_id = int(request.GET.get('chat_id', ''))
            data = TgGroup.objects.get(chat_id=chat_id).data_dict()
            status_code = status.HTTP_200_OK
        except (ValueError, TypeError, TgGroup.DoesNotExist,):
            pass
        return Response(data=data, status=status_code)

    def check_data(self, request):
        if request.data.get('tg_token', '') != settings.TELEGRAM_BOT_TOKEN:
            raise ServiceException('Неверный токен телеграм бота')
        try:
            chat_id = int(request.data.get('chat_id') or 0)
        except (ValueError, TypeError,):
            chat_id = 0
        if not chat_id:
            raise ServiceException('Не верный chat_id')

    def post(self, request):
        try:
            self.check_data(request)
            tg_group, created_ = self.group_post(request.data)
            data = tg_group.data_dict()
            data.update(created=created_)
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

    def put(self, request):
        """
        Изменить группу канал
        На входе: {
            "old_chat_id"=...       эту группу/канал изменяем,
            "chat_id"=...,          возможно новый ид
            "type"=...,             может и не быть
            "title"=...             может и не быть
            "pin_message_id"=...    может и не быть
        }
        Возвращает: {
            "chat_id"=...,
            "type"=...,
            "title"=...
            "pin_message_id"=...
        }
        или HTTP_400_BAD_REQUEST при неверных входных данных
        или HTTP_404_NOT_FOUND, если не найдена группа/канал
        """
        try:
            status_code = None
            self.check_data(request)
            try:
                old_chat_id = int(request.data.get('old_chat_id'))
            except (ValueError, TypeError,):
                raise ServiceException('Не верный old_chat_id')
            try:
                tg_group = TgGroup.objects.get(chat_id=old_chat_id)
            except TgGroup.DoesNotExist:
                status_code = status.HTTP_404_NOT_FOUND
                raise ServiceException('Не найдена группа/канал')
            do_save = False
            for f in ('chat_id', 'title', 'type', 'pin_message_id',):
                if v := request.data.get(f):
                    if v != getattr(tg_group, f):
                        do_save = True
                        setattr(tg_group, f, v)
                if do_save:
                    tg_group.save()
            data = tg_group.data_dict()
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            if status_code is None:
                status_code = status.HTTP_404_NOT_FOUND
        return Response(data=data, status=status_code)

    def delete(self, request):
        try:
            self.check_data(request)
            chat_id = request.data['chat_id']
            try:
                TgGroup.objects.get(chat_id=chat_id).delete()
            except TgGroup.DoesNotExist:
                raise ServiceException('Группа с chat_id = %s не найдена среди назначенных боту' % chat_id)
            status_code = status.HTTP_200_OK
            data = {}
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_bot_group = ApiBotGroup.as_view()

class ApiBotGroupMember(ApiBotGroupMixin, APIView):
    """
    Добавить/удалить пользователя телеграм в группу
    """

    def check_data(self, request):
        """
        Проверка данных при добавлении/удаления пользователя из группы

        Данные на входе:
            tg_token
            group
                chat_id
                title
                type
            user
                tg_uid
        На выходе:  (объекты из б.д)
            oauth
            tggroup

        """
        if request.data.get('tg_token', '') != settings.TELEGRAM_BOT_TOKEN:
            raise ServiceException('Неверный токен телеграм бота')
        try:
            group = request.data['group']
            user = request.data['user']
        except KeyError:
            raise ServiceException('Не хватает данных: group и/или user')
        try:
            chat_id = int(group.get('chat_id') or 0)
        except (ValueError, TypeError, AttributeError):
            chat_id = 0
        if not chat_id:
            raise ServiceException('Не верный или отсутствует chat_id для группы')
        tg_group, created = self.group_post(group)
        try:
            tg_uid = user.get('tg_uid') or None
        except (AttributeError):
            tg_uid = None
        if not tg_uid:
            raise ServiceException('Не верный или отсутствует user.tg_uid')
        try:
            oauth = Oauth.objects.get(provider=Oauth.PROVIDER_TELEGRAM, uid=str(tg_uid))
        except Oauth.DoesNotExist:
            raise ServiceException('Нет такого tg_uid среди зарегистрированных пользователей телеграма в апи')
        return oauth, tg_group

    def post(self, request):
        try:
            oauth, tg_group = self.check_data(request)
            oauth.groups.add(tg_group)
            data = dict(group=tg_group.data_dict())
            status_code = 200
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

    def delete(self, request):
        try:
            oauth, tg_group = self.check_data(request)
            oauth.groups.remove(tg_group)
            status_code = 200
            data = {}
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = 400
        return Response(data=data, status=status_code)

api_bot_groupmember = ApiBotGroupMember.as_view()

class ApiUserPoints(FromToCountMixin, FrontendMixin, TelegramApiMixin, UuidMixin, GenderMixin, APIView):
    """
    Вернуть список координат пользователей

    На входе:
    без параметров:
        на выходе пустой список
    возможные параметры
    (в порядке их анализа):
        chat_id         ид группы/канала в телеграме,
                        показать участников этой группы/канала

        meet            on или другое не пустое, участники игры знакомств
            Вместе с meet возможны:
                lat_south, lat_north, lng_west, lng_east:
                        координаты области, в которой карта.
                        При этом возвращается только legend

        offer           on или другое не пустое.
                        Показ на карте всех юзеров, оставивших опросы

        offer_id        ид опроса- предложения в телеграме,
                        показать участников опроса, как они голосовали,
                        каждый из участников на карте будет в рамке цвета,
                        назначенного ответу (settings.OFFER_ANSWER_COLOR_MAP).
                        Если подал несколько ответов, то без рамки

        uuid_trustees   uuid пользователя. Показать тех, кто ему доверяет
                        или не доверяет

        videoid         ид видео, по которым голосуют
                        показать участников голосания по видео,
                        каждый из участников на карте будет в рамке цвета,
                        назначенного голосу (Vote.VOTES_IMAGE[<голос>][color]).
                        Если подал несколько голосов, то без рамки
            Вместе с videoid может прийти:
                source, по умолчанию 'yt' (youtube)

        uuid            показать координаты пользователя с этим uuid.
                        Вместе с этим в выводе могут быть, при наличии параметров
                        participants и/или owned и другие пользователи
        participants    (on или пусто)
                        показать активных пользователей (не родственников, точнее
                        not owned профили)
        owned          (on или пусто)
                        показать не активных пользователей (например, родственников, точнее
                        owned профили)

    Пример выходных данных:
    {
        "first_name": "",                   // имя запрошенного пользователя, при параметре uuid
                                            // или uuid_trustees
        "found_coordinates": false,         // нашелся ли пользователь, при параметре uuid
                                            // или uuid_trustees
        "address": null,                    // текстовый адрес пользователя, при параметре uuid
                                            // или uuid_trustees
        "lat_avg": 50.94895896995098,       // где центрировать карту. При параметре uuid это
        "lng_avg": 33.90609824676903,       // адрес найденного с координатами пользователя с uuid,
                                            // иначе центр относительно всех найденных

        "chat_title": null,                 // Название телеграм группы/канала, где ищем пользователей
        "chat_type": null,                  // тип телеграм группы/канала, где ищем пользоватей,
                                            // группа или канал
        "offer_question": null,             // вопрос телеграм опроса- предложения (offer)
        "offer_deeplink": null,             // ссылка на опроса- предложение (offer) в телеграме
        "legend": "строка",                 // если задан offer_id:
                                            //      html таблица легенды для цветов ответов, две колонки:
                                            //          - фото неизвестного в рамке цвета
                                            //          - ответ, соответствующий цвету
                                            // если задан uuid_trustees:
                                            //      пользователи:
                                            //          - опрашиваемый пользователь
                                            //          - те, кто ему доверяет
                                            //          - те, кто ему не доверяет
                                            // если задан videoid:
                                            //      html таблица легенды для цветов голосов, две колонки:
                                            //          - фото неизвестного в рамке цвета
                                            //          - голос, соответствующий цвету
        "video_title",                      // заголовок видео: ссылка на голосование по видео
                Возможны еще параметры:
                    from:   с такой секунды видео начинать
                    to:     по какую секунду видео показывать

        "points": [
            {
                // Информация по каждому найденному пользователю с координатами
                "latitude": 54.208471,
                "longitude": 28.500346,
                // имя фамилия
                "title": "(0) Eugene S",
                // что выскочит на карте при щелчке по пользователю
                "popup": "<table>
                            <tr>
                                <td><img src=\"http://api.x.org/thumb/profile-photo/2023/04/12/1484/photo_cUfiWNv.jpg/64x64~crop~12.jpg\" width=64 height=64></td>
                                <td> Eugene S (0)<br /> <a href=\"https://t.me/DevBlagoBot?start=cf047bf6-ade6-4167-82e1-a266b43b96e0\" target=\"_blank\">Профиль</a>
                                    <br /><br /> <a href=\"http://x.org/genesis/relations?user_uuid_trusts=cf047bf6-ade6-4167-82e1-a266b43b96e0\" target=\"_blank\">Доверия</a>
                                    </td>
                                </tr></table>",
                // это пользователь, которого искали с параметром uuid?
                "is_of_found_user": false,
                "icon": "http://api.x.org/thumb/profile-photo/2023/04/12/1484/photo.jpg/32x32~crop~12.jpg",
                "size_icon": 32
            },
            ...
        ]
    }
    Если не нашли никого, что показать на карте, она центрируется по Москве
    """

    # permission_classes = (IsAuthenticated,)

    # Фото пользователя, когда в карте щелкаешь на балун
    #
    THUMB_SIZE_POPUP = 72

    # Фото пользователя в легенде
    #
    THUMB_SIZE_LEGEND = 80

    # Фото пользователя, по которому есть параметр uuid
    #
    THUMB_SIZE_ICON_FOUND = 48

    # Фото остальных пользователей
    #
    THUMB_SIZE_ICON = 32

    # Ширина рамки для фоток, где ответ на опрос
    #
    OFFER_PHOTO_FRAME = 5

    # Ширина рамки для фоток, где ответ на видео
    #
    VOTE_PHOTO_FRAME = 5

    # Ширина рамки для фото умершего
    #
    DEAD_PHOTO_FRAME = 5

    # Ширина рамки для найденного пользователя
    #
    FOUND_USER_PHOTO_FRAME = 3

    # Ширина рамки для пользователя uuid_trustees или в легенде для всех
    #
    USER_TRUSTEEE_FRAME_LEGEND = 5

    # Ширина рамки для тех, кто доверяют, не доверяют uuid_trustees
    #
    USER_TRUSTEE_FRAME_MAP = 3

    # В каком формате и куда выводим профиль пользователя
    #
    FMT = '3d-force-graph'

    # Каким цветом обрамляем себя на карте игры
    #
    SELF_FRAME_COLOR = 'blue'

    def popup_data(self, profile,
            color=None,
            frame=0,
            thumb_size_popup=THUMB_SIZE_POPUP,
            thumb_size_icon=THUMB_SIZE_ICON
        ):
        url_profile = self.profile_url_by_uuid(self.request, profile.uuid, fmt=self.FMT)
        url_deeplink = self.get_deeplink(profile.user, self.bot_username) if self.bot_username else url_profile
        if profile.latitude and profile.longitude:
            link_on_map = '<a href="%s/?uuid_trustees=%s" target="_blank">На карте</a><br />' % (
                settings.MAP_URL, profile.uuid,
            )
        else:
            link_on_map = ''
        method_template = 'crop-%s-frame-%s'
        if color and frame:
            method = method_template % (color, frame,)
        elif not color and frame:
            method = method_template % ('black', frame,)
        elif color and not frame:
            method = method_template % (color, 3,)
        elif not color and not frame:
            method = 'crop'
        return dict(
            user_id=profile.user.pk,
            full_name=profile.user.first_name,
            username=profile.user.username,
            trust_count=profile.trust_count,
            acq_count=profile.acq_count,
            dob=str(profile.dob) if profile.dob else '',
            is_org=profile.is_org,
            url_profile = url_profile,
            url_deeplink=url_deeplink,
            latitude=profile.latitude,
            longitude=profile.longitude,
            comment=profile.comment and profile.comment.replace("\n", "<br />") or '',
            url_photo_popup=Profile.image_thumb(
                self.request, profile.photo,
                method=method,
                width=thumb_size_popup + frame * 2,
                height=thumb_size_popup + frame * 2,
                put_default_avatar=True,
                default_avatar_in_media=PhotoModel.get_gendered_default_avatar(profile.gender)
            ),
            url_photo_icon=Profile.image_thumb(
                self.request, profile.photo,
                method=method,
                width=thumb_size_icon + frame * 2,
                height=thumb_size_icon + frame * 2,
                put_default_avatar=True,
                default_avatar_in_media=PhotoModel.get_gendered_default_avatar(profile.gender)
            ),
            thumb_size_popup = thumb_size_popup + frame * 2,
            thumb_size_icon = thumb_size_icon + frame * 2,
            video_reply_html='',
            offer_reply_html='',
            link_on_map=link_on_map,
        )

    def get(self, request):

        bot_username = self.get_bot_username()
        self.bot_username = bot_username
        self.request = request

        lat_avg = 55.7522200
        lng_avg = 37.6155600

        # Ищем пользователя. Его помещаем в центр и делаем больше по размеру иконки на карте
        #
        found_coordinates = False

        user_auth = request.user if request.user.is_authenticated else None
        graph =None
        meet = False
        offer_on = False
        num_all = 0
        first_name = ''
        gender = ''
        address = None
        is_org = False
        legend=''
        chat_id = chat_title = chat_type = None
        offer_id = offer_question = offer_deeplink = None
        videoid = source = None
        video_title = ''
        offer_reply_html = video_reply_html = ''
        uuid_trustees = None
        qs = None
        title_template = '%(full_name)s (%(trust_count)s)'
        popup = (
            '<table>'
            '<tr>'
                '<td valign=top>'
                    '<img src="%(url_photo_popup)s" width=%(thumb_size_popup)s height=%(thumb_size_popup)s>'
                '</td>'
                '<td valign=top>'
                    ' %(full_name)s (%(trust_count)s)<br />'
                    ' <a href="%(url_deeplink)s" target="_blank">Профиль</a><br />'
                    '%(link_on_map)s'
                    ' <a href="%(url_profile)s" target="_blank">Доверия</a>'
                '</td>'
            '</tr>'
            '%(offer_reply_html)s%(video_reply_html)s'
            '</table>'
        )
        if request.GET.get('uuid'):
            try:
                found_user, found_profile = self.check_user_uuid(request.GET['uuid'], related=('user',))
                first_name = found_user.first_name
                gender = found_profile.gender
                found_coordinates = bool(found_profile.latitude and found_profile.longitude)
                if found_coordinates:
                    lat_avg = found_profile.latitude
                    lng_avg = found_profile.longitude
                    address = found_profile.address
                    is_org = found_profile.is_org
            except ServiceException:
                pass
        elif request.GET.get('chat_id'):
            chat_id = request.GET['chat_id']
        elif request.GET.get('meet'):
            meet = True
        elif request.GET.get('offer'):
            offer_on = True
        elif request.GET.get('offer_id'):
            offer_id = request.GET['offer_id']
        elif request.GET.get('uuid_trustees'):
            uuid_trustees = request.GET['uuid_trustees']
        elif request.GET.get('videoid'):
            videoid = request.GET['videoid']
            source = request.GET.get('source', 'yt')
        lat_sum = lng_sum = 0
        points = []
        q = Q(
            latitude__isnull=False,
            longitude__isnull=False,
        )
        if chat_id:
            try:
                tggroup = TgGroup.objects.get(chat_id=chat_id)
                chat_title = tggroup.title
                chat_type = tggroup.type
                q &= Q(user__oauth__groups__chat_id=chat_id)
            except (ValueError, TgGroup.DoesNotExist,):
                pass
        if chat_id and chat_title:
            qs = Profile.objects.filter(q).select_related('user').distinct()

        elif offer_on:
            q_offer_geo = Q(latitude__isnull=False, longitude__isnull=False, closed_timestamp__isnull=True)
            coords = set()
            for offer in Offer.objects.filter(q_offer_geo
                ).select_related('owner', 'owner__profile',
                ).distinct():
                coords.add(f'{offer.latitude}~{offer.longitude}')
                offerer = self.popup_data(offer.owner.profile)
                title = title_template % offerer
                title_deeplink = f'<a href="{offerer["url_deeplink"]}" target="_blank">{title}</a>'
                offer_popup = popup % offerer
                offer_popup = offer_popup[:-len('</table>')]
                point = dict(
                    latitude=offer.latitude,
                    longitude=offer.longitude,
                    title=offer.question,
                    icon=offerer['url_photo_icon'],
                    is_of_found_user=False,
                    size_icon=offerer['thumb_size_icon'],
                )
                lat_sum += offer.latitude
                lng_sum += offer.longitude
                question_deeplink = (
                    f'<a href="https://t.me/{self.bot_username}?start=offer-{offer.uuid}">'
                    f'{html.escape(offer.question)}</a>'
                )
                offer_popup += (
                    '<tr>'
                        '<td valign=middle>'
                            'Опрос/<br>предложение:'
                        '</td>'
                        '<td valign=middle>'
                            f'{question_deeplink}'
                        '</td>'
                    '</tr>'
                )
                offer_popup += '</table>'
                point.update(popup=offer_popup)
                points.append(point)
            num_all = len(coords)

        elif meet:
            if not user_auth:
                raise NotAuthenticated
            if request.GET.get('admin'):
                meet_admin = user_auth.profile.is_meetgame_admin()
            else:
                meet_admin = False
            graph = None
            color_sympa = 'darkorange'
            if meet_admin:
                list_m = []
                list_f = []
                legend = (
                    '<br />'
                    '<table style="border-spacing: 0;border-top: 2px solid;width:100%;">'
                    '<col width="40%" />'
                    '<col width="10%" />'
                    '<col width="10%" />'
                    '<col width="40%" />'
                    '<tr>'
                        '<td style="text-align:center;border-bottom: 2px solid";">М</td>'
                        '<td style="text-align:center;border-bottom: 2px solid;border-right: 1px solid;"></td>'
                        '<td style="text-align:center;border-bottom: 2px solid";"></td>'
                        '<td style="text-align:center;border-bottom: 2px solid;">Ж</td>'
                    '</tr>'
                )

            # Участники игры должны указывать пол, д.р. и место,
            # однако не исключаем, что место и д.р. затёрли
            #
            q_meet = Q(did_meet__isnull=False, gender__isnull=False)
            if not meet_admin:
                q_meet &= Q(r_sympa__isnull=True)
            in_rectangle = False
            try:
                # это для обновлении легенды, когда меняются границы карты
                #
                lat_south = float(request.GET.get('lat_south'))
                lat_north = float(request.GET.get('lat_north'))
                lng_west = float(request.GET.get('lng_west'))
                lng_east = float(request.GET.get('lng_east'))
                in_rectangle = True
            except (TypeError, ValueError):
                pass
            if in_rectangle:
                q_rectangle = Q(
                    latitude__gte=lat_south,
                    latitude__lte=lat_north,
                    longitude__gte=lng_west,
                    longitude__lte=lng_east,
                )
                q_meet &= q_rectangle
            else:
                q_meet &= Q(latitude__isnull=False, longitude__isnull=False)
            if request.GET.get('gender'):
                q_meet &= Q(gender=request.GET['gender'])
            parm_status = request.GET.get('status')
            show_hidden = request.GET.get('show_hidden') or parm_status == 'hidden'
            today = datetime.date.today()
            try:
                d_older = datetime.date(today.year - int(request.GET.get('older')), 12, 31)
                q_meet &= Q(dob__lte=d_older)
            except (TypeError, ValueError,):
                pass
            try:
                d_younger = datetime.date(today.year - int(request.GET.get('younger')), 1, 1)
                q_meet &= Q(dob__gte=d_younger)
            except (TypeError, ValueError,):
                pass
            popup_meet_simple = (
                '<table style="width:100%%">'
                '<col width="15%%" />'
                '<col width="25%%" />'
                '<tr>'
                    '<td valign=center>'
                        '<img src="%(url_photo_popup)s" width=%(thumb_size_popup)s height=%(thumb_size_popup)s>'
                    '</td>'
                    '<td valign=center>'
                        ' %(full_name)s<br />'
                '</tr>'
                '</table>'
            )
            my_interests = []; my_hidden = []; my_sympas = []
            if meet_admin:
                popup_meet = popup_meet_simple
                nodes = []
                user_pks = []
            else:
                for cs in CurrentState.objects.filter(
                    user_from=user_auth, user_to__isnull=False,
                ):
                    if cs.is_sympa == True and cs.is_sympa_reverse == False:
                        my_interests.append(cs.user_to_id)
                        if cs.is_sympa_confirmed:
                            my_sympas.append(cs.user_to_id)
                    if cs.is_hide_meet:
                        my_hidden.append(cs.user_to_id)
                popup_meet = (
                    '<table style="width:100%%;">'
                    '<tr>'
                        '<td colspan=2 valign=center align=center>'
                            '<img '
                                'src="%(url_photo_popup)s" width=%(thumb_size_popup)s height=%(thumb_size_popup)s '
                            '>'
                        '</td>'
                    '</tr>'
                    '<tr>'
                        '<td colspan=2 valign=middle align=center>'
                            '<b><big>%(full_name)s</big></b> (%(dob)s)'
                            '<br />'
                        '</td>'
                    '</tr>'
                    '<tr colspan=2>'
                        '<br />'
                    '</tr>'
                    '<tr>'
                        '<td valign=middle align=center>'
                            '<label for="id_handle_user_hide">Скрыть: </lable>'
                            '<input type="checkbox" class="hide_him_her" '
                            'name="handle_user_hide" id="id_handle_user_hide-%(user_id)s" '
                            '%(hide_checked)s>'
                            '<br />'
                        '</td>'
                        '<td valign=middle align="center">'
                            '<input type="button" class="sympa" value="%(sympa_button_value)s" '
                            'style="color:%(sympa_color)s;" '
                            'name="handle_user_sympa" id="id_handle_user_sympa-%(user_id)s" '
                        '</td>'
                    '</tr>'
                    '</table>'
                )

            profile_auth = Profile.objects.select_related('user').get(user=user_auth)
            user_auth = profile_auth.user

            if not meet_admin:
                if show_hidden:
                    q_meet &= Q(user__pk__in=my_hidden)
                elif my_hidden:
                    q_meet &= ~Q(user__pk__in=my_hidden)
                if parm_status == 'interests':
                    q_meet &= Q(user__pk__in=my_interests)
                elif parm_status == 'sympas':
                    q_meet &= Q(user__pk__in=my_sympas)
                elif parm_status == 'new':
                    q_meet &= ~Q(user__pk__in=my_interests)

            for p in Profile.objects.filter(q_meet).order_by('dob').select_related('user').distinct():
                lat_sum += p.latitude
                lng_sum += p.longitude

                color = None; frame = 0
                if meet_admin:
                    thumb_size_popup = self.THUMB_SIZE_POPUP
                else:
                    thumb_size_popup = 240
                if meet_admin and user_auth.pk == p.user.pk:
                    color = self.SELF_FRAME_COLOR; frame=5
                dict_user = self.popup_data(p, color, frame, thumb_size_popup, thumb_size_icon=50)
                dict_user['full_name'] = html.escape(dict_user['full_name'])
                dict_user.update(
                    sympa_button_value='Смотреть',
                    sympa_color=color_sympa if dict_user['user_id'] in my_interests else 'currentcolor',
                    hide_checked='checked' if dict_user['user_id'] in my_hidden else '',
                )
                points.append(dict(
                    latitude=p.latitude,
                    longitude=p.longitude,
                    title=title_template % dict_user,
                    popup=popup_meet % dict_user,
                    icon=dict_user['url_photo_icon'],
                    is_of_found_user=False,
                    size_icon=dict_user['thumb_size_icon'],
                ))
                if meet_admin:
                    if p.gender == GenderMixin.GENDER_MALE:
                        list_m.append(dict_user)
                    elif p.gender == GenderMixin.GENDER_FEMALE:
                        list_f.append(dict_user)
                    else:
                        # fool proof
                        continue
                    nodes.append(dict(
                        id=p.user.pk,
                        uuid=p.uuid,
                        username=p.user.username,
                        first_name=p.user.first_name,
                        photo=dict_user['url_photo_popup'],
                        gender=p.gender,
                    ))
                    user_pks.append(p.user.pk)
                num_all += 1

            if not meet_admin and profile_auth.latitude and profile_auth.longitude:
                dict_auth = self.popup_data(
                    profile_auth,
                    color=self.SELF_FRAME_COLOR,
                    frame=5,
                    thumb_size_icon=40
                )
                points.append(dict(
                    latitude=profile_auth.latitude,
                    longitude=profile_auth.longitude,
                    title=title_template % dict_auth,
                    popup=popup_meet_simple % dict_auth,
                    icon=dict_auth['url_photo_icon'],
                    is_of_found_user=False,
                    size_icon=dict_auth['thumb_size_icon'],
                ))

            if meet_admin:
                q_connections = \
                    Q(user_to__isnull=False) & \
                    (
                        Q(attitude__isnull=False, is_reverse=False) | \
                        Q(is_invite_meet=True, is_invite_meet_reverse=False) | \
                        Q(is_sympa_confirmed=True, is_sympa_reverse=False) |
                        Q(is_hide_meet=True)
                    )
                links = []
                for cs in CurrentState.objects.filter(q_connections).filter(
                        user_from__in=user_pks, user_to__in=user_pks,
                        ).select_related(
                            'user_from__profile', 'user_to__profile',
                        ).distinct():
                    link_pattern = dict(
                        source=cs.user_from.pk,
                        target=cs.user_to.pk,
                    )
                    if cs.attitude is not None and not cs.is_reverse:
                        link = link_pattern.copy()
                        link.update(attitude=cs.attitude)
                        links.append(link)
                    if cs.is_invite_meet and not cs.is_invite_meet_reverse:
                        link = link_pattern.copy()
                        link.update(is_invite_meet=True)
                        links.append(link)
                    if cs.is_sympa and not cs.is_sympa_reverse and cs.is_sympa_confirmed:
                        link = link_pattern.copy()
                        link.update(is_sympa=True)
                        links.append(link)
                    if cs.is_hide_meet:
                        link = link_pattern.copy()
                        link.update(is_hide_meet=True)
                        links.append(link)
                graph = dict(nodes=nodes, links=links)

                len_m = len(list_m)
                len_f = len(list_f)
                popup_m = popup_meet
                popup_f = (
                    '<table style="width:100%%">'
                    '<col width="25%%" />'
                    '<col width="15%%" />'
                    '<tr>'
                        '<td valign=center align=center>'
                            ' %(full_name)s'
                        '</td>'
                        '<td valign=center align=right>'
                            '<img src="%(url_photo_popup)s" width=%(thumb_size_popup)s height=%(thumb_size_popup)s>'
                        '</td>'
                    '</tr>'
                    '</table>'
                )
                if len_f or len_m:
                    legend_user = (
                        '<tr style="border-bottom: 2px solid">'
                            '<td align="left" style="border-bottom: 2px solid;">%(m)s</td>'
                            '<td style="text-align:center;border-bottom: 2px solid;border-right: 1px solid;">%(m_dob)s</td>'
                            '<td style="text-align:center;border-bottom: 2px solid;">%(f_dob)s</td>'
                            '<td align="right" style="border-bottom: 2px solid;"">%(f)s</td>'
                        '</tr>'
                    )

                    for i in range(max(len_m, len_f)):
                        d = dict(
                            m='', m_dob='', m_sympa='', m_hide='',
                            f='', f_dob='', f_sympa='', f_hide='',
                        )
                        if i < len_m:
                            d['m'] = popup_m % list_m[i]
                            d['m_dob'] = list_m[i]['dob']
                        if i < len_f:
                            d['f'] = popup_f % list_f[i]
                            d['f_dob'] = list_f[i]['dob']
                        legend += legend_user % d
                legend += '</table><br /><br />'

                if request.GET.get('with_offers'):
                    q_offer_geo = Q(closed_timestamp__isnull=True)
                    if in_rectangle:
                        q_offer_geo &= q_rectangle
                    else:
                        q_offer_geo &= Q(latitude__isnull=False, longitude__isnull=False)
                    for offer in Offer.objects.filter(q_offer_geo
                        ).select_related('owner', 'owner__profile',
                        ).distinct():
                        offerer = self.popup_data(offer.owner.profile, thumb_size_icon=24, color='plum', frame=2)
                        title = title_template % offerer
                        title_deeplink = f'<a href="{offerer["url_deeplink"]}" target="_blank">{title}</a>'
                        offer_popup = popup % offerer
                        offer_popup = offer_popup[:-len('</table>')]
                        point = dict(
                            latitude=offer.latitude,
                            longitude=offer.longitude,
                            title=f'Опрос/предложение: {offer.question}',
                            icon=offerer['url_photo_icon'],
                            is_of_found_user=False,
                            size_icon=offerer['thumb_size_icon'],
                            is_offer=True,
                        )
                        question_deeplink = (
                            f'<a href="https://t.me/{self.bot_username}?start=offer-{offer.uuid}">'
                            f'{offer.question}</a>'
                        )
                        offer_popup += (
                            '<tr>'
                                '<td valign=middle>'
                                    'Опрос/<br>предложение:'
                                '</td>'
                                '<td valign=middle>'
                                    f'{question_deeplink}'
                                '</td>'
                            '</tr>'
                        )
                        offer_popup += '</table>'
                        point.update(popup=offer_popup % offerer)
                        points.append(point)

        elif offer_id:
            try:
                offer = Offer.objects.select_related('owner', 'owner__profile').get(uuid=offer_id)
                q = Q(offer_answers__offer__uuid=offer_id)
                qs = Profile.objects.filter(q).select_related('user').distinct()
                offer_dict = offer.data_dict(request=None, user_ids_only=True)
                offer_question = offer_dict['question']
                answers = [answer['answer'] for answer in offer_dict['answers']]
                answers[0] = 'не ответил(а)'
                if bot_username:
                    offer_deeplink = 'https://t.me/%s?start=offer-%s' % (bot_username, offer.uuid)
            except (ValueError, Offer.DoesNotExist,):
                qs = offer = None

        elif uuid_trustees:
            num_attitude_trust = num_attitude_mistrust = num_attitude_acq = 0
            try:
                try:
                    found_user, found_profile = self.check_user_uuid(uuid_trustees, related=('user',))
                except ServiceException:
                    raise SkipException
                first_name = found_user.first_name
                gender = found_profile.gender
                found_coordinates = bool(found_profile.latitude and found_profile.longitude)
                if found_coordinates:
                    lat_avg = found_profile.latitude
                    lng_avg = found_profile.longitude
                    address = found_profile.address
                    is_org = found_profile.is_org
                color = 'black' if found_profile.is_dead or found_profile.dod else 'blue'
                legend = f'<br><table style="border-spacing: 0;border-top: 2px solid {color};border-bottom: 2px solid {color};">'
                legend += '<tr><td>'
                dict_user = self.popup_data(
                    found_profile,
                    color,
                    self.USER_TRUSTEEE_FRAME_LEGEND,
                    self.THUMB_SIZE_LEGEND,
                )
                legend += popup % dict_user
                legend += '</td></tr>'
                legend += '</table><br />'
                if found_coordinates:
                    frame = self.USER_TRUSTEE_FRAME_MAP
                    dict_user = self.popup_data(
                        found_profile,
                        color,
                        frame,
                        self.THUMB_SIZE_POPUP,
                    )
                    points.append(dict(
                        latitude=found_profile.latitude,
                        longitude=found_profile.longitude,
                        title=title_template % dict_user,
                        popup=popup % dict_user,
                        is_of_found_user=True,
                        icon=found_profile.choose_thumb(
                            request,
                            method=f'crop-{color}-frame-{frame}',
                            width=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                            height=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                            put_default_avatar=True,
                            default_avatar_in_media=PhotoModel.get_gendered_default_avatar(gender)
                        ),
                        size_icon=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                    ))
                legend_attitude_trust = legend_attitude_mistrust = legend_attitude_acq = ''
                legend_attitude_trust_title = 'Доверяют:'
                legend_attitude_mistrust_title = 'Не доверяют:'
                legend_attitude_acq_title = 'Знакомы:'
                if not found_profile.is_org:
                    if found_profile.gender == GenderMixin.GENDER_FEMALE:
                        legend_attitude_trust_title = 'Ей доверяют:'
                        legend_attitude_mistrust_title = 'Ей не доверяют:'
                        legend_attitude_acq_title = 'С ней знакомы:'
                    elif found_profile.gender == GenderMixin.GENDER_MALE:
                        legend_attitude_trust_title = 'Ему доверяют:'
                        legend_attitude_mistrust_title = 'Ему не доверяют:'
                        legend_attitude_acq_title = 'С ним знакомы:'
                for cs in CurrentState.objects.filter(
                            user_to=found_profile.user,
                            is_reverse=False,
                            attitude__in=(CurrentState.TRUST, CurrentState.MISTRUST, CurrentState.ACQ, ),
                          ).select_related(
                              'user_from', 'user_from__profile'
                          ).order_by(
                              'user_from__first_name'
                          ):
                    if cs.attitude == CurrentState.TRUST:
                        color = 'darkgreen'
                    elif cs.attitude == CurrentState.MISTRUST:
                        color = 'red'
                    else:
                        color = 'yellowgreen'
                    legend_tempo= f'<table style="border-spacing: 0;border-top: 2px solid {color};">'
                    if cs.attitude == CurrentState.TRUST and not legend_attitude_trust:
                        legend_attitude_trust = (
                            f'{legend_attitude_trust_title}'
                            '<br /><br />'
                            f'{legend_tempo}'
                        )
                    if cs.attitude == CurrentState.MISTRUST and not legend_attitude_mistrust:
                        legend_attitude_mistrust = (
                            f'{legend_attitude_mistrust_title}'
                            '<br /><br />'
                            f'{legend_tempo}'
                        )
                    if cs.attitude == CurrentState.ACQ and not legend_attitude_acq:
                        legend_attitude_acq = (
                            f'{legend_attitude_acq_title}'
                            '<br /><br />'
                            f'{legend_tempo}'
                        )
                    dict_user = self.popup_data(
                        cs.user_from.profile,
                        color,
                        self.USER_TRUSTEEE_FRAME_LEGEND,
                        self.THUMB_SIZE_LEGEND,
                    )
                    legend_tempo = f'<tr><td style="border-bottom: 2px solid {color};">' + (popup % dict_user) + '</td></tr>'
                    if cs.attitude == CurrentState.TRUST:
                        num_attitude_trust += 1
                        legend_attitude_trust += legend_tempo
                    elif cs.attitude == CurrentState.MISTRUST:
                        num_attitude_mistrust += 1
                        legend_attitude_mistrust += legend_tempo
                    else:
                        num_attitude_acq += 1
                        legend_attitude_acq += legend_tempo
                    if cs.user_from.profile.latitude and cs.user_from.profile.longitude:
                        if not found_coordinates:
                            lat_sum += cs.user_from.profile.latitude
                            lng_sum += cs.user_from.profile.longitude
                        frame = self.USER_TRUSTEE_FRAME_MAP
                        dict_user = self.popup_data(
                            cs.user_from.profile,
                            color,
                            frame,
                            self.THUMB_SIZE_POPUP,
                        )
                        points.append(dict(
                            latitude=cs.user_from.profile.latitude,
                            longitude=cs.user_from.profile.longitude,
                            title=title_template % dict_user,
                            popup=popup % dict_user,
                            is_of_found_user=False,
                            icon=cs.user_from.profile.choose_thumb(
                                request,
                                method=f'crop-{color}-frame-{frame}',
                                width=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                                height=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                                put_default_avatar=True,
                                default_avatar_in_media=PhotoModel.get_gendered_default_avatar(cs.user_from.profile.gender)
                            ),
                            size_icon=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                        ))

                if legend_attitude_trust:
                    legend_attitude_trust += '</table><br />'
                else:
                    legend_attitude_trust += 'Кто доверяет: не найдены<br /><br />'
                if legend_attitude_mistrust:
                    legend_attitude_mistrust += '</table><br /><br />'
                else:
                    legend_attitude_mistrust += 'Кто не доверяет: не найдены<br /><br />'
                if legend_attitude_acq:
                    legend_attitude_acq += '</table><br /><br />'
                else:
                    legend_attitude_acq += 'Кто знаком: не найдены<br /><br />'
                legend += legend_attitude_trust + legend_attitude_mistrust + legend_attitude_acq

            except SkipException:
                pass

        elif videoid:
            votes_names = dict(Vote.VOTES)
            button_to_users = {'': set()}
            for vote in votes_names:
                button_to_users[vote] = set()
            user_pks = []
            user_datas = []
            video_title = Video.video_vote_url(source, videoid)
            if video_title.lower().startswith('http'):
                video_title = '<a href="%s" target="_blank">Голосование по видео</a>' % video_title
            else:
                video_title = 'Голосование по видео: <i>%s</i>' % video_title
            q_video = Q(
                video__source=source,
                video__videoid=videoid,
            )
            from_, to_ = self.get_from_to(request.GET, 'from', 'to')
            if from_ is not None:
                q_video &= Q(time__gte=from_)
            if to_ is not None:
                q_video &= Q(time__lte=to_)
            n_ind = 0
            for rec in Vote.objects.filter(q_video
                ).select_related(
                    'user', 'user__profile'
                ).values(
                    'user__id', 'user__first_name', 'user__username',
                    'user__profile__photo',
                    'user__profile__gender',
                    'user__profile__uuid',
                    'user__profile__trust_count',
                    'user__profile__acq_count',
                    'user__profile__latitude', 'user__profile__longitude',
                    'button'
                ).distinct('user', 'button'):
                try:
                    ind = user_pks.index(rec['user__id'])
                    user_datas[ind]['votes'].append(rec['button'])
                    button_to_users[''].add(ind)
                    for btn in votes_names:
                        try:
                            button_to_users[btn].remove(ind)
                        except KeyError:
                            pass
                except ValueError:
                    user_datas.append(dict(
                        full_name = rec['user__first_name'],
                        username = rec['user__username'],
                        photo=rec['user__profile__photo'],
                        gender=rec['user__profile__gender'],
                        trust_count=rec['user__profile__trust_count'],
                        acq_count=rec['user__profile__acq_count'],
                        uuid=rec['user__profile__uuid'],
                        latitude=rec['user__profile__latitude'],
                        longitude=rec['user__profile__longitude'],
                        votes=[rec['button']]
                    ))
                    user_pks.append(rec['user__id'])
                    button_to_users[rec['button']].add(n_ind)
                    n_ind += 1
            for user_data in user_datas:
                if user_data['latitude'] is not None and user_data['longitude'] is not None:
                    lat_sum += user_data['latitude']
                    lng_sum += user_data['longitude']
                    url_profile = self.profile_url_by_uuid(request, user_data['uuid'], fmt=self.FMT)
                    if bot_username:
                        url_deeplink = self.get_deeplink_by_username(user_data['username'], bot_username)
                    else:
                        url_deeplink = url_profile
                    votes = user_data['votes']
                    if len(votes) == 1:
                        vote = votes[0]
                        vote_color = Vote.VOTES_IMAGE[vote]['color']
                        frame = self.VOTE_PHOTO_FRAME
                        method = 'crop-%s-frame-%s' % (vote_color, frame, )
                        votes_text = votes_names[vote]
                        title = '%s: %s' % (user_data['full_name'], votes_text)
                    else:
                        votes.sort(key=lambda v: Vote.VOTES_IMAGE[v]['sort_order'])
                        frame = 0
                        method = 'crop'
                        votes_text = ', '.join([votes_names[vote] for vote in votes])
                        title = user_data['full_name']
                    video_reply_html = (
                        '<tr>'
                            '<td colspan=2>'
                            'Голос%s: %s'
                            '</td>'
                        '</tr>'
                    ) % (
                        'а' if len(votes) > 1 else '',
                        votes_text
                    )
                    if user_data['latitude'] and user_data['longitude']:
                        link_on_map = '<a href="%s/?uuid_trustees=%s" target="_blank">На карте</a><br />' % (
                            settings.MAP_URL, user_data['uuid']
                        )
                    else:
                        link_on_map = ''
                    popup_ = popup % dict(
                        full_name = user_data['full_name'],
                        trust_count=user_data['trust_count'],
                        acq_count=user_data['acq_count'],
                        url_deeplink=url_deeplink,
                        url_profile=url_profile,
                        url_photo_popup=Profile.image_thumb(
                            request, user_data['photo'],
                            method=method,
                            width=self.THUMB_SIZE_POPUP + frame * 2,
                            height=self.THUMB_SIZE_POPUP + frame * 2,
                            put_default_avatar=True,
                            default_avatar_in_media=PhotoModel.get_gendered_default_avatar(user_data['gender'])
                        ),
                        thumb_size_popup = self.THUMB_SIZE_POPUP,
                        video_reply_html=video_reply_html,
                        offer_reply_html=offer_reply_html,
                        link_on_map=link_on_map,
                    )
                    points.append(dict(
                        latitude=user_data['latitude'],
                        longitude=user_data['longitude'],
                        title=title,
                        is_of_found_user=False,
                        icon=Profile.image_thumb(
                            request, user_data['photo'],
                            method=method,
                            width=self.THUMB_SIZE_ICON + frame * 2,
                            height=self.THUMB_SIZE_ICON + frame * 2,
                            put_default_avatar=True,
                            default_avatar_in_media=PhotoModel.get_gendered_default_avatar(user_data['gender'])
                        ),
                        size_icon=self.THUMB_SIZE_ICON + frame * 2,
                        popup=popup_,
                    ))
            frame = self.VOTE_PHOTO_FRAME * 2
            legend = '<br><table style="border-spacing: 0;border-bottom: 2px solid black;">'
            vote_ts = [('', 'подал(а)<br/>несколько голосов')] + list(Vote.VOTES)
            for vote_t in vote_ts:
                vote, vote_name = vote_t
                legend += (
                    '<tr>'
                        '<td valign=top style="border-top: 2px solid black; padding: 4px;">'
                            '<img src="%(photo)s" width=%(width)s height=%(height)s />'
                        '</td>'
                        '<td valign=top style="border-top: 2px solid black; padding: 4px;">'
                            '<big>%(vote_name)s</big>'
                        '</td>'
                ) % dict(
                    photo=PhotoModel.image_thumb(
                        request=request,
                        fname=PhotoModel.DEFAULT_AVATAR_IN_MEDIA_NONE,
                        method = 'crop-%s-frame-%s' % (
                            Vote.VOTES_IMAGE[vote]['color'] if vote else 'white',
                            frame,
                        )
                    ),
                    vote_name=vote_name,
                    width=self.THUMB_SIZE_POPUP + frame * 2,
                    height=self.THUMB_SIZE_POPUP + frame * 2,
                )
                legend += '<td valign=top style="border-top: 2px solid black; padding: 4px;">'
                for ind in button_to_users[vote]:
                    user_data = user_datas[ind]
                    url_profile = self.profile_url_by_uuid(request, user_data['uuid'], fmt=self.FMT)
                    if bot_username:
                        url_deeplink = self.get_deeplink_by_username(user_data['username'], bot_username)
                    else:
                        url_deeplink = url_profile
                    votes = user_data['votes']
                    if len(votes) == 1:
                        vote_ = votes[0]
                        vote_color = Vote.VOTES_IMAGE[vote_]['color']
                        frame_ = self.VOTE_PHOTO_FRAME
                        method_ = 'crop-%s-frame-%s' % (vote_color, frame, )
                        video_reply_html = ''
                    else:
                        votes.sort(key=lambda v: Vote.VOTES_IMAGE[v]['sort_order'])
                        frame_ = 0
                        method_ = 'crop'
                        title = user_data['full_name']
                        video_reply_html = (
                            '<tr>'
                                '<td colspan=2>'
                                'Голоса: %s'
                                '</td>'
                            '</tr>'
                        ) % ', '.join([votes_names[vote_] for vote_ in votes])
                    if user_data['latitude'] and user_data['longitude']:
                        link_on_map = '<a href="%s/?uuid_trustees=%s" target="_blank">На карте</a><br />' % (
                            settings.MAP_URL, user_data['uuid']
                        )
                    else:
                        link_on_map = ''
                    popup_ = popup % dict(
                        full_name = user_data['full_name'],
                        username = user_data['username'],
                        trust_count=user_data['trust_count'],
                        acq_count=user_data['acq_count'],
                        url_deeplink=url_deeplink,
                        url_profile=url_profile,
                        url_photo_popup=Profile.image_thumb(
                            request, user_data['photo'],
                            method=method_,
                            width=self.THUMB_SIZE_LEGEND + frame_ * 2,
                            height=self.THUMB_SIZE_LEGEND + frame_ * 2,
                            put_default_avatar=True,
                            default_avatar_in_media=PhotoModel.get_gendered_default_avatar(user_data['gender'])
                        ),
                        thumb_size_popup = self.THUMB_SIZE_LEGEND,
                        video_reply_html=video_reply_html,
                        offer_reply_html=offer_reply_html,
                        link_on_map=link_on_map,
                    )
                    legend += popup_
                legend += '</td></tr>'
            legend += '</table><br /><br />'

        else:
            # Или задан uuid, или ничего
            qq_or = []
            if request.GET.get('participants'):
                qq_or.append(Q(owner__isnull=True))
            if request.GET.get('owned'):
                qq_or.append(Q(owner__isnull=False))
            if qq_or:
                for i, qq in enumerate(qq_or):
                    if i == 0:
                        q_or = qq
                    else:
                        q_or |= qq
                q &= q_or
                if found_coordinates:
                    q |= Q(pk=found_profile.pk)
                qs = Profile.objects.filter(q).select_related('user').distinct()
            else:
                if found_coordinates:
                    qs = Profile.objects.filter(pk=found_profile.pk).select_related('user').distinct()
        if offer_question:
            answer_to_users = {
                # не ответили
                -1: [],
                # ответили на несколько
                0: [],
                # Дальше ответы от 1 до числа ответов
            }
            for i in range(1, len(offer_dict['answers'])):
                answer_to_users[i] = []
        for profile in (qs if qs else []):
            url_profile = self.profile_url(request, profile, fmt=self.FMT)
            if bot_username:
                url_deeplink = self.get_deeplink(profile.user, bot_username)
            else:
                url_deeplink = url_profile
            if profile.latitude is not None and profile.longitude is not None:
                link_on_map = '<a href="%s/?%s=%s" target="_blank">На карте</a><br />' % (
                    settings.MAP_URL,
                    'uuid_trustees' if offer_question or chat_id else 'uuid',
                    profile.uuid,
                )
            else:
                link_on_map = ''
            if offer_question:
                answer_numbers = offer_dict['user_answered'].get(profile.user.pk, dict(answers=[0]))['answers']
                user_data = dict(
                    full_name = profile.user.first_name,
                    username=profile.user.username,
                    trust_count=profile.trust_count,
                    acq_count=profile.acq_count,
                    url_deeplink=url_deeplink,
                    url_profile=url_profile,
                    link_on_map=link_on_map
                )
                frame = self.OFFER_PHOTO_FRAME
                if len(answer_numbers) == 1:
                    answer_color = settings.OFFER_ANSWER_COLOR_MAP[answer_numbers[0]]
                    method = 'crop-%s-frame-%s' % (answer_color, frame, )
                    answer_text = answers[answer_numbers[0]]
                    title_template = '%(full_name)s: %(answer_text)s'
                    if answer_numbers[0]:
                        answer_to_users[answer_numbers[0]].append(user_data)
                    else:
                        answer_to_users[-1].append(user_data)
                else:
                    # Здесь только много ответов
                    method = 'crop-%s-frame-%s' % ('gray', frame, )
                    answer_text = '<br />' + '<br />'.join(
                        [' &nbsp;&nbsp;' + offer_dict['answers'][n]['answer'] for n in answer_numbers]
                    )
                    title_template = '%(full_name)s'
                    answer_to_users[0].append(user_data)
                user_data['photo'] = profile.choose_thumb(
                        request,
                        method=method,
                        width=self.THUMB_SIZE_POPUP + frame * 2,
                        height=self.THUMB_SIZE_POPUP + frame * 2,
                        put_default_avatar=True,
                        default_avatar_in_media=PhotoModel.get_gendered_default_avatar(profile.gender)
                )
                offer_reply_html = (
                    '<tr>'
                        '<td colspan=2>'
                        'Ответ%s: %s'
                        '</td>'
                    '</tr>'
                ) % (
                    'ы' if len(answer_numbers) > 1 else '',
                    answer_text
                )
                user_data['offer_reply_html'] = offer_reply_html if len(answer_numbers) > 1 else ''
            else:
                if profile.is_dead or profile.dod:
                    frame = self.DEAD_PHOTO_FRAME
                    method = f'crop-black-frame-{frame}'
                elif found_coordinates and profile == found_profile:
                    frame = self.FOUND_USER_PHOTO_FRAME
                    method = f'crop-blue-frame-{frame}'
                else:
                    frame = 0
                    method = 'crop'
                answer_text=''
            if offer_id or profile.latitude is not None and profile.longitude is not None:
                dict_user = dict(
                    full_name=profile.user.first_name,
                    username=profile.user.username,
                    trust_count=profile.trust_count,
                    acq_count=profile.acq_count,
                    url_deeplink=url_deeplink,
                    url_profile=url_profile,
                    url_photo_popup=profile.choose_thumb(
                        request,
                        method=method,
                        width=self.THUMB_SIZE_POPUP + frame * 2,
                        height=self.THUMB_SIZE_POPUP + frame * 2,
                        put_default_avatar=True,
                        default_avatar_in_media=PhotoModel.get_gendered_default_avatar(profile.gender)
                    ),
                    thumb_size_popup = self.THUMB_SIZE_POPUP,
                    offer_reply_html=offer_reply_html,
                    answer_text=answer_text,
                    title_template=title_template,
                    video_reply_html=video_reply_html,
                    link_on_map=link_on_map,
                )
                if profile.latitude is not None and profile.longitude is not None:
                    point = dict(
                        latitude=profile.latitude,
                        longitude=profile.longitude,
                        title=title_template % dict_user,
                        popup=popup % dict_user,
                    )
                    if (found_coordinates and profile == found_profile) or \
                    (offer_question and offer_dict['owner']['user_id'] == profile.user.pk):
                        point.update(
                            is_of_found_user=True,
                            icon=profile.choose_thumb(
                                request,
                                method=method,
                                width=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                                height=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                                put_default_avatar=True,
                                default_avatar_in_media=PhotoModel.get_gendered_default_avatar(profile.gender)
                            ),
                            size_icon=self.THUMB_SIZE_ICON_FOUND + frame * 2,
                        )
                    else:
                        point.update(
                            is_of_found_user=False,
                            icon=profile.choose_thumb(
                                request,
                                method=method,
                                width=self.THUMB_SIZE_ICON + frame * 2,
                                height=self.THUMB_SIZE_ICON + frame * 2,
                                put_default_avatar=True,
                                default_avatar_in_media=PhotoModel.get_gendered_default_avatar(profile.gender)
                            ),
                            size_icon=self.THUMB_SIZE_ICON + frame * 2,
                        )
                    points.append(point)
                    if not found_coordinates:
                        lat_sum += profile.latitude
                        lng_sum += profile.longitude

        if offer_question:
            legend = '<br><table style="border-spacing: 0;border-bottom: 2px solid black;">'
            frame = self.OFFER_PHOTO_FRAME * 2
            for i in range(-1, len(offer_dict['answers'])):
                if i == 0 and not offer.is_multi:
                    continue
                if i < 0:
                    answer = 'Не ответили'
                    frame_color = settings.OFFER_ANSWER_COLOR_MAP[0]
                elif i == 0:
                    answer = 'Несколько ответов'
                    frame_color = 'gray'
                else:
                    answer = offer_dict['answers'][i]['answer']
                    frame_color = settings.OFFER_ANSWER_COLOR_MAP[i]
                legend += (
                    '<tr>'
                        '<td valign=top style="border-top: 2px solid black; padding: 4px;">'
                            '<img src="%(photo)s" width=%(width)s height=%(height)s />'
                        '</td>'
                        '<td valign=top style="border-top: 2px solid black; padding: 4px;">'
                            '<big>%(answer)s</big>'
                        '</td>'
                ) % dict(
                    photo=PhotoModel.image_thumb(
                        request=request,
                        fname=PhotoModel.DEFAULT_AVATAR_IN_MEDIA_NONE,
                        method = 'crop-%s-frame-%s' % (frame_color, frame),
                    ),
                    answer=answer,
                    width=self.THUMB_SIZE_POPUP + frame * 2,
                    height=self.THUMB_SIZE_POPUP + frame * 2,
                )
                legend += '<td valign=top style="border-top: 2px solid black; padding: 4px;">'
                for user_data in answer_to_users[i]:
                    popup_ = popup % dict(
                        full_name=user_data['full_name'],
                        username=user_data['username'],
                        trust_count=user_data['trust_count'],
                        acq_count=user_data['acq_count'],
                        url_deeplink=user_data['url_deeplink'],
                        url_profile=user_data['url_profile'],
                        offer_reply_html=user_data['offer_reply_html'],
                        video_reply_html=video_reply_html,
                        url_photo_popup=user_data['photo'],
                        link_on_map=user_data['link_on_map'],
                        thumb_size_popup = self.THUMB_SIZE_LEGEND,
                    )
                    legend += popup_
                legend += '</td></tr>'
            legend += '</table><br /><br />'

        if points and not found_coordinates:
            lat_avg = lat_sum / len(points)
            lng_avg = lng_sum / len(points)
        data = dict(
            first_name=first_name,
            found_coordinates=found_coordinates,
            address=address,
            is_org = is_org,
            gender=gender,
            lat_avg=lat_avg,
            lng_avg=lng_avg,
            points=points,
            chat_title=chat_title,
            chat_type=chat_type,
            offer_question=offer_question,
            offer_deeplink=offer_deeplink,
            legend=legend,
            video_title=video_title,
            num_all=num_all,
            graph=graph,
        )
        if uuid_trustees:
            data.update(
                num_attitude_mistrust=num_attitude_mistrust,
                num_attitude_trust=num_attitude_trust,
                num_attitude_acq=num_attitude_acq,
            )
        return Response(data=data, status=200)

api_user_points = ApiUserPoints.as_view()

class ApiImportGedcom(ApiAddOperationMixin, UuidMixin, CreateUserMixin, APIView):

    def do_import(self, owner_uuid, bytes_io, indi_to_merge):
        """
        Импорт из gedcom файла

        owner_uuid:         uuid владельца импорируемых персон
        bytes_io:           считанный в BytesIO gedcom файл
        indi_to_merge:      в файле может быть владелец,
                            его сливаем с пользователем c owner_uuid
        """
        owner, owner_profile = self.check_user_uuid(owner_uuid, related=[])
        if owner_profile.owner:
            raise ServiceException('Допускается owner_id только активного пользователя')

        with GedcomReader(bytes_io) as parser:

            #   (ged)xref_id:
            #       first_name, first_name, gender, dob, dod, is_dead
            #       father_xref_id
            #       mother_xref_id
            #
            indis = dict()

            for indi in parser.records0('INDI'):
                xref_id = indi.xref_id
                first_name = indi.name.format() or ''
                gender = indi.sub_tag_value('SEX')
                if gender:
                    gender = gender.lower()
                    if gender not in (GenderMixin.GENDER_MALE, GenderMixin.GENDER_FEMALE):
                        gender = None
                dob = indi.sub_tag_value('BIRT/DATE') or None
                if dob:
                    dob = UnclearDate.from_str_safe(str(dob), format='d M y')
                is_dead = bool(indi.sub_tag_value('DEAT'))
                dod = indi.sub_tag_value('DEAT/DATE') or None
                if dod:
                    dod = UnclearDate.from_str_safe(str(dod), format='d M y')
                    is_dead = True
                item = dict(
                    first_name=first_name,
                    gender=gender,
                    dob=dob,
                    is_dead=is_dead,
                    dod=dod,
                    father_xref_id=indi.father and indi.father.xref_id or None,
                    mother_xref_id=indi.mother and indi.mother.xref_id or None,
                )
                indis[xref_id] = item

        if indi_to_merge not in indis:
            raise ServiceException('В gedcom данных не обнаружен человек, который будет владельцем')

        for key in indis:
            item = indis[key]
            # Сначала создать пользователей, потом родительские связи
            user = self.create_user(
                first_name=item['first_name'] or 'Без имени',
                owner=owner,
                dob=item['dob'],
                is_dead=item['is_dead'],
                dod=item['dod'],
                is_active=False,
                gender=item['gender'],
            )
            item.update(user_id=user.pk)

        for key in indis:
            item = indis[key]
            if item['father_xref_id']:
                user_from = User.objects.select_related('profile').get(pk=item['user_id'])
                user_to = User.objects.select_related('profile').get(pk=indis[item['father_xref_id']]['user_id'])
                self.add_operation(
                    user_from,
                    user_to.profile,
                    operationtype_id = OperationType.SET_FATHER,
                    comment = None,
                    insert_timestamp = int(time.time()),
                )
            if item['mother_xref_id']:
                user_from = User.objects.select_related('profile').get(pk=item['user_id'])
                user_to = User.objects.select_related('profile').get(pk=indis[item['mother_xref_id']]['user_id'])
                self.add_operation(
                    user_from,
                    user_to.profile,
                    operationtype_id = OperationType.SET_MOTHER,
                    comment = None,
                    insert_timestamp = int(time.time()),
                )

        user_to_merge = User.objects.select_related('profile').get(pk=indis[indi_to_merge]['user_id'])
        owner.profile.merge(user_to_merge.profile)

api_import_gedcom = ApiImportGedcom.as_view()

class ApiBotPoll(APIView):

    @transaction.atomic
    def post(self, request):
        """
        Создать телеграм опрос

        Принимает то, что отдает телеграм при создании опроса:
        {
            "message_id": 13052,
            "from": {"id": 12345, "is_bot": true, "first_name": "SevTrusts", "username": "DevBlagoBot"},
            "chat": {"id": 54321, "first_name": "Евгений", "last_name": "Фамилия", "username": "his_username", "type": "private"},
            "date": 1677680550,
            "poll": {
                "id": "987654321",
                "question": "Как дела",
                "options": [
                        {"text": "Отлично", "voter_count": 0},
                        {"text": "Хорошо", "voter_count": 0},
                        {"text": "Плохо", "voter_count": 0}
                    ],
                    "total_voter_count": 0, "is_closed": false, "is_anonymous": false, "type": "regular", "allows_multiple_answers": false
                }
        }
        Но не всё использует
        Еще в исходных данных должно быть: request.data.get('tg_token') == settings.TELEGRAM_BOT_TOKEN
        Проверок не производим: если бот правильно отдаст запрос, и здесь всё будет правильно
        """
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            tgpoll, created_ = TgPoll.objects.get_or_create(
                poll_id=request.data['poll']['id'],
                defaults=dict(
                    question=request.data['poll']['question'],
                    message_id=request.data['message_id'],
                    chat_id=request.data['chat']['id'],
            ))
            if created_:
                TgPollAnswer.objects.create(tgpoll=tgpoll, number=0, answer='')
                for i, option in enumerate(request.data['poll']['options']):
                    TgPollAnswer.objects.create(tgpoll=tgpoll, number=i+1, answer=option['text'])
            data = tgpoll.data_dict()
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_bot_poll = ApiBotPoll.as_view()

class ApiBotPollAnswer(APIView):

    @transaction.atomic
    def post(self, request):
        """
        Послать или отменить голос в телеграм опрос

        {
            "poll_id": "54321",
            "user": {
                "id": 12345, "is_bot": false, "first_name": "Eugene",
                "last_name": "Surname", "username": "his_username", "language_code": "ru"
            },
            "option_ids": [0]
        }
        Принимает то, что отдает телеграм при получении голоса:
        Но не всё использует
        Еще в исходных данных должно быть: request.data.get('tg_token') == settings.TELEGRAM_BOT_TOKEN
        Проверок не производим: если бот правильно отдаст запрос, и здесь всё будет правильно
        """
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            try:
                tgpoll = TgPoll.objects.get(poll_id=request.data['poll_id'])
            except (KeyError, TgPoll.DoesNotExist,):
                raise ServiceException('Не найден опрос')
            try:
                oauth = Oauth.objects.get(
                    provider = Oauth.PROVIDER_TELEGRAM,
                    uid=str(request.data['user']['id']),
                )
            except (KeyError, Oauth.DoesNotExist,):
                raise ServiceException('Телеграм пользователь не найден')
            for a in oauth.tg_poll_answers.filter(tgpoll=tgpoll):
                oauth.tg_poll_answers.remove(a)
            try:
                if request.data['option_ids']:
                    for o in request.data['option_ids']:
                        number = o + 1
                        tgpollanswer = TgPollAnswer.objects.get(tgpoll=tgpoll, number=number)
                        oauth.tg_poll_answers.add(tgpollanswer)
                else:
                    tgpollanswer = TgPollAnswer.objects.get(tgpoll=tgpoll, number=0)
                    oauth.tg_poll_answers.add(tgpollanswer)
            except (KeyError, TgPollAnswer.DoesNotExist,):
                raise ServiceException('Получен не существующий ответ')
            data = {}
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_bot_poll_answer = ApiBotPollAnswer.as_view()


class ApiBotPollResults(TelegramApiMixin, APIView):
    """
    Получить результаты "родного" телеграм- опроса и отношения межлу участниками опроса

    Возможно полчение результата методом get или post
    с одним и тем же параметром tg_poll_id, id запроса
    в телеграме

    GET:
        требует авторизации
    POST
        требует наличия токена бота (tg_token)

    На выходе (например):
    {
        "question": "Как дела",
        "message_id": 15026,
        "chat_id": 1109405488,
        "bot_username": "DevBlagoBot",
        "nodes": [
            {
                "id": 0,
                "first_name": "Без ответа",
                "photo": "http://api.blagoroda.bsuir.by/thumb/images/poll_answer_0.jpg/128x128~crop-white-frame-10~12.jpg"
            },
            {
                "id": -1,
                "first_name": "Отлично",
                "photo": "http://api.blagoroda.bsuir.by/thumb/images/poll_answer_1.jpg/128x128~crop-red-frame-10~12.jpg"
            },
            {
                "id": -2,
                "first_name": "Хорошо",
                "photo": "http://api.blagoroda.bsuir.by/thumb/images/poll_answer_2.jpg/128x128~crop-purple-frame-10~12.jpg"
            },
            {
                "id": -3,
                "first_name": "Плохо",
                "photo": "http://api.blagoroda.bsuir.by/thumb/images/poll_answer_3.jpg/128x128~crop-orange-frame-10~12.jpg"
            },
            {
                "id": 1506,
                "uuid": "6fb2699e-e105-4f62-b2c5-aaaaaaaaaaaa',
                "first_name": "Иван",
                "photo": "http://api.blagoroda.bsuir.by/thumb/profile-photo/2023/05/16/1506/photo.jpg/128x128~crop~12.jpg",
            },
            {
                "id": 326,
                "uuid": "8f686101-c5a2-46d0-a5ee-bbbbbbbbbbbb"
                "first_name": "Петр",
                "photo": "http://api.blagoroda.bsuir.by/thumb/profile-photo/2023/05/15/326/photo.jpg/128x128~crop~12.jpg",
            }
        ],
        "links": [
            {
                "source": 1506,
                "target": -1,
                "is_poll": true
            },
            {
                "source": 326,
                "target": -2,
                "is_poll": true
            },
            {
                "source": 326,
                "target": 1506,
                "attitude": "mt"
            }
        ]
    }

    Если опрос не найден или не задан tg_poll_id, то HTTP_404_NOT_FOUND
    Если в методе post не задан или неверный tg_token, то HTTP_400_BAD_REQUEST
    """

    def do_it(self, request, poll_id):
        try:
            tgpoll = TgPoll.objects.get(poll_id=poll_id)
            nodes = []
            links = []
            data = dict(
                question=tgpoll.question,
                message_id=tgpoll.message_id,
                chat_id=tgpoll.chat_id,
            )
            for answer in TgPollAnswer.objects.filter(tgpoll=tgpoll):
                nodes.append(dict(
                    id=-answer.number if answer.number else 0,
                    first_name=answer.answer if answer.number else 'Без ответа',
                    photo=Profile.image_thumb(request, 'images/poll_answer_%s.jpg' % answer.number,
                    width=128, height=128,
                    method='crop-%s-frame-%s' % (settings.OFFER_ANSWER_COLOR_MAP[answer.number], 10,),
                )))
            prefetch = Prefetch('oauth_set', queryset=Oauth.objects.select_related('user', 'user__profile').filter(provider=Oauth.PROVIDER_TELEGRAM))
            queryset = TgPollAnswer.objects.prefetch_related(prefetch).select_related('tgpoll').filter(tgpoll=tgpoll)
            user_pks = set()
            for answer in queryset:
                for oauth in answer.oauth_set.all():
                    user = oauth.user
                    if user.pk not in user_pks:
                        user_pks.add(user.pk)
                        nodes.append(user.profile.data_dict(request, fmt='3d-force-graph'))
                    links.append(dict(
                        source=user.pk,
                        target=-answer.number,
                        is_poll=True,
                    ))
            q_connections = Q(
                attitude__isnull=False, is_reverse=False,
                user_from__in=user_pks, user_to__in=user_pks
            )
            for cs in CurrentState.objects.filter(q_connections).select_related(
                        'user_from__profile', 'user_to__profile',).distinct():
                links.append(dict(source=cs.user_from.pk, target=cs.user_to.pk, attitude=cs.attitude))

            bot_username = self.get_bot_username()
            data.update(bot_username=bot_username, nodes=nodes, links=links)
            status_code = status.HTTP_200_OK
        except (TypeError, ValueError, TgPoll.DoesNotExist,):
            data = {}
            status_code = status.HTTP_404_NOT_FOUND
        return Response(data=data, status=status_code)

    def get(self, request):
        # if not request.user.is_authenticated:
        #     raise NotAuthenticated
        return self.do_it(request, request.GET.get('tg_poll_id'))

    def post(self, request):
        if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
            data = dict(message='Неверный токен телеграм бота')
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        return self.do_it(request, request.data.get('tg_poll_id'))

api_bot_poll_results = ApiBotPollResults.as_view()


class ApiOfferMixin(object):

    def put_location(self, request, offer):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if latitude is not None and longitude is not None:
            offer.put_geodata(latitude, longitude)


class ApiOffer(ApiOfferMixin, UuidMixin, APIView):

    @transaction.atomic
    def post(self, request):
        """
        Создать опрос/предложение

        На входе:
        {
            "tg_token": settings.TELEGRAM_BOT_TOKEN,
            "user_uuid": ....,
            "question": "Как дела",
            "is_multi": True,
            "answers": [
                    {"text": "Отлично"},
                    {"text": "Хорошо"},
                    {"text": "Плохо"}
                ],
        }
        """
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            owner, profile = self.check_user_uuid(uuid=request.data.get('user_uuid'), related=('user',))
            if not request.data.get('question'):
                raise ServiceException('Не задан вопрос')
            if not request.data.get('answers'):
                raise ServiceException('Не заданы ответы')
            elif len(request.data['answers']) > Offer.MAX_NUM_ANSWERS:
                raise ServiceException('Число ответов > %s' % Offer.MAX_NUM_ANSWERS)
            offer = Offer.objects.create(
                owner=owner,
                question=request.data['question'],
                is_multi=request.data['is_multi'],
            )
            self.put_location(request, offer)
            offeranswer0 = OfferAnswer.objects.create(offer=offer, number=0, answer='')
            # Создатель опроса его видел. Ему присваивается "фиктивный" номер 0 ответа
            profile.offer_answers.add(offeranswer0)
            for i, answer in enumerate(request.data['answers']):
                if not answer.strip():
                    raise ServiceException('Обнаружен пустой вопрос')
                OfferAnswer.objects.create(offer=offer, number=i+1, answer=answer)
            data = offer.data_dict()
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

    def get(self, request):
        try:
            if request.GET.get('uuid'):
                qs = Q(uuid=request.GET['uuid'])
            elif request.GET.get('offer_id'):
                qs = Q(pk=request.GET['offer_id'])
            else:
                raise ValueError
            offer = Offer.objects.select_related('owner', 'owner__profile').get(qs)
            user_ids_only=request.GET.get('user_ids_only')
            data = dict(offer=offer.data_dict(request=request, user_ids_only=user_ids_only))
            status_code = status.HTTP_200_OK
        except (TypeError, ValueError, ValidationError, Offer.DoesNotExist,):
            data = {}
            status_code = status.HTTP_404_NOT_FOUND
        return Response(data=data, status=status_code)

    def put(self, request):
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            try:
                offer = Offer.objects.get(uuid=request.data.get('offer_uuid'))
                tgdesc_dict = request.data['tgdesc']
            except (TypeError, KeyError, ValueError, ValidationError, Offer.DoesNotExist,):
                raise ServiceException('Опрос не найден или не заданы необходимые параметры')
            if str(offer.owner.username) != request.data.get('username'):
                raise PermissionDenied()
            if request.data.get('is_first'):
                offer.tgdesc.filter(
                    ~Q(uuid_pack=tgdesc_dict['uuid_pack'])
                ).delete()
            tgdesc = TgDesc.objects.create(**tgdesc_dict)
            offer.tgdesc.add(tgdesc)
            data = {}
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_offer = ApiOffer.as_view()


class ApiOfferList(APIView):

    def get(self, request):
        """
        Список офферов юзера с uuid = request.GET.get('uuid')
        """
        try:
            data = [
                dict(
                    offer=dict(question=offer.question,uuid=offer.uuid, closed_timestamp=offer.closed_timestamp)
                ) for offer in Offer.objects.filter(
                    owner__profile__uuid=request.GET.get('uuid'),
                    ).select_related('owner', 'owner__profile',
                    ).distinct()
            ]
        except ValidationError:
            data = []
        return Response(data=data, status=status.HTTP_200_OK)

api_offer_list = ApiOfferList.as_view()


class ApiOfferAnswer(ApiDonateUser, ApiOfferMixin, UuidMixin, APIView):

    @transaction.atomic
    def post(self, request):
        """
        Послать или отменить голос в опрос-предложение

        На входе:
        {
            "tg_token": settings.TELEGRAM_BOT_TOKEN,
            "offer_uuid": "...",
            "user_uuid": "...",
            "referrer_username"
            "answers": [1]  // Нумерация ответов начинается с 1 !!!
                            // Есть возможность обрабатывать сразу несколько
                            // полученных ответов, но из бота всегда приходит
                            // выбранный голос в массиве из одного голоса
                            // Если [0], то сброс ответов
                            // Если [-1], то только показать текущие результаты
                            // [-2] прийти не может, это сообщение участникам
                            // Если [-3], то остановить опрос
                            // Если [-4], то возобновить опрос
                            // Если [-5], то задать координаты
                            // Если [-6], то задать описание, обрабатывается без вызова сюда
        }
        В случае успеха на выходе словарь опроса с ответами, кто за что отвечал:
            offer.data_dict(request)
        Если ответ больше нуля, то это голосование за выбор.
        Этот факт фиксируется в журнале: от user_uuid к referrer_username пошел голос
        """
        try:
            data = dict()
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            owner, profile = None, None
            if request.data.get('user_uuid'):
                owner, profile = self.check_user_uuid(uuid=request.data.get('user_uuid'), related=('user',))
            try:
                offer = Offer.objects.get(uuid=request.data.get('offer_uuid'))
            except (KeyError, TypeError, ValidationError, Offer.DoesNotExist,):
                raise ServiceException('Не найден опрос')
            if profile:
                numbers = request.data['answers']
                if len(numbers) == 1 and numbers[0] == -1:
                    # Обновить. Если еще не голосовал или впервые видит
                    # опрос, задать фиктивный номер 0: видел опрос
                    if profile.offer_answers.filter(offer=offer).count() == 0:
                        offeranswer0 = OfferAnswer.objects.get(offer=offer, number=0)
                        profile.offer_answers.add(offeranswer0)
                # numbers[0] == -2: пропускаем, это сообщение участникам
                elif len(numbers) == 1 and numbers[0] == -3 and owner == offer.owner:
                    # Остановить опрос
                    if owner == offer.owner:
                        if not offer.closed_timestamp:
                            offer.closed_timestamp = int(time.time())
                            offer.save(update_fields=('closed_timestamp',))
                    else:
                        raise PermissionDenied()
                elif len(numbers) == 1 and numbers[0] == -4:
                    # Возобновить опрос
                    if owner == offer.owner:
                        if offer.closed_timestamp:
                            offer.closed_timestamp = None
                            offer.save(update_fields=('closed_timestamp',))
                    else:
                        raise PermissionDenied()
                elif len(numbers) == 1 and numbers[0] == -5:
                    # Указать координаты
                    if owner == offer.owner:
                        self.put_location(request, offer)
                    else:
                        raise PermissionDenied()
                elif len(numbers) == 1 and numbers[0] == -6:
                    pass
                elif not offer.closed_timestamp:
                    current_numbers_set = set([a.number for a in profile.offer_answers.filter(offer=offer)])
                    if profile and current_numbers_set.union(set(numbers)) != current_numbers_set:
                        if len(numbers) == 1 and numbers[0] == 0 or not offer.is_multi:
                            for a in profile.offer_answers.filter(offer=offer):
                                profile.offer_answers.remove(a)
                        if offer.is_multi and len(numbers) == 1 and numbers[0] > 0:
                            if profile.offer_answers.filter(offer=offer, number=0).exists():
                                offeranswer0 = OfferAnswer.objects.get(offer=offer, number=0)
                                profile.offer_answers.remove(offeranswer0)
                        try:
                            offeranswer_n = None
                            for number in numbers:
                                offeranswer = OfferAnswer.objects.get(offer=offer, number=number)
                                if not offeranswer_n and number > 0:
                                   offeranswer_n = offeranswer
                                profile.offer_answers.add(offeranswer)

                            if offeranswer_n and request.data.get('username_ref') and owner:
                                try:
                                    user_ref = User.objects.get(username=request.data['username_ref'])
                                    journal = Journal.objects.create(
                                        user_from=owner,
                                        user_to=user_ref,
                                        operationtype=OperationType.objects.get(pk=OperationType.OFFER_VOTED),
                                        offer_answer=offeranswer_n,
                                    )
                                    data.update(journal_id=journal.pk)
                                    if donate := self.find_donate_to_user(owner, user_ref):
                                        data.update(donate=donate)
                                except (User.DoesNotExist, OperationType.DoesNotExist,):
                                    pass

                        except (KeyError, OfferAnswer.DoesNotExist,):
                            raise ServiceException('Получен не существующий ответ')
            data.update(offer=offer.data_dict(request, user_ids_only=True))
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_offer_answer = ApiOfferAnswer.as_view()


class ApiOfferResults(TelegramApiMixin, APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Получить результаты опроса-предложения в пригодном для отображения всех связей пользователь - ответ

        Включая связи доверия
        """
        try:
            offer_uuid = request.GET.get('offer_uuid')
            offer = Offer.objects.get(uuid=offer_uuid)
            offer_dict = offer.data_dict(request, user_ids_only=False)
            nodes = []
            links = []
            data = dict(question=offer.question)
            user_pks = set()
            for answer in offer_dict['answers']:
                nodes.append(dict(
                    id=-answer['number'],
                    first_name=answer['answer'] if answer['number'] else 'Без ответа',
                    photo=Profile.image_thumb(request, 'images/poll_answer_%s.jpg' % answer['number'],
                        width=128, height=128,
                        method='crop-%s-frame-%s' % (settings.OFFER_ANSWER_COLOR_MAP[answer['number']], 10,),
                )))
                for user in answer['users']:
                    if user['id'] not in user_pks:
                        user_pks.add(user['id'])
                        nodes.append(user)
                    links.append(dict(
                        source=user['id'],
                        target=-answer['number'],
                        is_offer=True,
                    ))

            if request.user.is_authenticated and request.user.pk not in user_pks:
                user_pks.add(request.user.pk)
                nodes.append(request.user.profile.data_dict(request, fmt='3d-force-graph'))

            q_connections = Q(
                attitude__isnull=False, is_reverse=False,
                user_from__in=user_pks, user_to__in=user_pks
            )
            for cs in CurrentState.objects.filter(q_connections).select_related(
                        'user_from__profile', 'user_to__profile',).distinct():
                links.append(dict(source=cs.user_from.pk, target=cs.user_to.pk, attitude=cs.attitude))

            bot_username = self.get_bot_username()
            data.update(bot_username=bot_username, nodes=nodes, links=links)
            status_code = status.HTTP_200_OK
        except (TypeError, ValueError, ValidationError, Offer.DoesNotExist,):
            data = {}
            status_code = status.HTTP_404_NOT_FOUND
        return Response(data=data, status=status_code)

api_offer_results = ApiOfferResults.as_view()

class ApiOfferRef(APIView):

    @transaction.atomic
    def post(self, request):
        """
        Записать пригласившего и приглашенного в журнал и в состояние

        Если и тот, и другой один юзер, то только запись в журнал
        """
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            uu = dict()
            for f in ('username_from', 'username_to'):
                if not request.data.get(f):
                    raise ServiceException(f'Незадан параметр {f}')
                try:
                    uu[f] = User.objects.get(username=request.data[f])
                except User.DoesNotExist:
                    raise ServiceException(f'Не найден пользователь {request.data[f]}')
            if not request.data.get('offer_uuid'):
                raise ServiceException('Незадан параметр offer_uuid')
            try:
                offer = Offer.objects.get(uuid=request.data['offer_uuid'])
            except Offer.DoesNotExist:
                raise ServiceException('Не найден опрос/предложение')

            OfferRefJournal.objects.create(
                offer=offer,
                user_from=uu['username_from'],
                user_to=uu['username_to'],
            )

            if uu['username_from'] != uu['username_to']:
                offerrefstate, created = OfferRefState.objects.select_for_update().get_or_create(
                    offer=offer,
                    user_from=uu['username_from'],
                    user_to=uu['username_to'],
                )
                if not created:
                    offerrefstate.update_timestamp = int(time.time())
                    offerrefstate.save()

            data = dict()
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_offer_ref = ApiOfferRef.as_view()


class ApiVotedTgUsers(APIView):

    def post(self, request):
        """
        Получить проголосовавших в опросе-предложении телеграм- пользователей

        Владелец опроса не включается
        Не включаются пользователи, которые не доверяют юзеру
        На входе:
        {
            "tg_token": <settings.TELEGRAM_BOT_TOKEN>,
             "offer_uuid": <offer_uuid>,
             "user_uuid": <uuid пользователя, из чата которого отправлен запрос>
        }
        Если не найден опрос или владелец опроса имеет иной user_uuid, HTTP_404_NOT_FOUND
        Результат:
        {
            "question": "Как дела",
            "users": [
                {
                    "tg_data": [
                        {
                            "tg_uid": "1111111111"
                        }
                    ]
                },
                {
                    "tg_data": [
                        {
                            "tg_uid": "2222222222"
                        }
                    ]
                }
            ]
        }
        """
        data = dict()
        status_code = status.HTTP_404_NOT_FOUND
        if request.data.get('tg_token') == settings.TELEGRAM_BOT_TOKEN:
            try:
                offer_uuid = request.data.get('offer_uuid')
                offer = Offer.objects.select_related('owner','owner__profile').get(uuid=offer_uuid)
            except (TypeError, ValueError, ValidationError, Offer.DoesNotExist,):
                pass
            else:
                user_uuid = request.data.get('user_uuid')
                if str(user_uuid) != str(offer.owner.profile.uuid):
                    pass
                else:
                    data = dict(
                        question=offer.question,
                    )
                    q = Q(
                        provider=Oauth.PROVIDER_TELEGRAM,
                    )
                    q &= Q(
                        user__profile__offer_answers__offer__uuid=offer_uuid,
                        user__profile__offer_answers__number__gt=0,
                    ) & ~Q(user__profile__uuid=user_uuid)
                    users = dict()
                    for oauth in Oauth.objects.select_related('user', 'user__profile').filter(q).distinct():
                        if users.get(oauth.user.pk):
                            users[oauth.user.pk]['tg_data'].append(dict(tg_uid=oauth.uid))
                        else:
                            users[oauth.user.pk] = dict(
                                tg_data=[dict(tg_uid=oauth.uid)]
                            )
                    for cs in CurrentState.objects.filter(
                        is_reverse=False,
                        attitude=CurrentState.MISTRUST,
                        user_from__pk__in=users.keys(),
                        user_to__profile__uuid=user_uuid,
                        ).distinct():
                        del users[cs.user_from.pk]
                    data.update(users=users.values())
                    status_code = status.HTTP_200_OK
        return Response(data=data, status=status_code)

api_offer_voted_tg_users = ApiVotedTgUsers.as_view()

class ApiTokenUrl(TelegramApiMixin, APIView):
    """
    Зашить url в токене. Получить url из token

    Используем кэш redis!
    Token кодируется как uuid
    """

    # Префикс и разделитель полей для ключа
    #
    TOKEN_URL_PREFIX = 'urltoken'
    TOKEN_URL_SEP = '~'

    def post(self, request):
        """
        Зашить url в токене.

        На входе:
            {
                "url": "<url>"
            }
        На выходе:
            {
                "url": "<url>",
                "token": "<token>",
                // Это требуется для формирования ссылки login url
                // к кнопке телеграма
                "bot_username": "<bot_username>"
            }
        """
        validate = URLValidator()
        try:
            try:
                url = request.data.get('url')
                validate(url)
            except ValidationError:
                raise ServiceException('Неверный URL')
            token = str(uuid4())
            data = dict(
                url=request.data['url'],
                token=token,
                bot_username=self.get_bot_username(),
            )
            if r := redis.Redis(**settings.REDIS_TOKEN_CONNECT):
                r.set(
                    name=self.TOKEN_URL_PREFIX + self.TOKEN_URL_SEP + token,
                    value=url,
                    ex=settings.TOKEN_URL_EXPIRE,
                )
                r.close()
            else:
                raise ServiceException('Не удалось подключиться к хранилищу токенов (redis cache)')
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

    def get(self, request):
        """
        Получить url из token

        На входе:
            https:/.../path/to/?token=<token>
        На выходе:
            {
                "token": "<token>"
                "url": "<url>",
            }
            или HTTP_404_NOT_FOUND
        """
        data = dict()
        status_code = status.HTTP_404_NOT_FOUND
        token = str(request.GET.get('token'))
        token_in_redis = self.TOKEN_URL_PREFIX + self.TOKEN_URL_SEP + token
        if r := redis.Redis(**settings.REDIS_TOKEN_CONNECT):
            if url := r.get(token_in_redis):
                data = dict(token=token, url=url)
                # Так быстрее, чем delete, redis в фоне удалит через секунду
                r.expire(token_in_redis, 1)
                status_code = status.HTTP_200_OK
            r.close()
        return Response(data=data, status=status_code)

api_token_url = ApiTokenUrl.as_view()

class ApiTokenAuthData(ApiTokenAuthDataMixin, APIView):
    """
    Создать или получить зашитый в токене данные авторизационной куки

    Используем кэш redis!
    Token кодируется как uuid
    """

    # Префикс и разделитель полей для ключа: см ApiTokenAuthDataMixin
    #
    # TOKEN_AUTHDATA_PREFIX =
    # TOKEN_AUTHDATA_SEP

    def post(self, request):
        """
        Получить токен с зашитыми в нем данными авторизационной куки

        Post запрос.
        http(s)://<api-host>/api/token/authdata/
        Требует авторизации.
        На входе json, c собственно объектом авторизационной куки:
        {
            "auth_data": {
                "provider": "telegram",
                "user_id": <user.pk>,
                "user_uuid": <uuid>,
                "auth_token": <auth_token>
            }
        }
        Возвращает зашитое в токене содержимое request.data['auth_data']
        {
            "authdata_token": <токен>
        }
        """

        #   Требование к методу: максимально быстро. Посему:
        #       -   проверки почти нет
        #       -   обращения к б.д. за user_uuid и auth_token тоже нет

        if not request.user.is_authenticated:
            raise NotAuthenticated
        try:
            auth_data = request.data.get('auth_data')
            if not isinstance(auth_data, dict):
                raise ServiceException("Неверные данные")
            data = dict(authdata_token=self.make_authdata_token(auth_data))
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

    def get(self, request):
        """
        Получить данные авторизационной куки из token

        На входе:
            http(s)://<api-host>/api/token/authdata/?token=<token>
        На выходе:
            {
                "url": "<url>",
                "token": "<url>"
            }
            или HTTP_404_NOT_FOUND
        """
        data = dict()
        status_code = status.HTTP_404_NOT_FOUND
        token = str(request.GET.get('token'))
        token_in_redis = self.TOKEN_AUTHDATA_PREFIX + self.TOKEN_AUTHDATA_SEP + token
        if r := redis.Redis(**settings.REDIS_TOKEN_CONNECT):
            if auth_str := r.get(token_in_redis):
                try:
                    data = json.loads(auth_str)
                    status_code = status.HTTP_200_OK
                except ValueError:
                    pass
                # Так быстрее, чем delete, redis в фоне удалит через секунду
                r.expire(token_in_redis, 1)
            r.close()
        return Response(data=data, status=status_code)

api_token_authdata = ApiTokenAuthData.as_view()

class ApiTokenInvite(UuidMixin, APIView):
    """
    Зашить invite в токене. Получить данные invite из token

    Invite:
        Приглашение в бот: пользователь телеграма велит боту создать
        сообщение для приглашения своего собственного живого пользователя,
        содержащее ссылку типа:
            https://t.me/<имя_бота>?start=<токен>
        Пользователь пересылает это сообщение приглашаемому, тот давит
        на ссылку, если приглашаемого нет в системе, то создается.
        Собственный пользователь приглашающего становится тем
        приглашаемым.
    Используем кэш redis!
    Ключ токена:
        <TOKEN_INVITE_PREFIX><TOKEN_INVITE_SEP><токен>
    Данные токена:
        <uuid_приглашающего><TOKEN_INVITE_SEP><uuid_его_собственного>
    """

    # Префикс и разделитель полей для ключа токена
    #
    TOKEN_INVITE_PREFIX = 'invite'
    TOKEN_INVITE_SEP = '~'

    def post(self, request):
        """
        Зашить данные invite в токене. Получить данные из токена invite

        На входе
            Приглашающий:
                Зашить данные invite в токене:
                    {
                        "operation": "set",
                        "tg_token": settings.TELEGRAM_BOT_TOKEN,
                        "uuid_inviter": "<uuid>"
                        "uuid_to_merge": "<uuid>"   // user owned by inviter
                    }
                На выходе:
                    {
                        "token": "<токен>",
                    }
            Приглашаемый.
                Получает данные по ссылке (get) или подтверждает (accept) 
                    {
                        "operation": "get",         // получить данные по ссылке
                                     "accept",      // подтвердить
                        "tg_token": settings.TELEGRAM_BOT_TOKEN,
                        "token": "<token>"
                        "uuid_invited": "<uuid>"    // активный приглашаемый пользователь,
                                                    // нажавший на ссылку- приглашения
                    }
                На выходе:
                    {
                        "profile": {...}            // данные профиля
                                                    // при get: того с uuid_to_merge
                                                    // при accept: того с uuid_invited
                    }
        """
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            operation = request.data.get('operation')
            if operation == 'set':
                uuid_inviter = request.data.get('uuid_inviter')
                uuid_to_merge = request.data.get('uuid_to_merge')
                user_inviter, profile_inviter = self.check_user_uuid(uuid_inviter, related= ('user',))
                user_to_merge, profile_to_merge = self.check_user_uuid(uuid_to_merge, related= ('user',))
                if not profile_to_merge.owner or profile_to_merge.owner != user_inviter:
                    raise ServiceException('Нет прав на операцию')
                if profile_to_merge.is_dead:
                    raise ServiceException(f'{user_to_merge.first_name} умер. Нельзя приглашать умершего')
                token = str(uuid4())
                data = dict(token=token,)
                if r := redis.Redis(**settings.REDIS_TOKEN_CONNECT):
                    r.set(
                        name=self.TOKEN_INVITE_PREFIX + self.TOKEN_INVITE_SEP + token,
                        value=uuid_inviter + self.TOKEN_INVITE_SEP + uuid_to_merge,
                        ex=settings.TOKEN_INVITE_EXPIRE,
                    )
                    r.close()
                else:
                    raise ServiceException('Не удалось подключиться к хранилищу токенов (redis cache)')
            elif operation in ('get', 'accept'):
                token = request.data.get('token', 'token')
                token_in_redis = self.TOKEN_INVITE_PREFIX + self.TOKEN_INVITE_SEP + token
                if r := redis.Redis(**settings.REDIS_TOKEN_CONNECT):
                    if value_in_redis := r.get(token_in_redis):
                        values = value_in_redis.split(self.TOKEN_INVITE_SEP)
                        try:
                            uuid_inviter = values[0]
                            uuid_to_merge = values[1]
                        except IndexError:
                            raise ServiceException('Ошибка API')
                        # Часто может быть: приглашающий щелкнул на ссылку
                        uuid_invited = request.data.get('uuid_invited')
                        if uuid_invited == uuid_inviter:
                            raise ServiceException('Вы пригласили. Приглашенный -- кто-то другой, кому Вы потравите ссылку')
                        try:
                            user_invited, profile_invited = self.check_user_uuid(uuid_invited, related= ('user',))
                        except ServiceException:
                            raise ServiceException('Приглашающего уже нет в системе')
                        if Profile.objects.filter(owner=user_invited).exists():
                            raise ServiceException(
                                'У Вас уже есть связи - обратитесь, пожалуйста, в поддержку: /feedback'
                            )
                        if profile_invited.owner:
                            raise ServiceException('Приглашаемый является собственным')
                        try:
                            user_to_merge, profile_to_merge = self.check_user_uuid(uuid_to_merge, related= ('user',))
                        except ServiceException:
                            raise ServiceException('Приглашение уже не действует')
                        try:
                            user_inviter, profile_inviter = self.check_user_uuid(uuid_inviter, related= ('user',))
                        except ServiceException:
                            raise ServiceException('Приглашающий исчез из системы')
                        if not profile_to_merge.owner or profile_to_merge.owner != user_inviter:
                            raise ServiceException('Профиль, с которым было намечено Вас объединить, исчез или передан другому')
                        if profile_to_merge.is_dead:
                            raise ServiceException(f'{user_to_merge.first_name} умер. Нельзя объединять Вас с умершим')
                        if operation == 'get':
                            profile = profile_to_merge
                            profile_data = profile.data_dict(request)
                        else:
                            # accept
                            profile = profile_invited
                            profile.merge(profile_to_merge)
                            profile_data = profile.data_dict(request)
                            profile_data.update(profile.parents_dict(request))
                            profile_data.update(profile.data_WAK())
                            profile_data.update(profile.owner_dict())
                            profile_data.update(tg_data=profile.tg_data())
                            # Так быстрее, чем delete, redis в фоне удалит через секунду
                            r.expire(token_in_redis, 1)
                        data = dict(profile=profile_data)
                        status_code = status.HTTP_200_OK
                    else:
                        raise ServiceException('Приглашение уже принято')
                    r.close()

            else:
                raise ServiceException('Неверный вызов апи')
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_token_invite = ApiTokenInvite.as_view()

class ApiShortIdView(View):

    def get(self, request, short_id):
        try:
            user = User.objects.select_related('profile').get(username=short_id)
        except User.DoesNotExist:
            raise NotFound()
        return redirect(settings.SHORT_ID_URL % user.username)

api_short_id = ApiShortIdView.as_view()

class ApiCheckDateView(APIView):

    def get(self, request):
        try:
            date = request.GET.get('date', '').strip()
            if not date:
                raise ServiceException('Не задана дата')
            m = UnclearDate.check_safe_str(date, check_today=True)
            if m:
                raise ServiceException(m)
            y, m, d = UnclearDate.from_str_dmy(date)
            y_current = datetime.date.today().year
            try:
                min_age = int(request.GET.get('min_age', ''))
            except ValueError:
                min_age = None
            try:
                max_age = int(request.GET.get('max_age', ''))
            except ValueError:
                max_age = None
            if min_age and y_current - y < min_age:
                raise ServiceException('Слишком недавняя дата')
            if max_age and y_current - y > max_age:
                raise ServiceException('Слишком древняя дата')
            data=dict(date=date)
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_check_date = ApiCheckDateView.as_view()


class ApiGetBotData(TelegramApiMixin, APIView):
    def get(self, request):
        try:
            data = self.get_bot_data()
            if not data:
                raise ServiceException('Не удалось получить данные бота')
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_get_bot_data = ApiGetBotData.as_view()

class ApiMeetId(APIView):
    """
    Действия с meet_id

    Meet_id - это секрет. Запрос только из бота. И только post.
    Функции (в зависимости от наличия параметра в post запросе):
        username:   по username получить meet_id, если он есть,
                    иначе создать и отдать meet_id:
                        dict(meet_id=<meet_id>)
        meet_id:    по meet_id получить профиль пользователя:
                        dict(profile=<profile>)
    """

    @transaction.atomic
    def post(self, request):
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            data = dict()
            if request.data.get('username'):
                try:
                    profile = Profile.objects.select_for_update(
                        ).get(
                        user__username=request.data['username']
                    )
                    done = False
                    if profile.meet_id:
                        done = True
                    else:
                        chars = string.ascii_lowercase + string.digits + string.ascii_uppercase
                        meet_id_len = Profile._meta.get_field('meet_id').max_length
                        random.seed()
                        for i in range(1000):
                            with transaction.atomic():
                                try:
                                    profile.meet_id = ''.join(random.choice(chars) for x in range(meet_id_len))
                                    profile.save(update_fields=('meet_id',))
                                    done = True
                                    break
                                except IntegrityError:
                                    continue
                    if done:
                        data.update(meet_id=profile.meet_id)
                    else:
                        raise ServiceException('Не удалось создать уникальный meet_id')
                except Profile.DoesNotExist:
                    raise NotFound

            elif request.data.get('meet_id'):
                try:
                    profile = Profile.objects.get(meet_id=request.data['meet_id'])
                    data.update(profile=profile.data_dict(request))
                    data['profile'].update(tg_data=profile.tg_data())
                except Profile.DoesNotExist:
                    raise NotFound
            status_code = status.HTTP_200_OK

        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_meet_id = ApiMeetId.as_view()

class ApiShowTgmsgPack(TelegramApiMixin, APIView):

    def post(self, request):
        """
        Вывод пачки сообщений

        Параметры:
            uuid_pack:  в соответствующей таблице это идентифицирует пачку
                или
            messages:   готовые сообщения для показа

            username:   кому выводим в телеграме
            what:       messages, если пачку берем из TgMessageJournal,
                        иначе из TgDesc
        """
        try:
            if request.data.get('tg_token') != settings.TELEGRAM_BOT_TOKEN:
                raise ServiceException('Неверный токен телеграм бота')
            d_parms = dict(what='tgdesc')
            for parm in ('username', 'what'):
                if parm in request.data:
                    d_parms[parm] = request.data[parm]
                if not d_parms.get(parm):
                    raise ServiceException(f"Не указан параметр '{parm}'")
            try:
                user = User.objects.get(username=d_parms['username'])
            except User.DoesNotExist:
                raise ServiceException(f"Не найден user '{d_parms['username']}'")
            model = TgMessageJournal if d_parms['what'] == 'messages' else TgDesc

            d_parms['uuid_pack'] = request.data['uuid_pack'] if request.data.get('uuid_pack') else None
            d_parms['messages'] = request.data['messages'] if request.data.get('messages') else None
            if d_parms['uuid_pack']:
                messages = [
                    m.message_dict() for m in model.objects.filter(
                            uuid_pack=d_parms['uuid_pack']
                        ).order_by('message_id')
                ]
            elif d_parms['messages']:
                messages = d_parms['messages']

            options = dict(
                disable_web_page_preview=True,
                disable_notification=True,
            )
            if not self.send_pack_to_telegram(messages, user, options=options):
                raise ServiceException('Ошибка передачи сообщения')
            data = dict()
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

api_show_tgmsg_pack = ApiShowTgmsgPack.as_view()


class ApiMeetgamers(TelegramApiMixin, APIView):
    permission_classes = (IsAuthenticated, )

    def make_cs(self, cs, links):
        link_pattern = dict(
            source=cs.user_from.pk,
            target=cs.user_to.pk,
        )
        if cs.attitude is not None and not cs.is_reverse:
            link = link_pattern.copy()
            link.update(attitude=cs.attitude)
            links.append(link)
        if cs.is_invite_meet and not cs.is_invite_meet_reverse:
            link = link_pattern.copy()
            link.update(is_invite_meet=True)
            links.append(link)
        if cs.is_sympa and not cs.is_sympa_reverse and cs.is_sympa_confirmed:
            link = link_pattern.copy()
            link.update(is_sympa=True)
            links.append(link)
        if cs.is_hide_meet:
            link = link_pattern.copy()
            link.update(is_hide_meet=True)
            links.append(link)


    def get(self, request):
        fmt = '3d-force-graph'

        username = request.GET.get('id')
        links = []
        users = []
        user_pks = set()

        if request.user.profile.did_meet is None:
            raise PermissionDenied()
        if username:
            try:
                user = User.objects.get(username=username)
                root_node = user.profile.data_dict(request=request, fmt=fmt)
                qs_cs = Q(user_to__isnull=False,) & \
                        (Q(user_from=user) | Q(user_to=user)) & \
                        Q(attitude__isnull=False, is_reverse=False) | \
                        Q(is_invite_meet=True, is_invite_meet_reverse=False) | \
                        Q(is_sympa_confirmed=True, is_sympa_reverse=False) 
                        # vd temporary exclude hide links
                        # | \ Q(is_hide_meet=True)
                for cs in CurrentState.objects.filter(qs_cs
                        ).distinct():
                    user_pks.add(cs.user_from.pk)
                    user_pks.add(cs.user_to.pk)
            except User.DoesNotExist:
                pass
            for profile in Profile.objects.select_related('user').filter(
                    user__pk__in=user_pks
                ):
                data_dict = profile.data_dict(request=request, fmt=fmt)
                if profile.user == user:
                    color = 'blue'; frame = 5; thumb_size_popup = 72
                    method = 'crop-%s-frame-%s' % (color, frame)
                    data_dict['photo'] = Profile.image_thumb(
                        request, profile.photo,
                        method=method,
                        width=thumb_size_popup + frame * 2,
                        height=thumb_size_popup + frame * 2,
                        put_default_avatar=True,
                        default_avatar_in_media=PhotoModel.get_gendered_default_avatar(profile.gender)
                )
                users.append(data_dict)
                user_pks.add(profile.user.pk)
        else:
            from_ = number_ = None
            try:
                from_ = int(request.GET.get('from'))
                if from_ < 0:
                    from_ = 0
            except (ValueError, TypeError,):
                pass
            try:
                number_ = int(request.GET.get('number'))
            except (ValueError, TypeError,):
                pass
            if number_ and from_ is None:
                from_ = 0
            if from_ is not None and not number_:
                number_ = settings.PAGINATE_USERS_COUNT

            qs_profile = Profile.objects.select_related('user').filter(
                    did_meet__isnull=False,
                ).order_by(
                    '-user__date_joined'
                ).distinct()
            if from_ is not None and number_ is not None:
                qs_profile = qs_profile[from_: from_ + number_]

            for profile in qs_profile:
                users.append(profile.data_dict(request=request, fmt=fmt))
                user_pks.add(profile.user.pk)

        if request.user.is_authenticated and request.user.pk not in user_pks:
            user_pks.add(request.user.pk)
            users.append(request.user.profile.data_dict(request=request, fmt=fmt))

        for cs in CurrentState.objects.filter(
                user_from__in=user_pks, user_to__in=user_pks,
                ).distinct():
            self.make_cs(cs, links)

        bot_username = self.get_bot_username()
        data = dict(bot_username=bot_username, nodes=users, links=links)
        if username:
            data.update(root_node=root_node)
        return Response(data=data, status=status.HTTP_200_OK)

api_meetgamers = ApiMeetgamers.as_view()
