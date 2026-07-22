import datetime, string, random, os, binascii, time, logging
import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlencode
import json, re, hashlib
from decimal import Decimal
from uuid import uuid4, UUID

from django.conf import settings
from django.db import models, transaction, IntegrityError, connection
from django.db.models import Sum, F, Prefetch
from django.db.models.query_utils import Q
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.apps import apps
get_model = apps.get_model

from app.models import UnclearDateModelField, GenderMixin

from app.models import BaseModelInsertUpdateTimestamp, BaseModelInsertTimestamp, PhotoModel, GeoPointAddressModel
from app.utils import ServiceException

class TgGroup(BaseModelInsertTimestamp):
    """
    В каких группах присутствует бот
    """

    chat_id = models.BigIntegerField(_("Chat Id"), unique=True, db_index=True)
    title = models.CharField(_("Имя"), max_length=256)
    type = models.CharField(_("Тип"), max_length=50)
    # Сообщение для прикрепления к группе/каналу
    pin_message_id = models.BigIntegerField(_("Id of Message for Pin"), null=True)

    def data_dict(self):
        return {
            'id': self.pk,
            'type': self.type,
            'title': self.title,
            'chat_id': self.chat_id,
            'insert_timestamp': self.insert_timestamp,
            'pin_message_id': self.pin_message_id,
        }

    def __str__(self):
        return '%s (%s)' % (self.title, self.chat_id)

class Oauth(BaseModelInsertUpdateTimestamp):

    PROVIDER_GOOGLE = 'google'
    PROVIDER_TELEGRAM = 'telegram'
    PROVIDER_YANDEX = 'yandex'
    PROVIDER_VKONTAKTE = 'vk'
    PROVIDER_ODNOKLASSNIKI = 'odnoklassniki'

    OAUTH_PROVIDERS = (
        (PROVIDER_GOOGLE, _("Google")),
        (PROVIDER_TELEGRAM, _("Telegram")),
        (PROVIDER_YANDEX, _("Яндекс")),
        (PROVIDER_VKONTAKTE, _("ВКонтакте")),
        (PROVIDER_ODNOKLASSNIKI, _("Одноклассники")),
    )

    PROVIDER_DETAILS = {
        PROVIDER_YANDEX: {
            'url': "https://login.yandex.ru/info?format=json&oauth_token=%(token)s",
            'uid': 'id',
            'first_name': "first_name",
            'last_name': "last_name",
            'display_name': "real_name",
            'email': 'default_email',
            'username': 'login',
            'photo': 'default_avatar_id',
            'photo_template': 'https://avatars.yandex.net/get-yapic/%(photo_id)s/islands-200',
            'no_photo_re': r'^[0\-\/]+$',

            # Получаем от yandex:
                #{
                    #"id": "2731235527",
                    #"login": "supdghhdhd",
                    #"client_id": "cf3f076367fda00041eaa223761237623476",
                    #"display_name": "ivanov",
                    #"real_name": "Иван Иванов",
                    #"first_name": "Иван",
                    #"last_name": "Иванов",
                    #"sex": "male",
                    #"default_email": "shjhashsh@yandex.by",
                    #"emails": [
                        #"supsdhdh@yandex.by"
                    #],
                    #"birthday": "1999-06-20",
                    #"default_avatar_id": "45848/6ZJ0cT3Y3c3cDasdgjasdghasd0oqHevdVQ-1",
                    #"is_avatar_empty": false,
                    #"psuid": "1.AAcEbg.0ezg0dsfjsdfjhsdfRA4qpCA.tR78f2grSo0kZfx5IZlOqQ"
                #}
        },
        PROVIDER_VKONTAKTE: {
            'url': "https://api.vk.com/method/users.get?access_token=%(token)s"
                   "&fields=uid,first_name,last_name,photo_200,sex"
                   "&v=5.89",
            'uid': 'id',
            'first_name': "first_name",
            'last_name': "last_name",
            'display_name': None,
            'photo': 'photo_200',
            # Если такое приходит в фото, то это заглушка под отсутствие фото,
            # например, http://vk.com/images/camera_200.png
            'no_photo_re': r'/images/camera_\S*\.\S{3}$',
            'site': 'site',

            # Получаем от vkontakte
            #{
                #"response":[
                    #{
                        #"first_name":"Евгений",
                        #"id":56262662627,
                        #"last_name":"Супрун",
                        #"can_access_closed":True,
                        #"is_closed":False,
                        #"photo_200":"https://sun2.beltelecom-by-minsk.userapi.com/hshshsh.jpg"
                                    #"?size=200x0&quality=96&crop=113,101,593,593&ava=1"
                    #}
                #]
            #}
        },
        PROVIDER_ODNOKLASSNIKI: {
            # Внимание! Именно http://
            'url': "http://api.ok.ru/fb.do?method=users.getCurrentUser&"
                   "access_token=%(token)s&"
                   "application_key=%(public_key)s&"
                   "fields=user.*&"
                   "format=json&"
                   "sig=%(signature)s",
            'uid': 'uid',
            'first_name': "first_name",
            'last_name': "last_name",
            'display_name': "name",
            'email': 'email',
            'photo': 'pic190x190',
        },

        # Получаем от одноклассников
        #{
            #'uid': '5626262',
            #'birthday': '1978-06-22',
            #'birthdaySet': True,
            #'age': 42,
            #'first_name': 'Петр',
            #'last_name': 'Иванов',
            #'name': 'Петр Иванов',
            #'locale': 'ru',
            #'gender': 'male',
            #'has_email': True,
            #'location': {
                #'city': 'Минск',
                #'country': 'BELARUS',
                #'countryCode': 'BY',
                #'countryName': 'Беларусь'
                #},
            #'online': 'web',
            #'photo_id': '8363576312366123',
            #'pic_1': 'https://pic_1',
            #'pic_2': 'https://pic_2',
            #'pic_3': 'https://pic_3',
            #'pic_4': 'https://pic_4',
            #'pic_5': 'https://pic_5',
            #'pic50x50': 'https://pic_1',
            #'pic128x128': 'https://pic_5',
            #'pic128max': 'https://pic_2',
            #'pic180min': 'https://pic180min',
            #'pic240min': 'https://pic240min',
            #'pic320min': 'https://pic320min',
            #'pic190x190': 'https://pic_3',
            #'pic640x480': 'https://pic_4',
            #'pic1024x768': 'https://pic1024x768',
            #'pic_full': 'https://pic_full',
            #'pic_base': 'https://pic_base',
            #'url_profile': 'https://ok.ru/profile/56105959595',
            #'url_profile_mobile': 'https://m.ok.ru/profile/56105959595',
            #'premium': False,
            #'has_phone': True
        #}
    }

    # Поля, кроме provider, uid, user, которые запоминаем в таблице Oauth

    OAUTH_EXTRA_FIELDS = (
        'first_name',
        'last_name',
        'display_name',
        'username',
        # 'email',
        'photo',
    )

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    provider = models.CharField(_("Провайдер"), max_length=100, choices=OAUTH_PROVIDERS)
    uid = models.CharField(_("Ид пользователя у провайдера"), max_length=255,)

    # Эти данные пока не заносятся. В дальнейшем, с согласия клиента
    #
    last_name = models.CharField(_("Фамилия у провайдера"), max_length=255, default='')
    first_name = models.CharField(_("Имя у провайдера"), max_length=255, default='')
    username = models.CharField(_("Логин у провайдера"), max_length=255, default='')
    display_name = models.CharField(_("Отображаемое имя у провайдера"), max_length=255, default='')
    email = models.EmailField(_("Email у провайдера"), max_length=255, default='')
    photo = models.URLField(_("Фото у провайдера"), max_length=255, default='')
    groups = models.ManyToManyField(TgGroup, verbose_name=_("Группы telegram пользователя"))
    tg_poll_answers = models.ManyToManyField('users.TgPollAnswer', verbose_name=_("Ответы на опросы телеграм"))

    class Meta:
        unique_together = ('provider', 'uid')

    def get_display_name(self):
        return self.display_name or \
               " ".join((self.first_name, self.last_name, )).strip()

    def __str__(self):
        dn = self.get_display_name()
        if dn:
            dn = "%s (%s)" % (dn, self.provider)
        else:
            dn = "%s (uid=%s)" % (self.provider, self.uid)
        return dn

    def tg_data(self):
        return dict(tg_uid=self.uid, tg_username=self.username)

    @classmethod
    def check_token(cls, oauth_dict):
        """
        Проверить token у провайдера Oauth. Token & provider в входном oauth_dict
        
        oauth_dict:
        {
            "provider": "google",
            "token": ".....",
        }
        Вернуть словарь из необходимого для записи в auth.User & users.Oauth:
            last_name, first_name, display_name, email, photo
        А также
            message (сообщение об ошибке)
            code: если 401, то Unaiuhorized, иначе 200 или 400
        """

        result = dict(
            uid='',

            last_name='',
            first_name='',
            display_name='',
            email='',
            photo='',
            username='',

            message='',
            code=200,
        )
        try:
            try:
                provider = oauth_dict['provider']
                provider_details = Oauth.PROVIDER_DETAILS[oauth_dict['provider']]
                oauth_dict['token'] = urllib.parse.quote_plus(oauth_dict['token'])
            except KeyError:
                raise ServiceException(_('Провайдер Oauth не задан или не поддерживается, или не задан token'))

            if provider == Oauth.PROVIDER_ODNOKLASSNIKI:
                oauth_dict['public_key'] = settings.OAUTH_PROVIDERS[provider]['public_key']
                #
                # <signature> = md5(
                #    "application_key={$public_key}format=jsonmethod=users.getCurrentUser" .
                #     md5("{$tokenInfo['access_token']}{$client_secret}")) (php код)
                #
                m = hashlib.md5()
                m.update(("%s%s" % (
                        oauth_dict['token'],
                        settings.OAUTH_PROVIDERS[provider]['client_secret'],
                    )).encode()
                )
                m2 = m.hexdigest()
                m = hashlib.md5()
                m.update((
                    "application_key=%sfields=user.*format=jsonmethod=users.getCurrentUser%s" % (
                        settings.OAUTH_PROVIDERS[provider]['public_key'],
                        m2,
                    )).encode()
                )
                oauth_dict['signature'] = m.hexdigest()

            url = provider_details['url'] % oauth_dict

            try:
                msg_debug = ", url: %s" % url if settings.DEBUG else ""
                r = urllib.request.urlopen(url)
                raw_data = r.read().decode(r.headers.get_content_charset('utf-8'))
            except urllib.error.HTTPError as excpt:
                result['code'] = 401
                raise ServiceException(
                    _('Ошибка в ответе от провайдера %(provider)s, '
                      'код: %(code)s, статус: %(reason)s%(msg_debug)s') % dict(
                        provider=provider,
                        code=excpt.getcode(),
                        reason=excpt.reason,
                        msg_debug=msg_debug
                ))
            except urllib.error.URLError as excpt:
                reason = ": %s" % excpt.reason if excpt.reason else ''
                raise ServiceException(
                    _('Ошибка связи с провайдером%(reason)s%(msg_debug)s') % dict(
                        reason=reason,
                        msg_debug=msg_debug,
            ))

            try:
                data = json.loads(raw_data)
                if provider == Oauth.PROVIDER_VKONTAKTE:
                    data = data['response'][0]
            except (KeyError, ValueError, IndexError,):
                msg_debug = " DEBUG: Request: %s. Response: %s" % (url, raw_data, ) \
                            if settings.DEBUG else ""
                raise ServiceException(
                    _("Ошибка интерпретации ответа от провайдера %(provider)s.%(msg_debug)s") % dict(
                        provider=provider, msg_debug=msg_debug,
                ))
            try:
                uid = data[provider_details['uid']]
            except KeyError:
                result['code'] = 401
                raise ServiceException(_('Не получен (id) от провайдера'))
            if not uid:
                result['code'] = 401
                raise ServiceException(_('Получен пустой (id) от провайдера'))

            result['uid'] = str(uid)
            for key in Oauth.OAUTH_EXTRA_FIELDS:
                real_key = provider_details.get(key)
                if real_key:
                    result[key] = data.get(real_key) or ''
                    if isinstance(result[key], str):
                        result[key] = result[key].strip()
                    if result[key]:
                        if key == 'photo':
                            if provider == Oauth.PROVIDER_YANDEX:
                                if data.get('is_avatar_empty') or \
                                   re.search(provider_details['no_photo_re'], result[key]):
                                    result[key] = ''
                                else:
                                    result[key] = provider_details['photo_template'] % \
                                                        dict(photo_id=result[key])
                            elif provider == Oauth.PROVIDER_VKONTAKTE:
                                if re.search(provider_details['no_photo_re'], result[key]):
                                    result[key] = ''
        except ServiceException as excpt:
            result['message'] = excpt.args[0]
            if result['code'] == 200:
                result['code'] = 400
        return result

class Profile(PhotoModel, GeoPointAddressModel):

    TELEGRAM_KIND_UNKNOWN = 'unknown'
    TELEGRAM_KIND_BOT = 'bot'
    TELEGRAM_KIND_GROUP = 'group'
    TELEGRAM_KIND_CHANNEL = 'channel'
    TELEGRAM_KIND_CHOICES = (
        (TELEGRAM_KIND_UNKNOWN, _("Неизвестно")),
        (TELEGRAM_KIND_BOT, _("Бот")),
        (TELEGRAM_KIND_GROUP, _("Группа")),
        (TELEGRAM_KIND_CHANNEL, _("Канал")),
    )

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid4, editable=False, db_index=True)
    middle_name = models.CharField(_("Отчество"), max_length=255, blank=True, default='')
    is_notified = models.BooleanField(_("Принимает уведомления"), default=True)
    fame = models.PositiveIntegerField(_("Известность"), default=0)
    sum_thanks_count = models.PositiveIntegerField(_("Число благодарностей"), default=0)
    trust_count = models.PositiveIntegerField(_("Число оказанных доверий"), default=0)
    mistrust_count = models.PositiveIntegerField(_("Число утрат доверия"), default=0)
    acq_count = models.PositiveIntegerField(_("Число тех кто с ним (с ней) знаком)"), default=0)
    invite_meet_count = models.PositiveIntegerField(_("Число тех, кого он пригласил)"), default=0)
    did_bot_start = models.BooleanField(_("Стартовал телеграм бот"), default=False)
    pending_tg_username = models.CharField(max_length=32, null=True, unique=True)
    telegram_kind = models.CharField(max_length=7, choices=TELEGRAM_KIND_CHOICES, null=True)
    is_org = models.BooleanField(_("Организация"), default=False)
    ability = models.ForeignKey('contact.Ability', verbose_name=_("Способность"), null=True, on_delete=models.SET_NULL)
    # Для родни:
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, related_name='profile_owner_set')
    gender = models.CharField(_("Пол"), max_length=1, choices=GenderMixin.GENDER_CHOICES, null=True)
    dob = UnclearDateModelField("Дата рождения", null=True, blank=True)

    # Может быть умершим, но дата смерти не задана
    is_dead = models.BooleanField(_("Умер ли?"), default=False)
    dod = UnclearDateModelField("Дата смерти", null=True, blank=True)

    comment = models.TextField(verbose_name=_("Примечание"), null=True)
    offer_answers = models.ManyToManyField('users.OfferAnswer', verbose_name=_("Ответы на опросы/предложения"))
    tgdesc = models.ManyToManyField('users.TgDesc', verbose_name=_("Сообщения с описаниями"))

    did_meet = models.BigIntegerField(_("Принял участие в игре знакомств"), null=True)
    meet_id = models.CharField(_("Ид приглашения в игру знакомств"), max_length=11, unique=True, null=True)
    r_sympa = models.ForeignKey('auth.User', verbose_name=_("Взаимная симпатия к"),
                                on_delete=models.CASCADE, null=True, related_name='profile_r_sympa_set')

    class Meta:
        ordering = ('user__first_name', )
        constraints = (
            models.CheckConstraint(
                condition=Q(pending_tg_username__isnull=True) |
                          Q(pending_tg_username=Lower('pending_tg_username')),
                name='users_profile_pending_tg_username_lower',
            ),
        )

    def __str__(self):
        return self.user.first_name or str(self.pk)

    @property
    def subject_kind(self):
        return self.telegram_kind or ('organization' if self.is_org else 'person')

    @property
    def is_person(self):
        return self.subject_kind == 'person'

    def data_dict(self, request=None, fmt='d3js', thumb={}, short=False):
        user = self.user
        result = dict()
        if request:
            if fmt == '3d-force-graph' and not thumb:
                # Здесь всегда иконки
                thumb = dict(method=PhotoModel.THUMB_METHOD)
            if thumb:
                c_thumb = dict(
                    method = thumb.get('method', PhotoModel.THUMB_METHOD),
                    width = thumb.get('width', PhotoModel.THUMB_WIDTH if fmt == '3d-force-graph' else 64),
                    height = thumb.get('width', PhotoModel.THUMB_HEIGHT if fmt == '3d-force-graph' else 64),
                    put_default_avatar = thumb.get('put_default_avatar', False),
                    default_avatar_in_media = thumb.get('default_avatar_in_media', PhotoModel.DEFAULT_AVATAR_IN_MEDIA),
                    mark_dead = thumb.get('mark_dead', False) and self.is_dead,
                )
                photo=self.choose_thumb(request, **c_thumb)
            else:
                photo = self.choose_photo(request)
        else:
            photo = ''
        if fmt == '3d-force-graph':
            result.update(
                id=user.pk,
                uuid=self.uuid,
                username=user.username,
                first_name=user.first_name,
                photo=photo,
                gender=self.gender,
                is_dead = self.is_dead,
            )
        elif short:
            result.update(
                user_id=user.pk,
                uuid=self.uuid,
                username=user.username,
                first_name=user.first_name,
                trust_count=self.trust_count,
                acq_count=self.acq_count,
                did_meet=self.did_meet,
            )
        else:
            result.update(
                user_id=user.pk,
                uuid=self.uuid,
                username=user.username,
                last_name=user.last_name,
                first_name=user.first_name,
                middle_name=self.middle_name,
                photo=photo,
                is_notified=self.is_notified,
                is_meetgame_admin=self.is_meetgame_admin(),
                is_power = self.is_power(),
                sum_thanks_count=self.sum_thanks_count,
                fame=self.fame,
                mistrust_count=self.mistrust_count,
                invite_meet_count=self.invite_meet_count,
                trust_count=self.trust_count,
                acq_count=self.acq_count,
                is_active=user.is_active,
                latitude=self.latitude,
                longitude=self.longitude,
                address=self.address,
                ability=self.ability and self.ability.text or None,
                gender=self.gender,
                is_org=self.is_org,
                subject_kind=self.subject_kind,
                is_person=self.is_person,
                dob=self.dob and self.dob.str_safe() or None,
                is_dead=self.is_dead or bool(self.dod),
                dod=self.dod and self.dod.str_safe() or None,
                comment=self.comment or '',
                did_meet=self.did_meet,
                pending_tg_username=self.pending_tg_username,
                has_tgdesc=self.tgdesc.exists(),
                has_bank=self.has_bank(),
                r_sympa_username=self.r_sympa.username if self.r_sympa else None,
            )
        return result

    def has_bank(self):
        """
        Имеет ли Реквизиты платежей
        """
        Key = get_model('contact', 'Key')
        KeyType = get_model('contact', 'KeyType')
        return Key.objects.filter(owner=self.user, type__pk=KeyType.BANKING_DETAILS_ID).exists()

    def is_power(self):
        return self.user.groups.filter(pk=settings.GROUP_IDS['power_telegram']).exists()

    def is_meetgame_admin(self):
        return self.user.groups.filter(pk=settings.GROUP_IDS['meetgame_admin']).exists()

    def owner_dict(self, request=None):
        owner = {}
        if self.owner:
            owner.update(
                user_id=self.owner.pk,
                uuid=self.owner.profile.uuid,
                username=self.owner.username,
                first_name=self.owner.first_name,
                is_power=self.owner.profile.is_power(),
            )
        return dict(owner=owner)

    def tg_data(self):
        """
        Найти профиль среди telegtam ouath's, вернуть данные
        """
        return [ oauth.tg_data()
            for oauth in Oauth.objects.filter(user=self.user, provider=Oauth.PROVIDER_TELEGRAM)
        ]

    def data_WAK(self):
        Wish = get_model('contact', 'Wish')
        Ability = get_model('contact', 'Ability')
        Key = get_model('contact', 'Key')
        KeyType = get_model('contact', 'KeyType')
        user = self.user
        wishes = [
            wish.data_dict(
            ) for wish in Wish.objects.filter(owner=user).order_by('insert_timestamp')
        ]
        abilities = [
            ability.data_dict(
            ) for ability in Ability.objects.filter(owner=user).order_by('insert_timestamp')
        ]
        keys = [
            key.data_dict(
            )  for key in Key.objects.filter(owner=user
                    ).exclude(type__pk=KeyType.BANKING_DETAILS_ID).order_by('type__pk', 'pk')
        ]
        return dict(wishes=wishes, abilities=abilities, keys=keys)

    def desc(self):
        return [
            m.message_dict() for m in self.tgdesc.all().order_by('message_id')
        ]

    @transaction.atomic
    def merge(self, profile_from):
        # Проверку на один и тот же профиль производить
        # в вызывающей этот метод функции!
        #
        if self == profile_from:
            return

        CurrentState = get_model('contact', 'CurrentState')
        Journal = get_model('contact', 'Journal')

        Wish = get_model('contact', 'Wish')
        Ability = get_model('contact', 'Ability')
        Key = get_model('contact', 'Key')
        TgMessageJournal = get_model('contact', 'TgMessageJournal')

        user = self.user
        user_from = profile_from.user
        Oauth.objects.filter(user=user_from).update(user=user)

        Journal.objects.filter(user_from=user_from).update(user_from=user)
        Journal.objects.filter(user_from=user, user_to=user).delete()
        Journal.objects.filter(user_to=user_from).update(user_to=user)
        Journal.objects.filter(user_from=user, user_to=user).delete()

        TgMessageJournal.objects.filter(user_from=user_from).update(user_from=user)
        TgMessageJournal.objects.filter(user_to=user_from).update(user_to=user)
        TgMessageJournal.objects.filter(user_to_delivered=user_from).update(user_to_delivered=user)

        for cs in CurrentState.objects.filter(user_from=user_from, user_to__isnull=False):
            try:
                with transaction.atomic():
                    thanks_count = cs.thanks_count
                    user_to = cs.user_to
                    CurrentState.objects.filter(pk=cs.pk).update(user_from=user)
            except IntegrityError:
                CurrentState.objects.filter(pk=cs.pk).delete()
                CurrentState.objects.filter(
                    user_from=user,
                    user_to=user_to
                ).update(thanks_count=F('thanks_count') + thanks_count)
        CurrentState.objects.filter(user_from=user, user_to=user).delete()

        for cs in CurrentState.objects.filter(user_to=user_from):
            try:
                with transaction.atomic():
                    thanks_count = cs.thanks_count
                    user_from_ = cs.user_from
                    CurrentState.objects.filter(pk=cs.pk).update(user_to=user)
            except IntegrityError:
                CurrentState.objects.filter(pk=cs.pk).delete()
                CurrentState.objects.filter(
                    user_from=user_from_,
                    user_to=user
                ).update(thanks_count=F('thanks_count') + thanks_count)
        CurrentState.objects.filter(user_from=user, user_to=user).delete()

        for cs in CurrentState.objects.filter(user_from=user_from, anytext__isnull=False):
            try:
                with transaction.atomic():
                    anytext = cs.anytext
                    thanks_count = cs.thanks_count
                    CurrentState.objects.filter(pk=cs.pk).update(user_from=user)
            except IntegrityError:
                CurrentState.objects.filter(pk=cs.pk).delete()
                CurrentState.objects.filter(
                    user_from=user,
                    anytext=anytext
                ).update(thanks_count=F('thanks_count') + thanks_count)

        Wish.objects.filter(owner=user_from).update(owner=user)

        Ability.objects.filter(owner=user_from).update(owner=user)
        try:
            self.ability = user.ability_set.all().order_by('insert_timestamp')[0]
        except IndexError:
            self.ability = None
        self.save(update_fields=('ability',))

        for key in Key.objects.filter(owner=user_from):
            try:
                with transaction.atomic():
                    Key.objects.filter(pk=key.pk).update(owner=user)
            except IntegrityError:
                Key.objects.filter(pk=key.pk).delete()
        try:
            self_token = Token.objects.get(user=user)
        except Token.DoesNotExist:
            Token.objects.filter(user=user_from).update(user=user)

        Offer.objects.filter(owner=user_from).update(owner=user)
        RentalOffer.objects.filter(owner=user_from).update(owner=user)
        RentalOfferContactRequest.objects.filter(requester=user_from).update(requester=user)
        RentalOfferMessage.objects.filter(recipient=user_from).update(recipient=user)
        RentalReservationIntent.objects.filter(requester=user_from).update(requester=user)

        do_save = False
        if not self.photo and profile_from.photo:
            self.photo = profile_from.photo
            profile_from.photo = ''
            do_save = True
        for f in (
            'photo_original_filename',
            'did_bot_start',
            'address', 'dob', 'dod', 'gender', 'comment', 'is_dead',
           ):
            if not getattr(self, f) and getattr(profile_from, f):
                setattr(self, f, getattr(profile_from, f))
                do_save = True
        for f in ('latitude', 'longitude'):
            if getattr(self, f) is None and getattr(profile_from, f) is not None:
                setattr(self, f, getattr(profile_from, f))
                do_save = True
        if do_save:
            self.save()

        Profile.objects.filter(owner=user_from).update(owner=user)

        profile_from_deleted = False
        if self.owner and not profile_from.owner:

            # Мигрируем not owned user (profile_from, user_from) -> owned user (self, user)
            # - uuid берем от активного (not-owned user)
            # - owned user пестает быть owned
            # -     посему делаем ему Token
            # - у мигрируемого пользователя могут быть owned. Пусть сам удаляет!
            #       TODO: рассмотреть это как опцию

            profile_from_uuid = profile_from.uuid
            profile_from.delete()
            profile_from_deleted = True
            self.uuid = profile_from_uuid
            self.owner = None
            self.save(update_fields=('uuid', 'owner',))
            Token.objects.get_or_create(user=user)
            user.is_active = True
            user.save(update_fields=('is_active',))

        if not profile_from_deleted:
            # Просто user_from.delete() удаляет profile из базы,
            # но не отрабатывект метод Profile.delete()
            profile_from.delete()

        user_from_id = user_from.id
        user_from.delete()

        self.recount_sum_thanks_count()
        self.recount_invite_meet_count()
        self.recount_trust_fame()

    def recount_invite_meet_count(self, do_save=True):
        CurrentState = get_model('contact', 'CurrentState')
        self.invite_meet_count = CurrentState.objects.filter(
            is_invite_meet_reverse=False,
            user_from=self.user,
            user_to__isnull=False,
            is_invite_meet=True,
        ).distinct().count()
        if do_save:
            self.save(update_fields=('invite_meet_count',))

    def recount_sum_thanks_count(self, do_save=True):
        CurrentState = get_model('contact', 'CurrentState')
        user = self.user
        self.sum_thanks_count = CurrentState.objects.filter(
            user_to=user,
        ).distinct().aggregate(Sum('thanks_count'))['thanks_count__sum'] or 0
        if do_save:
            self.save(update_fields=('sum_thanks_count',))

    def recount_trust_fame(self, do_save=True):
        CurrentState = get_model('contact', 'CurrentState')
        user = self.user
        self.trust_count = CurrentState.objects.filter(
            is_reverse=False,
            user_to=user,
            attitude=CurrentState.TRUST,
        ).distinct().count()
        self.mistrust_count = CurrentState.objects.filter(
            is_reverse=False,
            user_to=user,
            attitude=CurrentState.MISTRUST,
        ).distinct().count()
        self.acq_count = CurrentState.objects.filter(
            is_reverse=False,
            user_to=user,
            attitude=CurrentState.ACQ,
        ).distinct().count()
        self.fame = self.trust_count + self.mistrust_count + self.acq_count
        if do_save:
            self.save(update_fields=('fame', 'trust_count', 'mistrust_count', 'acq_count', ))

    @classmethod
    def make_first_name(cls, last_name, first_name, middle_name=''):
        """
        В user.first_name будет и о ф
        """
        if middle_name and not first_name:
            result = (last_name or '').strip()
        else:
            result = " ".join(((first_name or ''), (middle_name or ''), (last_name or ''),)).strip()
        result = re.sub(r'\s{2,}', ' ', result)
        return result or 'Без имени'

    def parents_dict(self, request):
        """
        Вернуть папу, маму и детей из CurrentState
        """
        result = dict(father=None, mother=None, children=[])
        q = Q(user_to__isnull=False) & (Q(is_father=True) | Q(is_mother=True))
        for parent_link in self.user.currentstate_user_from_set.filter(q). \
                           select_related('user_to', 'user_to__profile', 'user_to__profile__ability'). \
                           order_by(F('user_to__profile__dob').asc(nulls_first=True)).distinct():
            human = parent_link.user_to.profile.data_dict(request)
            if parent_link.is_child:
                result['children'].append(human)
            elif parent_link.is_father:
                result['father'] = human
            elif parent_link.is_mother:
                result['mother'] = human
        return result


class TelegramRelationRecheckNotice(BaseModelInsertTimestamp):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    tg_username = models.CharField(max_length=32)
    attempts = models.PositiveIntegerField(default=0)
    delivered_timestamp = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        unique_together = ('user', 'profile')

class CreateUserMixin(object):

    MSG_FAILED_CREATE_USER = 'Не удалось создать пользователя с уникальным именем. Попробуйте еще раз.'

    TG_USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{5,32}$')

    @classmethod
    def normalize_tg_username(cls, username):
        return (username or '').strip().lstrip('@').lower()

    @classmethod
    def validate_tg_username(cls, username):
        username = cls.normalize_tg_username(username)
        return username if cls.TG_USERNAME_RE.fullmatch(username) else ''

    def deliver_relation_recheck_notices(self, user):
        try:
            with transaction.atomic():
                notices = list(TelegramRelationRecheckNotice.objects.select_for_update().filter(
                    user=user,
                    delivered_timestamp=0,
                ).order_by('pk')[:50])
                if not notices:
                    return
                usernames = ', '.join('@' + notice.tg_username for notice in notices)
                message = (
                    'Эти профили теперь подтверждены: %s. Проверьте их и, если нужно, '
                    'создайте отношения заново, отправив имя боту.'
                ) % usernames
                delivered = self.send_to_telegram(message, user=user)
                updates = {'attempts': F('attempts') + 1}
                if delivered:
                    updates['delivered_timestamp'] = int(time.time())
                TelegramRelationRecheckNotice.objects.filter(
                    pk__in=[notice.pk for notice in notices]
                ).update(**updates)
        except Exception:
            logging.exception('Failed to deliver Telegram relation recheck notices')

    def validate_pending_profile(self, profile):
        has_identity = Oauth.objects.filter(user=profile.user).exists()
        has_token = Token.objects.filter(user=profile.user).exists()
        if profile.owner_id or profile.user.is_active or has_identity or has_token:
            raise ServiceException('Нельзя автоматически подтвердить повреждённый ожидающий профиль')

    def reset_pending_relations(self, profile, tg_username):
        CurrentState = get_model('contact', 'CurrentState')
        user_id = profile.user_id
        states = CurrentState.objects.filter(Q(user_from_id=user_id) | Q(user_to_id=user_id))
        related_ids = set(states.values_list('user_from_id', flat=True))
        related_ids.update(states.exclude(user_to_id=None).values_list('user_to_id', flat=True))
        related_ids.update(Profile.objects.filter(r_sympa_id=user_id).values_list('user_id', flat=True))
        if profile.r_sympa_id:
            related_ids.add(profile.r_sympa_id)
        related_ids.discard(user_id)

        recipients = set()
        for related in Profile.objects.filter(user_id__in=related_ids).only('user_id', 'owner_id'):
            recipients.add(related.owner_id or related.user_id)
        for recipient_id in recipients:
            TelegramRelationRecheckNotice.objects.get_or_create(
                user_id=recipient_id,
                profile=profile,
                defaults={'tg_username': tg_username},
            )

        states.delete()
        Profile.objects.filter(r_sympa_id=user_id).update(r_sympa=None)
        if profile.r_sympa_id:
            profile.r_sympa_id = None

        affected_ids = related_ids | {user_id}
        for affected in Profile.objects.filter(user_id__in=affected_ids):
            affected.recount_sum_thanks_count()
            affected.recount_invite_meet_count()
            affected.recount_trust_fame()

    @transaction.atomic
    def reconcile_telegram_identity(
        self, *, uid, username='', last_name='', first_name='', photo='', telegram_kind='person',
    ):
        if telegram_kind not in ('person', Profile.TELEGRAM_KIND_BOT,
                                 Profile.TELEGRAM_KIND_GROUP, Profile.TELEGRAM_KIND_CHANNEL):
            raise ServiceException('Неверный тип субъекта Telegram')
        uid = str(uid)
        username = self.normalize_tg_username(username)
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                # ponytail: global identity lock; shard by UID/alias if Telegram auth throughput grows.
                cursor.execute(
                    'SELECT pg_advisory_xact_lock(hashtext(%s))',
                    ['telegram_identity_reconciliation'],
                )

        oauth = Oauth.objects.select_for_update(of=('self',)).select_related('user', 'user__profile').filter(
            provider=Oauth.PROVIDER_TELEGRAM,
            uid=uid,
        ).first()
        pending = None
        if username:
            pending = Profile.objects.select_for_update().filter(
                pending_tg_username=username,
            ).select_related('user').first()

        identity_created = oauth is None
        if oauth:
            user = oauth.user
            profile = user.profile
            if pending and pending.pk != profile.pk:
                self.validate_pending_profile(pending)
                self.reset_pending_relations(pending, username)
                pending.pending_tg_username = None
                pending.save(update_fields=('pending_tg_username', 'r_sympa'))
        else:
            if pending:
                self.validate_pending_profile(pending)
                profile = pending
                user = profile.user
                self.reset_pending_relations(profile, username)
                profile.pending_tg_username = None
                profile.save(update_fields=('pending_tg_username', 'r_sympa'))
            else:
                user = self.create_user(last_name=last_name, first_name=first_name)
                profile = user.profile
            oauth = Oauth.objects.create(
                provider=Oauth.PROVIDER_TELEGRAM,
                uid=uid,
                user=user,
            )

        if username:
            Oauth.objects.select_for_update().filter(
                provider=Oauth.PROVIDER_TELEGRAM,
                username__iexact=username,
            ).exclude(pk=oauth.pk).update(username='')

        values = {
            'last_name': last_name or '',
            'first_name': first_name or '',
            'username': username,
            'photo': photo or '',
        }
        changed = []
        for field, value in values.items():
            if getattr(oauth, field) != value:
                setattr(oauth, field, value)
                changed.append(field)
        if changed:
            oauth.update_timestamp = int(time.time())
            oauth.save(update_fields=tuple(changed) + ('update_timestamp',))

        stored_kind = None if telegram_kind == 'person' else telegram_kind
        profile_changed = []
        if profile.telegram_kind != stored_kind:
            profile.telegram_kind = stored_kind
            profile_changed.append('telegram_kind')
        is_org = telegram_kind != 'person'
        if profile.is_org != is_org:
            profile.is_org = is_org
            profile_changed.append('is_org')
        if not profile.is_person and profile.did_bot_start:
            profile.did_bot_start = False
            profile_changed.append('did_bot_start')
        if profile_changed:
            profile.save(update_fields=profile_changed)
        if not profile.is_person:
            Token.objects.filter(user=user).delete()
            if user.is_active:
                user.is_active = False
                user.save(update_fields=('is_active',))

        transaction.on_commit(lambda: self.deliver_relation_recheck_notices(user))
        return oauth, user, profile, identity_created

    def create_user(self,
        # Keyword only parameters
        *,
        last_name='',
        first_name='',
        middle_name='',
        email='',
        owner=None,
        dob=None,
        is_dead=False,
        dod=None,
        is_active=True,
        gender=None,
        is_org=False,
        latitude=None,
        longitude=None,
        comment=None,
    ):
        user = None
        random.seed()
        chars = string.ascii_lowercase + string.digits + string.ascii_uppercase
        for i in range(1000):
            with transaction.atomic():
                try:
                    username = ''.join(random.choice(chars) for x in range(10))
                    user = User.objects.create(
                        username=username,
                        last_name='',
                        first_name=Profile.make_first_name(last_name, first_name, middle_name),
                        email=email,
                        is_active=is_active,
                    )
                    break
                except IntegrityError:
                    continue
        if user:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (ValueError, TypeError,):
                latitude = longitude = None
            if dod:
                is_dead = True
            Profile.objects.create(
                user=user,
                middle_name='',
                owner=owner,
                dob=dob,
                is_dead=is_dead,
                dod=dod,
                gender=gender,
                is_org=is_org,
                latitude=latitude,
                longitude=longitude,
                address=GeoPointAddressModel.coordinates_to_address(latitude, longitude),
                comment=comment,
            )
        return user

    def update_oauth(self, oauth, oauth_result):
        changed = False
        for f in Oauth.OAUTH_EXTRA_FIELDS:
            if getattr(oauth, f) != oauth_result[f]:
                setattr(oauth, f, oauth_result[f])
                changed = True
        if changed:
            oauth.update_timestamp = int(time.time())
            oauth.save(update_fields=Oauth.OAUTH_EXTRA_FIELDS + ('update_timestamp',))

        user = oauth.user
        changed = False
        if user.last_name != '':
            user.last_name = ''
            changed = True
        first_name = Profile.make_first_name(oauth_result['last_name'], oauth_result['first_name'])
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        user_fields = ('email',)
        for f in user_fields:
            if oauth_result[f] and getattr(user, f) != oauth_result[f]:
                setattr(user, f, oauth_result[f])
                changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if changed:
            user.save(update_fields=user_fields + ('is_active',))

        if oauth_result['photo'] and oauth.photo != oauth_result['photo']:
            user.profile.put_photo_from_url(oauth_result['photo'])

class IncognitoUser(BaseModelInsertUpdateTimestamp):

    private_key = models.CharField(_("Личный ключ"), max_length=36, unique=True, db_index=True)
    public_key = models.CharField(_("Публичный ключ"), max_length=36, null=True, unique=True, db_index=True)

class TempToken(BaseModelInsertTimestamp):
    """
    Для разного рода временных токенов
    """

    TYPE_INVITE = 1

    type = models.PositiveIntegerField(editable=False, db_index=True)
    ct = models.ForeignKey('contenttypes.ContentType', editable=False, on_delete=models.CASCADE)
    obj_id = models.PositiveIntegerField(editable=False, db_index=True)
    obj = GenericForeignKey(ct_field='ct', fk_field='obj_id')
    token = models.CharField(max_length=40, primary_key=True)
    ttl = models.PositiveIntegerField(editable=False)

    @classmethod
    def create(cls, type_, obj, ttl):
        temptoken = cls(
            type = type_,
            ct=ContentType.objects.get_for_model(obj),
            obj_id=obj.pk,
            token=binascii.hexlify(os.urandom(20)).decode(),
            ttl=ttl,
        )
        return temptoken

    def __str__(self):
        return "%s - %s" % (self.type, self.token, )

class UuidMixin(object):

    MSG_NO_UUID = 'Не задан идентификатор пользователя'

    def check_user_uuid(self, uuid, related=('user', 'ability',), comment=''):
        if not uuid:
            raise ServiceException(comment + self.MSG_NO_UUID)
        try:
            profile = Profile.objects.select_related(*related).get(uuid=uuid)
            user = profile.user
        except ValidationError:
            raise ServiceException('Неверный uuid = %s' % uuid)
        except Profile.DoesNotExist:
            raise ServiceException('Не найден пользователь с uuid = %s' % uuid)
        return user, profile

    def check_user_id(self, id_, related=('user', 'ability',), comment=''):
        if not id_:
            raise ServiceException(comment + self.MSG_NO_UUID)
        try:
            profile = Profile.objects.select_related(*related).get(user__pk=id_)
            user = profile.user
        except Profile.DoesNotExist:
            raise ServiceException('Не найден пользователь с id = %s' % id_)
        return user, profile

    def check_user_username(self, username, related=('user', 'ability',), comment=''):
        if not username:
            raise ServiceException(comment + self.MSG_NO_UUID)
        try:
            profile = Profile.objects.select_related(*related).get(user__username=username)
            user = profile.user
        except Profile.DoesNotExist:
            raise ServiceException('Не найден пользователь с username (sid) = %s' % username)
        return user, profile

    def check_user_or_owned_uuid(
            self, request,
            uuid_field='uuid',
            related=('user', 'ability',),
            need_uuid=False,
        ):
        """
        Кого правим: авторизованного пользователя или заданного по uuid
        """
        uuid = request.data.get(uuid_field)
        if need_uuid and not uuid:
            raise ServiceException(self.MSG_NO_UUID)
        err_message = 'Профиль, uuid = "%s" не подлежит правке Вами' % uuid
        if uuid:
            user, profile = self.check_user_uuid(uuid, related=related)
        else:
            user = request.user
            profile = Profile.objects.select_related(*related).get(user=user)
        if profile.owner:
            if request.user != profile.owner:
                raise ServiceException(err_message)
        else:
            if user != request.user:
                raise ServiceException(err_message)
        return user, profile

    def is_uuid(self, val):
        """
        Это uuid передано?
        """
        try:
            UUID(str(val))
            return True
        except ValueError:
            return False

class TelegramApiMixin(object):

    class KeyboardType(object):
        '''
        Коды "комманд" в кнопках inline keyboard для бота

        Должны быть теми же, что в telegram-bot/common.py/KeyboardType
        '''

        SYMPA_SET = 65
        SYMPA_REVOKE = 66
        SYMPA_HIDE = 67

        # Удалить сообщение из архива
        #
        MESSAGE_DELETE = 77

        # Разделитель данных в call back data
        #
        SEP = '~'

    API_TELEGRAM = 'https://api.telegram.org'
    API_TIMEOUT = 20
    BOT_DATA_CACHE_TTL = 300
    BOT_DATA_FAILURE_TTL = 60
    _bot_data_cache = None
    _bot_data_cache_at = 0

    def __urlopen(self, req):
        timeout = getattr(settings, 'TELEGRAM_API_TIMEOUT', self.API_TIMEOUT)
        proxy_url = getattr(settings, 'TELEGRAM_API_PROXY', None)
        if proxy_url:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({
                'http': proxy_url,
                'https': proxy_url,
            }))
            return opener.open(req, timeout=timeout)
        return urllib.request.urlopen(req, timeout=timeout)


    def __get_tg_ids(self, user=None, telegram_uid=None):
        result = []
        if not settings.SEND_TO_TELEGRAM:
            return
        uids = []
        if user:
            uids = [oauth.uid for oauth in Oauth.objects.filter(user=user, provider=Oauth.PROVIDER_TELEGRAM)]
        elif telegram_uid:
            uids = [telegram_uid]
        return uids

    def __get_url_parms(self, func):
        url = '%s/bot%s/%s' % (self.API_TELEGRAM, settings.TELEGRAM_BOT_TOKEN, func)
        return url

    def __make_request(self, url, parms):
        success = False
        try:
            req = urllib.request.Request(
                url,
                json.dumps(parms).encode(),
                headers={"Content-Type":"application/json"},
                method='POST',
            )
            self.__urlopen(req)
            success = True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        return success


    def send_to_telegram(self, message, user=None, telegram_uid=None, options={}):
        success = False
        uids = self.__get_tg_ids(user, telegram_uid)
        if uids:
            url = self.__get_url_parms('sendMessage')
            options_ = options.copy()
            if not options_.get('parse_mode'):
                options_.update(parse_mode='html')
            options_.update(text=message)
            for uid in uids:
                options_.update(chat_id=uid)
                sent = self.__make_request(url, options_)
                if sent:
                    success = True
        return success

    def copy_to_telegram(self, message_id, from_chat_id, user, options={}):
        success = False
        uids = self.__get_tg_ids(user)
        if uids:
            options_ = options.copy()
            url = self.__get_url_parms('copyMessage')
            options_.update(message_id=message_id, from_chat_id=from_chat_id)
            for uid in uids:
                options_.update(chat_id=uid)
                sent = self.__make_request(url, options_)
                if sent:
                    success = True
        return success

    def send_pack_to_telegram(self, messages, user, options={}):
        success = False
        if not messages:
            return messages
        uids = self.__get_tg_ids(user)
        if uids:
            from_chat_id = messages[0]['chat_id']
            parsed_pack = self.parse_tgmsg_pack(messages)
            for p in parsed_pack:
                if not p:
                    continue
                if len(p) == 1:
                    sent = self.copy_to_telegram(
                        message_id = p[0]['message_id'],
                        from_chat_id = from_chat_id,
                        user=user, options=options,
                    )
                    if sent:
                        success = True
                else:
                    url = self.__get_url_parms('sendMediaGroup')
                    media=[
                            {
                                'type': m['file_type'],
                                'media': m['file_id'],
                                'caption': m['caption'],
                            }
                       for m in p
                    ]
                    options_ = options.copy()
                    options_.update(media=media)
                    for uid in uids:
                        options_.update(chat_id=uid)
                        sent = self.__make_request(url, parms=options_)
                        if sent:
                            success = True
        return success

    def parse_tgmsg_pack(self, messages):
        """
        Раскидать сообщения по пачкам.

        В пачке может быть либо одно сообщение, или несколько, если они в одной
        media_group_id
        """

        n = 0; j = -1
        skip_it = []
        result = []
        l_messages = len(messages)

        while n < l_messages:
            if n not in skip_it:
                item = messages[n]
                j += 1
                result.append([item])
                media_group_id = item['media_group_id']
                if media_group_id and item['file_id'] and item['file_type']:
                    k = n + 1
                    while k < l_messages:
                        checking = messages[k]
                        if checking['media_group_id'] == media_group_id and \
                        checking['file_id'] and checking['file_type']:
                            result[j].append(checking)
                            skip_it.append(k)
                        k += 1
            n += 1

        return result

    def get_bot_data(self):
        """
        Получить данные бота
        """
        now = time.time()
        cached = self.__class__._bot_data_cache
        cached_at = self.__class__._bot_data_cache_at
        ttl = self.BOT_DATA_CACHE_TTL if cached else self.BOT_DATA_FAILURE_TTL
        if cached_at and now - cached_at < ttl:
            return cached

        result = None
        url = '%s/bot%s/getMe' % (self.API_TELEGRAM, settings.TELEGRAM_BOT_TOKEN)
        try:
            req = urllib.request.Request(url)
            r = self.__urlopen(req)
            raw_data = r.read().decode(r.headers.get_content_charset('utf-8'))
            try:
                data = json.loads(raw_data)
                if data['ok'] and data['result']:
                    result = data['result']
            except (KeyError, ValueError):
                pass
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        self.__class__._bot_data_cache = result
        self.__class__._bot_data_cache_at = now
        return result

    def get_bot_username(self):
        """
        Получить имя бота
        """
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', None)
        if bot_username:
            return bot_username
        bot_data = self.get_bot_data()
        if bot_data and bot_data.get('username'):
            return bot_data['username']
        else:
            return None

    def get_deeplink_by_username(self, username, bot_username=None):
        result = ''
        if not bot_username:
            bot_username = self.get_bot_username()
        if bot_username:
            result = 'https://t.me/%s?start=%s' % (bot_username, username)
        return result

    def get_deeplink(self, user, bot_username=None):
        return self.get_deeplink_by_username(user.username, bot_username)

    def get_deeplink_name(self, user, bot_username=None, target_blank=False):
        result = user.first_name
        deeplink = self.get_deeplink(user, bot_username)
        if deeplink:
            if target_blank:
                target = ' target="_blank"'
            else:
                target = ''
            result = '<a href="%(deeplink)s"%(target)s>%(full_name)s</a>' % dict(
                deeplink=deeplink,
                target=target,
                full_name=user.first_name,
            )
        return result

class TgPoll(BaseModelInsertTimestamp):
    """
    Опрос в телеграме
    """

    poll_id = models.BigIntegerField(_("Poll Id"), unique=True, db_index=True)
    question = models.CharField(_("Вопрос"), max_length=2048)
    # Сообщение с опросом и где это сообщение
    message_id = models.BigIntegerField(_("Message Id"))
    chat_id = models.BigIntegerField(_("Chat Id"))

    def data_dict(self):
        result = dict(
            poll_id=self.poll_id,
            question=self.question,
            message_id=self.message_id,
            chat_id=self.chat_id,
        )
        result.update(answers=[
            answer.data_dict() for answer in TgPollAnswer.objects.filter(
                tgpoll=self).order_by('number')
        ])
        return result

class TgPollAnswer(BaseModelInsertTimestamp):
    """
    Ответы на опросы в телеграме
    """
    tgpoll = models.ForeignKey(TgPoll, on_delete=models.CASCADE)
    # 0-й ответ резервируем для тех, кто сбросил свой голос
    number = models.PositiveIntegerField(_("Номер"), default=0)
    answer = models.CharField(_("Ответ"), max_length=255, blank=True, default='')

    class Meta:
        unique_together = ('tgpoll', 'number',)
        ordering = ('tgpoll', 'number',)

    def data_dict(self):
        return dict(
            number=self.number,
            answer=self.answer,
        )

    def __str__(self):
        return '%s: %s' % (self.number, self.answer)

class Offer(BaseModelInsertTimestamp, GeoPointAddressModel):
    """
    Самодельный опрос в телеграме

    Теоретически может быть и не в телеграме, например сделанный в web приложении
    """

    MAX_NUM_ANSWERS = 9

    owner = models.ForeignKey('auth.User', verbose_name=_("Владелец"), on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid4, editable=False, db_index=True)
    question = models.CharField(_("Вопрос"), max_length=2048)
    closed_timestamp = models.PositiveIntegerField(_("Приостановлен"), null=True, default=None)
    is_multi = models.BooleanField(_("Множественный выбор"), default=False)
    tgdesc = models.ManyToManyField('users.TgDesc', verbose_name=_("Сообщения с описаниями"))

    def data_dict(self, request=None, user_ids_only=False):
        result = dict(
            uuid=self.uuid,
            offer_id=self.pk,
            latitude=self.latitude,
            longitude=self.longitude,
            owner=dict(
                first_name=self.owner.first_name,
                uuid=self.owner.profile.uuid,
                user_id=self.owner.pk,
                username=self.owner.username,
            ),
            question=self.question,
            timestamp=self.closed_timestamp if self.closed_timestamp else int(time.time()),
            closed_timestamp=self.closed_timestamp,
            is_multi=self.is_multi,
            desc=self.desc(),
        )
        prefetch = Prefetch('profile_set', queryset=Profile.objects.select_related('user',).all())
        queryset = OfferAnswer.objects.prefetch_related(prefetch).select_related('offer').filter(offer=self)
        answers = []
        user_answered = dict()
        for answer in queryset:
            answer_dict = answer.data_dict()
            users = []
            for profile in answer.profile_set.all():
                user_id = profile.user.pk
                if user_ids_only:
                    users.append(user_id)
                else:
                    users.append(profile.data_dict(request, fmt='3d-force-graph'))
                if user_answered.get(user_id):
                    user_answered[user_id]['answers'].append(answer_dict['number'])
                else:
                    user_answered[user_id] = dict(answers=[answer_dict['number']])
            answer_dict.update(users=users)
            answers.append(answer_dict)
        result.update(answers=answers, user_answered=user_answered)
        return result

    def desc(self):
        return [
            m.message_dict() for m in self.tgdesc.all().order_by('message_id')
        ]


class OfferAnswer(BaseModelInsertTimestamp):
    """
    Ответы на опросы типа offer
    """
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    # 0-й ответ резервируем для тех, кто сбросил свой голос
    number = models.PositiveIntegerField(_("Номер"), default=0)
    answer = models.CharField(_("Ответ"), max_length=255, blank=True, default='')

    class Meta:
        unique_together = ('offer', 'number',)
        ordering = ('offer', 'number',)

    def data_dict(self):
        return dict(
            number=self.number,
            answer=self.answer,
        )

    def __str__(self):
        return '%s: %s' % (self.number, self.answer)

class OfferRefState(BaseModelInsertUpdateTimestamp):
    """
    Кто кого пригласил
    """
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    user_from = models.ForeignKey('auth.User',
                    verbose_name=_("Пригласивший"), on_delete=models.CASCADE,
                    related_name='offerrefstate_user_from_set')
    user_to = models.ForeignKey('auth.User',
                    verbose_name=_("Приглашенный (стал referrer"), on_delete=models.CASCADE,
                    related_name='offerrefstate_user_to_set')

    class Meta:
        unique_together = (
            ('offer', 'user_from', 'user_to', ),
        )

class OfferRefJournal(BaseModelInsertTimestamp):
    """
    Кто кого пригласил когда
    """
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    user_from = models.ForeignKey('auth.User',
                    verbose_name=_("Пригласивший"), on_delete=models.CASCADE,
                    related_name='offerrefjournal_user_from_set')
    user_to = models.ForeignKey('auth.User',
                    verbose_name=_("Приглашенный (стал referrer"), on_delete=models.CASCADE,
                    related_name='offerrefjournal_user_to_set')


class RentalEquipmentType(BaseModelInsertUpdateTimestamp):
    """
    Curated rental equipment taxonomy with multilingual labels/synonyms.
    """

    slug = models.SlugField(_("Slug"), max_length=64, unique=True)
    parent = models.ForeignKey(
        'self',
        verbose_name=_("Родитель"),
        on_delete=models.SET_NULL,
        related_name='children',
        null=True,
        blank=True,
    )
    canonical_name = models.CharField(_("Каноническое название"), max_length=255)
    labels = models.JSONField(_("Названия"), blank=True, default=dict)
    synonyms = models.JSONField(_("Синонимы"), blank=True, default=dict)
    is_ambiguous = models.BooleanField(_("Требует уточнения"), default=False, db_index=True)

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.canonical_name or self.slug

    def terms(self):
        result = set()
        for values in (self.labels or {}).values():
            if isinstance(values, str):
                result.add(values)
            else:
                result.update(values or [])
        for values in (self.synonyms or {}).values():
            if isinstance(values, str):
                result.add(values)
            else:
                result.update(values or [])
        result.add(self.slug.replace('-', ' '))
        result.add(self.canonical_name)
        return [term.strip() for term in result if term and term.strip()]

    def data_dict(self):
        return dict(
            slug=self.slug,
            parent=self.parent.slug if self.parent_id else '',
            canonical_name=self.canonical_name,
            labels=self.labels,
            synonyms=self.synonyms,
            is_ambiguous=self.is_ambiguous,
        )

    @classmethod
    def match_text(cls, text):
        text = (text or '').lower()
        if not text:
            return [], []
        concrete = []
        ambiguous = []
        for equipment_type in cls.objects.select_related('parent').all():
            for term in equipment_type.terms():
                pattern = r'(?<![\w])%s(?![\w])' % re.escape(term.lower())
                if re.search(pattern, text, flags=re.I):
                    if equipment_type.is_ambiguous:
                        ambiguous.append(equipment_type)
                    else:
                        concrete.append(equipment_type)
                    break
        return concrete, ambiguous

    @classmethod
    def clarification_data(cls, ambiguous_types):
        choices = []
        ambiguous_ids = [equipment_type.pk for equipment_type in ambiguous_types]
        qs = cls.objects.filter(is_ambiguous=False)
        if ambiguous_ids:
            qs = qs.filter(parent_id__in=ambiguous_ids)
        for equipment_type in qs.order_by('canonical_name', 'slug')[:8]:
            choices.append(equipment_type.data_dict())
        return dict(
            message='Уточните тип снаряжения',
            ambiguous=[equipment_type.data_dict() for equipment_type in ambiguous_types],
            choices=choices,
        )


class RentalOffer(BaseModelInsertUpdateTimestamp, GeoPointAddressModel):
    """
    Объявление о прокате снаряжения.

    Это не опрос и не использует ответы OfferAnswer.
    """

    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_ARCHIVED = 'archived'

    STATUSES = (
        (STATUS_DRAFT, _("Черновик")),
        (STATUS_ACTIVE, _("Активно")),
        (STATUS_PAUSED, _("Приостановлено")),
        (STATUS_ARCHIVED, _("Архив")),
    )

    VISIBILITY_AUTHENTICATED = 'authenticated'
    VISIBILITY_TRUSTED = 'trusted'
    VISIBILITY_PRIVATE = 'private'

    VISIBILITIES = (
        (VISIBILITY_AUTHENTICATED, _("Пользователи Doverabot")),
        (VISIBILITY_TRUSTED, _("Доверенное окружение")),
        (VISIBILITY_PRIVATE, _("Только по приватной ссылке")),
    )

    owner = models.ForeignKey(
        'auth.User',
        verbose_name=_("Владелец"),
        on_delete=models.CASCADE,
        related_name='rental_offers',
    )
    uuid = models.UUIDField(default=uuid4, editable=False, db_index=True)
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=STATUSES,
        default=STATUS_ACTIVE,
        db_index=True,
    )
    title = models.CharField(_("Название"), max_length=255, blank=True, default='', db_index=True)
    item_text = models.CharField(_("Предмет"), max_length=255, blank=True, default='', db_index=True)
    description_text = models.TextField(verbose_name=_("Описание"), blank=True, default='')
    price_text = models.TextField(verbose_name=_("Цена и платежи"), blank=True, default='')
    price_amount = models.DecimalField(
        _("Цена"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    price_currency = models.CharField(_("Валюта"), max_length=8, blank=True, default='')
    price_period = models.CharField(_("Период цены"), max_length=32, blank=True, default='')
    availability_text = models.TextField(verbose_name=_("Доступность"), blank=True, default='')
    available_from = models.DateField(_("Доступно с"), null=True, blank=True, db_index=True)
    available_to = models.DateField(_("Доступно до"), null=True, blank=True, db_index=True)
    quantity_total = models.PositiveIntegerField(_("Количество одинаковых предметов"), default=1)
    visibility = models.CharField(
        _("Видимость"),
        max_length=20,
        choices=VISIBILITIES,
        default=VISIBILITY_AUTHENTICATED,
        db_index=True,
    )
    tgdesc = models.ManyToManyField(
        'users.TgDesc',
        verbose_name=_("Сообщения с описаниями"),
        blank=True,
    )
    equipment_types = models.ManyToManyField(
        RentalEquipmentType,
        verbose_name=_("Типы снаряжения"),
        blank=True,
        related_name='rental_offers',
    )

    class Meta:
        ordering = ('-insert_timestamp', '-pk')

    def __str__(self):
        return self.title or self.item_text or str(self.uuid)

    def desc(self):
        return [
            m.message_dict() for m in self.tgdesc.all().order_by('message_id')
        ]

    def telegram_messages(self):
        return [
            m.data_dict() for m in self.telegram_messages_set.all().order_by('insert_timestamp', 'pk')
        ]

    def canonical_message(self):
        message = self.telegram_messages_set.filter(
            message_kind=RentalOfferMessage.KIND_OWNER_OFFER,
        ).order_by('insert_timestamp', 'pk').first()
        return message.data_dict() if message else None

    def payment_details_text(self):
        if self.price_text:
            return self.price_text
        Key = get_model('contact', 'Key')
        KeyType = get_model('contact', 'KeyType')
        key = Key.objects.filter(
            owner=self.owner,
            type__pk=KeyType.BANKING_DETAILS_ID,
        ).order_by('pk').first()
        return key.value if key else ''

    def trust_badges(self, viewer_user=None):
        result = dict(
            owner_trust_count=self.owner.profile.trust_count,
            owner_acq_count=self.owner.profile.acq_count,
            owner_fame=self.owner.profile.fame,
            viewer_attitude='',
            owner_attitude='',
        )
        if viewer_user and viewer_user.is_authenticated and viewer_user != self.owner:
            CurrentState = get_model('contact', 'CurrentState')
            viewer_state = CurrentState.objects.filter(
                user_from=viewer_user,
                user_to=self.owner,
                is_reverse=False,
                attitude__isnull=False,
            ).first()
            owner_state = CurrentState.objects.filter(
                user_from=self.owner,
                user_to=viewer_user,
                is_reverse=False,
                attitude__isnull=False,
            ).first()
            result.update(
                viewer_attitude=viewer_state.attitude if viewer_state else '',
                owner_attitude=owner_state.attitude if owner_state else '',
            )
        return result

    def rental_media(self, request=None, viewer_user=None):
        viewer_params = dict(offer_uuid=str(self.uuid))
        if viewer_user and viewer_user.is_authenticated:
            viewer_params['user_uuid'] = str(viewer_user.profile.uuid)

        result = []
        for message in self.tgdesc.all().order_by('message_id', 'pk'):
            if not message.file_id or not message.file_type:
                continue
            item = dict(
                id=message.pk,
                message_id=message.message_id,
                chat_id=message.chat_id,
                media_group_id=message.media_group_id,
                caption=message.caption,
                file_type=message.file_type,
                uuid_pack=str(message.uuid_pack),
                thumbnail_url='',
            )
            if request and message.file_type == 'photo':
                item['thumbnail_url'] = request.build_absolute_uri(
                    '/api/rental/media/%s/thumbnail/?%s' % (
                        message.pk,
                        urlencode(viewer_params),
                    )
                )
            result.append(item)
        return result

    def data_dict(self, request=None, viewer_user=None, include_payment=False):
        result = dict(
            uuid=self.uuid,
            rental_offer_id=self.pk,
            status=self.status,
            title=self.title,
            item_text=self.item_text,
            description_text=self.description_text,
            price_text=self.price_text,
            price_amount=str(self.price_amount) if self.price_amount is not None else '',
            price_currency=self.price_currency,
            price_period=self.price_period,
            availability_text=self.availability_text,
            available_from=self.available_from.isoformat() if self.available_from else '',
            available_to=self.available_to.isoformat() if self.available_to else '',
            quantity_total=self.quantity_total,
            visibility=self.visibility,
            latitude=self.latitude,
            longitude=self.longitude,
            address=self.address,
            insert_timestamp=self.insert_timestamp,
            update_timestamp=self.update_timestamp,
            owner=dict(
                first_name=self.owner.first_name,
                uuid=self.owner.profile.uuid,
                user_id=self.owner.pk,
                username=self.owner.username,
            ),
            desc=self.desc(),
            equipment_types=[
                equipment_type.data_dict()
                for equipment_type in self.equipment_types.all().order_by('slug')
            ],
            telegram_messages=self.telegram_messages(),
            canonical_message=self.canonical_message(),
            media=self.rental_media(request=request, viewer_user=viewer_user),
            trust_badges=self.trust_badges(viewer_user=viewer_user),
        )
        if include_payment:
            result.update(payment_details=self.payment_details_text())
        return result


class RentalOfferMessage(BaseModelInsertTimestamp):
    """
    Telegram message identity for copied/forwarded rental listings and prompts.
    """

    KIND_OWNER_OFFER = 'owner_offer'
    KIND_SEARCH_RESULT = 'search_result'
    KIND_BOOKING_PROMPT = 'booking_prompt'
    KIND_CONTACT_HANDOFF = 'contact_handoff'

    MESSAGE_KINDS = (
        (KIND_OWNER_OFFER, _("Сообщение владельца")),
        (KIND_SEARCH_RESULT, _("Результат поиска")),
        (KIND_BOOKING_PROMPT, _("Подсказка бронирования")),
        (KIND_CONTACT_HANDOFF, _("Передача контакта")),
    )

    offer = models.ForeignKey(
        RentalOffer,
        verbose_name=_("Объявление проката"),
        on_delete=models.CASCADE,
        related_name='telegram_messages_set',
    )
    chat_id = models.BigIntegerField(_("Chat Id"), db_index=True)
    message_id = models.BigIntegerField(_("Message Id"), db_index=True)
    message_kind = models.CharField(
        _("Тип сообщения"),
        max_length=32,
        choices=MESSAGE_KINDS,
        db_index=True,
    )
    recipient = models.ForeignKey(
        'auth.User',
        verbose_name=_("Получатель"),
        on_delete=models.SET_NULL,
        related_name='rental_offer_messages',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ('-insert_timestamp', '-pk')
        unique_together = ('offer', 'chat_id', 'message_id', 'message_kind')

    def data_dict(self):
        return dict(
            id=self.pk,
            offer_uuid=self.offer.uuid,
            chat_id=self.chat_id,
            message_id=self.message_id,
            message_kind=self.message_kind,
            recipient_uuid=self.recipient.profile.uuid if self.recipient_id else '',
            insert_timestamp=self.insert_timestamp,
        )


class RentalReservationIntent(BaseModelInsertUpdateTimestamp):
    """
    Non-escrow reservation/payment handoff intent for a rental offer.
    """

    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_AWAITING_PAYMENT = 'awaiting_payment'
    STATUS_OWNER_ACCEPTED = 'owner_accepted'
    STATUS_PAYMENT_REPORTED = 'payment_reported'
    STATUS_PAYMENT_PROOF_SUBMITTED = 'payment_proof_submitted'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_EXPIRED = 'expired'

    STATUSES = (
        (STATUS_DRAFT, _("Черновик")),
        (STATUS_SENT, _("Отправлено")),
        (STATUS_AWAITING_PAYMENT, _("Ожидает подтверждения оплаты")),
        (STATUS_OWNER_ACCEPTED, _("Принято владельцем")),
        (STATUS_PAYMENT_REPORTED, _("Оплата сообщена")),
        (STATUS_PAYMENT_PROOF_SUBMITTED, _("Подтверждение оплаты отправлено")),
        (STATUS_CONFIRMED, _("Подтверждено")),
        (STATUS_CANCELLED, _("Отменено")),
        (STATUS_EXPIRED, _("Истекло")),
    )

    RECIPIENT_OWNER = 'owner'
    RECIPIENT_SYSTEM = 'system'

    RECIPIENT_KINDS = (
        (RECIPIENT_OWNER, _("Владелец")),
        (RECIPIENT_SYSTEM, _("Система")),
    )

    offer = models.ForeignKey(
        RentalOffer,
        verbose_name=_("Объявление проката"),
        on_delete=models.CASCADE,
        related_name='reservation_intents',
    )
    requester = models.ForeignKey(
        'auth.User',
        verbose_name=_("Запросивший"),
        on_delete=models.CASCADE,
        related_name='rental_reservation_intents',
    )
    source_message = models.ForeignKey(
        RentalOfferMessage,
        verbose_name=_("Сообщение-источник"),
        on_delete=models.SET_NULL,
        related_name='reservation_intents',
        null=True,
        blank=True,
    )
    date_from = models.DateField(_("Дата с"), null=True, blank=True)
    date_to = models.DateField(_("Дата до"), null=True, blank=True)
    amount_suggested = models.DecimalField(
        _("Предложенная сумма"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.CharField(_("Валюта"), max_length=8, blank=True, default='')
    recipient_kind = models.CharField(
        _("Получатель"),
        max_length=16,
        choices=RECIPIENT_KINDS,
        default=RECIPIENT_OWNER,
        db_index=True,
    )
    recipient_payment_info_snapshot = models.TextField(
        verbose_name=_("Снимок реквизитов получателя"),
        blank=True,
        default='',
    )
    sequence_number = models.PositiveIntegerField(
        _("Глобальный номер"),
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    hold_expires_at = models.BigIntegerField(
        _("До какого времени держится бронь"),
        default=0,
        db_index=True,
    )
    status = models.CharField(
        _("Статус"),
        max_length=32,
        choices=STATUSES,
        default=STATUS_SENT,
        db_index=True,
    )

    class Meta:
        ordering = ('-insert_timestamp', '-pk')

    def data_dict(self):
        hold_seconds = 0
        if self.hold_expires_at and self.insert_timestamp:
            hold_seconds = max(0, self.hold_expires_at - self.insert_timestamp)
        return dict(
            id=self.pk,
            offer_uuid=self.offer.uuid,
            requester=dict(
                first_name=self.requester.first_name,
                uuid=self.requester.profile.uuid,
                user_id=self.requester.pk,
                username=self.requester.username,
            ),
            date_from=self.date_from.isoformat() if self.date_from else '',
            date_to=self.date_to.isoformat() if self.date_to else '',
            amount_suggested=str(self.amount_suggested) if self.amount_suggested is not None else '',
            currency=self.currency,
            recipient_kind=self.recipient_kind,
            recipient_payment_info_snapshot=self.recipient_payment_info_snapshot,
            sequence_number=self.sequence_number,
            hold_expires_at=self.hold_expires_at,
            hold_seconds=hold_seconds,
            hold_seconds_remaining=max(0, self.hold_expires_at - int(time.time()))
                if self.hold_expires_at else 0,
            status=self.status,
            insert_timestamp=self.insert_timestamp,
            update_timestamp=self.update_timestamp,
            payment_proof_count=self.payment_proofs.count() if self.pk else 0,
        )


class RentalReservationEvent(BaseModelInsertTimestamp):
    """
    Audited runtime event in the owner-consumer rental concierge flow.
    """

    ROLE_REQUESTER = 'requester'
    ROLE_OWNER = 'owner'
    ROLE_SYSTEM = 'system'

    ACTOR_ROLES = (
        (ROLE_REQUESTER, _("Запросивший")),
        (ROLE_OWNER, _("Владелец")),
        (ROLE_SYSTEM, _("Система")),
    )

    EVENT_CREATED = 'created'
    EVENT_OWNER_ACCEPT = 'owner_accept'
    EVENT_PAYMENT_REPORTED = 'payment_reported'
    EVENT_PAYMENT_PROOF_SUBMITTED = 'payment_proof_submitted'
    EVENT_PAYMENT_PROOF_REJECTED = 'payment_proof_rejected'
    EVENT_OWNER_CONFIRM = 'owner_confirm'
    EVENT_CANCEL = 'cancel'
    EVENT_EXPIRE = 'expire'

    EVENT_TYPES = (
        (EVENT_CREATED, _("Создано")),
        (EVENT_OWNER_ACCEPT, _("Принято владельцем")),
        (EVENT_PAYMENT_REPORTED, _("Оплата сообщена")),
        (EVENT_PAYMENT_PROOF_SUBMITTED, _("Подтверждение оплаты отправлено")),
        (EVENT_PAYMENT_PROOF_REJECTED, _("Подтверждение оплаты отклонено")),
        (EVENT_OWNER_CONFIRM, _("Подтверждено владельцем")),
        (EVENT_CANCEL, _("Отменено")),
        (EVENT_EXPIRE, _("Истекло")),
    )

    reservation = models.ForeignKey(
        RentalReservationIntent,
        verbose_name=_("Заявка на бронь"),
        on_delete=models.CASCADE,
        related_name='events',
    )
    actor = models.ForeignKey(
        'auth.User',
        verbose_name=_("Участник"),
        on_delete=models.SET_NULL,
        related_name='rental_reservation_events',
        null=True,
        blank=True,
    )
    actor_role = models.CharField(
        _("Роль участника"),
        max_length=16,
        choices=ACTOR_ROLES,
        db_index=True,
    )
    event_type = models.CharField(
        _("Тип события"),
        max_length=32,
        choices=EVENT_TYPES,
        db_index=True,
    )
    status_from = models.CharField(_("Статус до"), max_length=32, blank=True, default='')
    status_to = models.CharField(_("Статус после"), max_length=32, blank=True, default='')
    note = models.TextField(verbose_name=_("Комментарий"), blank=True, default='')
    payload = models.JSONField(_("Данные события"), blank=True, default=dict)

    class Meta:
        ordering = ('-insert_timestamp', '-pk')

    def data_dict(self):
        return dict(
            id=self.pk,
            reservation_id=self.reservation_id,
            actor_uuid=self.actor.profile.uuid if self.actor_id else '',
            actor_role=self.actor_role,
            event_type=self.event_type,
            status_from=self.status_from,
            status_to=self.status_to,
            note=self.note,
            payload=self.payload,
            insert_timestamp=self.insert_timestamp,
        )


class RentalReservationPaymentProof(BaseModelInsertTimestamp):
    """
    Saved Telegram media/text pack submitted as reservation payment proof.
    """

    reservation = models.ForeignKey(
        RentalReservationIntent,
        verbose_name=_("Заявка на бронь"),
        on_delete=models.CASCADE,
        related_name='payment_proofs',
    )
    sender = models.ForeignKey(
        'auth.User',
        verbose_name=_("Отправитель"),
        on_delete=models.SET_NULL,
        related_name='rental_payment_proofs',
        null=True,
        blank=True,
    )
    uuid_pack = models.CharField(_("UUID пачки"), max_length=64, db_index=True)
    recipient_kind = models.CharField(
        _("Получатель"),
        max_length=16,
        choices=RentalReservationIntent.RECIPIENT_KINDS,
        default=RentalReservationIntent.RECIPIENT_OWNER,
        db_index=True,
    )
    tgdesc = models.ManyToManyField(
        'users.TgDesc',
        verbose_name=_("Сообщения подтверждения"),
        blank=True,
    )

    class Meta:
        ordering = ('-insert_timestamp', '-pk')
        unique_together = ('reservation', 'uuid_pack')

    def data_dict(self):
        return dict(
            id=self.pk,
            reservation_id=self.reservation_id,
            sender_uuid=self.sender.profile.uuid if self.sender_id else '',
            uuid_pack=self.uuid_pack,
            recipient_kind=self.recipient_kind,
            messages=[
                m.message_dict() for m in self.tgdesc.all().order_by('message_id')
            ],
            insert_timestamp=self.insert_timestamp,
        )


class RentalOfferContactRequest(BaseModelInsertTimestamp):
    """
    Запрос контакта по объявлению проката.

    V1 хранит только факт и текст обращения, без брони и резервирования.
    """

    requester = models.ForeignKey(
        'auth.User',
        verbose_name=_("Запросивший"),
        on_delete=models.CASCADE,
        related_name='rental_contact_requests',
    )
    offer = models.ForeignKey(
        RentalOffer,
        verbose_name=_("Объявление проката"),
        on_delete=models.CASCADE,
        related_name='contact_requests',
    )
    message = models.TextField(verbose_name=_("Сообщение"), blank=True, default='')
    transcript = models.TextField(verbose_name=_("Распознанный текст"), blank=True, default='')

    class Meta:
        ordering = ('-insert_timestamp', '-pk')

    def data_dict(self):
        return dict(
            id=self.pk,
            offer_uuid=self.offer.uuid,
            requester=dict(
                first_name=self.requester.first_name,
                uuid=self.requester.profile.uuid,
                user_id=self.requester.pk,
                username=self.requester.username,
            ),
            message=self.message,
            transcript=self.transcript,
            insert_timestamp=self.insert_timestamp,
        )


class TgDesc(BaseModelInsertTimestamp):
    """
    Для описаний: персоны или оффера

    Здесь сообщения телеграма, в которых картинки, видео и т.п.
    Или просто текст.
    """

    message_id = models.BigIntegerField(_("Message Id"))
    chat_id = models.BigIntegerField(_("Chat Id"))
    media_group_id = models.CharField(_("media_group_id"), max_length=255, blank=True, default='')
    caption = models.TextField(verbose_name=_("Заголовок"), default='')
    file_id = models.CharField(_("file_id"), max_length=255, blank=True, default='')
    file_type = models.CharField(_("Тип медиа"), max_length=30, blank=True, default='')
    # Сообщения из одной пачки будут иметь один uuid
    uuid_pack = models.UUIDField(default=uuid4, editable=False, db_index=True)

    def message_dict(self):
        return dict(
            chat_id=self.chat_id,
            message_id=self.message_id,
            media_group_id = self.media_group_id,
            caption = self.caption,
            file_id = self.file_id,
            file_type = self.file_type,
        )


class VpnServerRunway(BaseModelInsertUpdateTimestamp):
    """
    Current prepaid VPN server renewal facts.

    This slice is intentionally scoped to the existing/current server. Payment
    dates and amounts are entered through admin/config, not hard-coded here.
    """

    label = models.CharField(_("Сервер"), max_length=128, default='current', db_index=True)
    prepaid_until = models.DateField(_("Оплачен до"), null=True, blank=True, db_index=True)
    upcoming_payment_amount = models.DecimalField(
        _("Следующий платеж"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.CharField(_("Валюта"), max_length=8, default='RUB')
    active = models.BooleanField(_("Текущий"), default=True, db_index=True)
    notes = models.TextField(verbose_name=_("Заметки"), blank=True, default='')

    class Meta:
        ordering = ('-active', '-pk')

    def __str__(self):
        return self.label

    @classmethod
    def current(cls):
        return cls.objects.filter(active=True).order_by('-pk').first()

    def days_left(self, today=None):
        if not self.prepaid_until:
            return None
        today = today or datetime.date.today()
        return (self.prepaid_until - today).days

    def data_dict(self, today=None):
        return dict(
            label=self.label,
            prepaid_until=self.prepaid_until.isoformat() if self.prepaid_until else '',
            days_left=self.days_left(today=today),
            upcoming_payment_amount=str(self.upcoming_payment_amount)
                if self.upcoming_payment_amount is not None else '',
            currency=self.currency,
            active=self.active,
        )


class VpnProfile(BaseModelInsertUpdateTimestamp):
    """
    Personal Xray access profile for the current server.
    """

    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_DISABLED = 'disabled'

    STATUSES = (
        (STATUS_ACTIVE, _("Активен")),
        (STATUS_PAUSED, _("Пауза")),
        (STATUS_DISABLED, _("Отключен")),
    )

    FRESH_OK = 'ok'
    FRESH_MISSING_CONFIG = 'missing_config'

    FRESH_STATUSES = (
        (FRESH_OK, _("Обновлен")),
        (FRESH_MISSING_CONFIG, _("Нет конфигурации")),
    )

    user = models.OneToOneField(
        'auth.User',
        verbose_name=_("Пользователь"),
        on_delete=models.CASCADE,
        related_name='vpn_profile',
    )
    label = models.CharField(_("Метка Xray"), max_length=128, unique=True, db_index=True)
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=STATUSES,
        default=STATUS_ACTIVE,
        db_index=True,
    )
    subscription_token = models.CharField(
        _("Токен подписки"),
        max_length=64,
        unique=True,
        db_index=True,
    )
    token_expires_at = models.BigIntegerField(_("Токен истекает"), default=0, db_index=True)
    config_uri = models.TextField(verbose_name=_("URI конфигурации"), blank=True, default='')
    artifact_label = models.CharField(
        _("Метка артефакта"),
        max_length=160,
        blank=True,
        default='',
        db_index=True,
    )
    last_refreshed_at = models.BigIntegerField(_("Последнее обновление"), default=0)
    last_fresh_status = models.CharField(
        _("Статус обновления"),
        max_length=32,
        choices=FRESH_STATUSES,
        default=FRESH_OK,
    )
    last_fresh_error = models.TextField(verbose_name=_("Ошибка обновления"), blank=True, default='')

    class Meta:
        ordering = ('user__first_name', 'user__username')

    def __str__(self):
        return self.label

    def default_label(self):
        username = re.sub(r'[^a-zA-Z0-9_\-]+', '-', self.user.username or '').strip('-')
        if not username:
            username = 'user'
        username = username[:48]
        return 'dovera-%s-%s' % (self.user_id, username)

    @classmethod
    def make_token(cls):
        return binascii.hexlify(os.urandom(24)).decode('ascii')

    def make_unique_token(self):
        for i in range(1000):
            token = self.make_token()
            qs = VpnProfile.objects.filter(subscription_token=token)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if not qs.exists():
                return token
        raise ServiceException('Не удалось создать уникальный VPN token')

    @classmethod
    def token_ttl(cls):
        try:
            return int(getattr(settings, 'VPN_PROFILE_TOKEN_TTL', 7 * 86400))
        except (TypeError, ValueError):
            return 7 * 86400

    def template_context(self):
        return dict(
            token=self.subscription_token,
            label=self.label,
            user_id=self.user_id,
            username=self.user.username,
            profile_uuid=str(self.user.profile.uuid),
        )

    def format_template(self, template):
        try:
            return template % self.template_context()
        except (KeyError, TypeError, ValueError):
            return ''

    def save(self, *args, **kwargs):
        if not self.label and self.user_id:
            self.label = self.default_label()
        if not self.subscription_token:
            self.subscription_token = self.make_unique_token()
        return super(VpnProfile, self).save(*args, **kwargs)

    def refresh_access(self, config_uri=None):
        """
        Rotate the weekly subscription token and refresh config from admin/config.

        Returns False and records a structured status if no current-server config
        source exists. It never suggests provisioning another server.
        """
        if not self.pk:
            self.save()
        now = int(time.time())
        self.subscription_token = self.make_unique_token()
        self.token_expires_at = now + self.token_ttl()

        if config_uri is not None:
            self.config_uri = str(config_uri).strip()
        elif getattr(settings, 'VPN_DEFAULT_CONFIG_URI_TEMPLATE', ''):
            self.config_uri = self.format_template(settings.VPN_DEFAULT_CONFIG_URI_TEMPLATE)

        self.last_refreshed_at = now
        self.artifact_label = '%s-%s' % (self.label, now)
        if self.config_uri:
            self.last_fresh_status = self.FRESH_OK
            self.last_fresh_error = ''
        else:
            self.last_fresh_status = self.FRESH_MISSING_CONFIG
            self.last_fresh_error = 'VPN current-server config URI is not configured'
        self.save()
        return self.last_fresh_status == self.FRESH_OK

    def subscription_url(self, request=None):
        template = getattr(settings, 'VPN_SUBSCRIPTION_URL_TEMPLATE', '')
        if template:
            return self.format_template(template)
        path = '/api/vpn/subscription/%s/' % self.subscription_token
        return request.build_absolute_uri(path) if request else path

    @classmethod
    def active_for_token(cls, token):
        if not token:
            return None
        return cls.objects.filter(
            subscription_token=token,
            status=cls.STATUS_ACTIVE,
            token_expires_at__gte=int(time.time()),
        ).first()

    def data_dict(self, request=None, include_secret=False):
        data = dict(
            id=self.pk,
            user_uuid=str(self.user.profile.uuid),
            label=self.label,
            status=self.status,
            subscription_url=self.subscription_url(request=request),
            token_expires_at=self.token_expires_at,
            artifact_label=self.artifact_label,
            last_refreshed_at=self.last_refreshed_at,
            last_fresh_status=self.last_fresh_status,
        )
        if include_secret:
            data.update(config_uri=self.config_uri)
        return data


class VpnTrafficPeriod(BaseModelInsertUpdateTimestamp):
    """
    Stored per-profile weekly/monthly traffic counters.
    """

    KIND_WEEK = 'week'
    KIND_MONTH = 'month'

    PERIOD_KINDS = (
        (KIND_WEEK, _("Неделя")),
        (KIND_MONTH, _("Месяц")),
    )

    profile = models.ForeignKey(
        VpnProfile,
        verbose_name=_("VPN профиль"),
        on_delete=models.CASCADE,
        related_name='traffic_periods',
    )
    period_kind = models.CharField(_("Период"), max_length=16, choices=PERIOD_KINDS, db_index=True)
    period_start = models.DateField(_("Начало периода"), db_index=True)
    uplink_bytes = models.BigIntegerField(_("Отправлено байт"), default=0)
    downlink_bytes = models.BigIntegerField(_("Получено байт"), default=0)

    class Meta:
        ordering = ('-period_start', 'profile__label')
        unique_together = ('profile', 'period_kind', 'period_start')

    def total_bytes(self):
        return (self.uplink_bytes or 0) + (self.downlink_bytes or 0)

    @staticmethod
    def week_start(date_value):
        return date_value - datetime.timedelta(days=date_value.weekday())

    @staticmethod
    def month_start(date_value):
        return date_value.replace(day=1)

    @classmethod
    def current_start(cls, period_kind, today=None):
        today = today or datetime.date.today()
        if period_kind == cls.KIND_WEEK:
            return cls.week_start(today)
        return cls.month_start(today)

    @classmethod
    def add_delta(cls, profile, captured_date, uplink_delta, downlink_delta):
        for period_kind, period_start in (
            (cls.KIND_WEEK, cls.week_start(captured_date)),
            (cls.KIND_MONTH, cls.month_start(captured_date)),
        ):
            period, created = cls.objects.get_or_create(
                profile=profile,
                period_kind=period_kind,
                period_start=period_start,
                defaults=dict(uplink_bytes=0, downlink_bytes=0),
            )
            period.uplink_bytes += max(0, int(uplink_delta or 0))
            period.downlink_bytes += max(0, int(downlink_delta or 0))
            period.save()

    def data_dict(self):
        return dict(
            period_kind=self.period_kind,
            period_start=self.period_start.isoformat(),
            uplink_bytes=self.uplink_bytes,
            downlink_bytes=self.downlink_bytes,
            total_bytes=self.total_bytes(),
        )


class VpnStatsSnapshot(BaseModelInsertTimestamp):
    """
    Sanitized imported Xray stats snapshot.

    Raw configs and opaque inbound JSON are intentionally not persisted.
    """

    profile = models.ForeignKey(
        VpnProfile,
        verbose_name=_("VPN профиль"),
        on_delete=models.CASCADE,
        related_name='stats_snapshots',
    )
    captured_at = models.BigIntegerField(_("Когда снят счетчик"), db_index=True)
    source = models.CharField(_("Источник"), max_length=64, default='xray', db_index=True)
    source_label = models.CharField(_("Метка источника"), max_length=128, db_index=True)
    uplink_bytes = models.BigIntegerField(_("Отправлено байт"), default=0)
    downlink_bytes = models.BigIntegerField(_("Получено байт"), default=0)

    class Meta:
        ordering = ('-captured_at', '-pk')

    def total_bytes(self):
        return (self.uplink_bytes or 0) + (self.downlink_bytes or 0)

    @classmethod
    def _stats_items(cls, payload):
        if isinstance(payload, dict) and isinstance(payload.get('stats'), list):
            return payload['stats']
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return [
                dict(label=label, **value)
                for label, value in payload.items()
                if isinstance(value, dict)
            ]
        return []

    @classmethod
    def normalize_xray_counters(cls, payload):
        counters = {}

        def add(label, direction, value):
            label = str(label or '').strip()
            direction = str(direction or '').strip().lower()
            if not label or direction not in ('uplink', 'downlink'):
                return
            try:
                value = int(value or 0)
            except (TypeError, ValueError):
                return
            counters.setdefault(label, dict(uplink=0, downlink=0))
            counters[label][direction] += max(0, value)

        for item in cls._stats_items(payload):
            if not isinstance(item, dict):
                continue
            label = item.get('source_label') or item.get('label') or item.get('email')
            direction = item.get('direction')
            name = item.get('name')
            if name and '>>>' in str(name):
                parts = str(name).split('>>>')
                if len(parts) >= 2:
                    label = parts[1]
                if parts[-1] in ('uplink', 'downlink'):
                    direction = parts[-1]
            if 'uplink' in item or 'downlink' in item:
                add(label, 'uplink', item.get('uplink'))
                add(label, 'downlink', item.get('downlink'))
            else:
                add(label, direction, item.get('value', item.get('bytes')))
        return counters

    @classmethod
    @transaction.atomic
    def import_xray_counters(cls, payload, captured_at=None, source='xray'):
        captured_at = int(captured_at or time.time())
        captured_date = datetime.datetime.fromtimestamp(captured_at).date()
        counters = cls.normalize_xray_counters(payload)
        imported = 0
        skipped_labels = []
        for label, values in counters.items():
            profile = VpnProfile.objects.filter(label=label).first()
            if not profile:
                skipped_labels.append(label)
                continue
            previous = cls.objects.filter(
                profile=profile,
                captured_at__lt=captured_at,
            ).order_by('-captured_at', '-pk').first()
            snapshot = cls.objects.create(
                profile=profile,
                captured_at=captured_at,
                source=source,
                source_label=label,
                uplink_bytes=values.get('uplink', 0),
                downlink_bytes=values.get('downlink', 0),
            )
            imported += 1
            if previous:
                uplink_delta = snapshot.uplink_bytes - previous.uplink_bytes
                downlink_delta = snapshot.downlink_bytes - previous.downlink_bytes
                VpnTrafficPeriod.add_delta(
                    profile=profile,
                    captured_date=captured_date,
                    uplink_delta=uplink_delta,
                    downlink_delta=downlink_delta,
                )
        return dict(
            imported=imported,
            skipped_labels=skipped_labels,
        )

    def data_dict(self):
        return dict(
            profile_label=self.profile.label,
            captured_at=self.captured_at,
            source=self.source,
            source_label=self.source_label,
            uplink_bytes=self.uplink_bytes,
            downlink_bytes=self.downlink_bytes,
            total_bytes=self.total_bytes(),
        )


class VpnDonorPreference(BaseModelInsertUpdateTimestamp):
    user = models.OneToOneField(
        'auth.User',
        verbose_name=_("Пользователь"),
        on_delete=models.CASCADE,
        related_name='vpn_donor_preference',
    )
    is_visible = models.BooleanField(_("Показывать в благодарностях"), default=False)
    public_name = models.CharField(_("Публичное имя"), max_length=80, blank=True, default='')

    class Meta:
        ordering = ('user__first_name', 'user__username')

    def __str__(self):
        return self.display_name()

    def display_name(self):
        return self.public_name or self.user.first_name or self.user.username or str(self.user_id)


class VpnRunwayLedgerEntry(BaseModelInsertTimestamp):
    ENTRY_DONATION = 'donation'
    ENTRY_REFERRAL_CREDIT = 'referral_credit'
    ENTRY_PAYMENT = 'payment'
    ENTRY_ADJUSTMENT = 'adjustment'

    ENTRY_TYPES = (
        (ENTRY_DONATION, _("Донат")),
        (ENTRY_REFERRAL_CREDIT, _("Реферальный кредит")),
        (ENTRY_PAYMENT, _("Оплата сервера")),
        (ENTRY_ADJUSTMENT, _("Корректировка")),
    )

    entry_type = models.CharField(_("Тип"), max_length=32, choices=ENTRY_TYPES, db_index=True)
    user = models.ForeignKey(
        'auth.User',
        verbose_name=_("Пользователь"),
        on_delete=models.SET_NULL,
        related_name='vpn_ledger_entries',
        null=True,
        blank=True,
    )
    amount = models.DecimalField(_("Сумма"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Валюта"), max_length=8, default='RUB')
    received_at = models.DateField(_("Дата"), default=datetime.date.today, db_index=True)
    is_confirmed = models.BooleanField(_("Подтверждено"), default=True, db_index=True)
    note = models.TextField(verbose_name=_("Заметка"), blank=True, default='')

    class Meta:
        ordering = ('-received_at', '-pk')

    def __str__(self):
        return '%s %s %s' % (self.entry_type, self.amount, self.currency)

    @classmethod
    def latest_payment_date(cls):
        payment = cls.objects.filter(
            entry_type=cls.ENTRY_PAYMENT,
            is_confirmed=True,
        ).order_by('-received_at', '-pk').first()
        return payment.received_at if payment else None

    @classmethod
    def project_income_since_latest_payment(cls):
        qs = cls.objects.filter(
            entry_type__in=(cls.ENTRY_DONATION, cls.ENTRY_REFERRAL_CREDIT),
            is_confirmed=True,
        )
        payment_date = cls.latest_payment_date()
        if payment_date:
            qs = qs.filter(received_at__gt=payment_date)
        total = qs.aggregate(total=Sum('amount'))['total']
        return total or Decimal('0')

    @classmethod
    def donations_since_latest_payment(cls):
        qs = cls.objects.filter(
            entry_type=cls.ENTRY_DONATION,
            is_confirmed=True,
        )
        payment_date = cls.latest_payment_date()
        if payment_date:
            qs = qs.filter(received_at__gt=payment_date)
        total = qs.aggregate(total=Sum('amount'))['total']
        return total or Decimal('0')

    def data_dict(self):
        return dict(
            entry_type=self.entry_type,
            amount=str(self.amount),
            currency=self.currency,
            received_at=self.received_at.isoformat(),
            is_confirmed=self.is_confirmed,
            user_uuid=str(self.user.profile.uuid) if self.user_id else '',
        )


class VpnFeedbackTicket(BaseModelInsertTimestamp):
    REASON_CONFIG_FAILED = 'config_failed'
    REASON_STILL_BROKEN = 'still_broken'

    REASONS = (
        (REASON_CONFIG_FAILED, _("Не удалось выдать конфигурацию")),
        (REASON_STILL_BROKEN, _("Свежая конфигурация не помогла")),
    )

    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'

    STATUSES = (
        (STATUS_OPEN, _("Открыто")),
        (STATUS_CLOSED, _("Закрыто")),
    )

    user = models.ForeignKey(
        'auth.User',
        verbose_name=_("Пользователь"),
        on_delete=models.CASCADE,
        related_name='vpn_feedback_tickets',
    )
    profile = models.ForeignKey(
        VpnProfile,
        verbose_name=_("VPN профиль"),
        on_delete=models.SET_NULL,
        related_name='feedback_tickets',
        null=True,
        blank=True,
    )
    reason = models.CharField(_("Причина"), max_length=32, choices=REASONS, db_index=True)
    artifact_label = models.CharField(_("Метка артефакта"), max_length=160, db_index=True)
    message = models.TextField(verbose_name=_("Сообщение"), blank=True, default='')
    status = models.CharField(_("Статус"), max_length=16, choices=STATUSES, default=STATUS_OPEN, db_index=True)

    class Meta:
        ordering = ('-insert_timestamp', '-pk')

    def data_dict(self):
        return dict(
            id=self.pk,
            reason=self.reason,
            artifact_label=self.artifact_label,
            status=self.status,
            insert_timestamp=self.insert_timestamp,
        )


class ApiDonateUser(object):

    def find_donate_to_user(self, user_from, user_to):
        """
        Найти, кому донатить юзеру user_from

        Вообще-то, надо донатить user_to,
        но у того может не быть банковского счета или user_from == user_to
        """
        donate_him = None; result = None; is_author = False
        Key = get_model('contact', 'Key')
        KeyType = get_model('contact', 'KeyType')
        if user_from != user_to:
            try:
                bank = Key.objects.filter(
                    owner=user_to, type__pk=KeyType.BANKING_DETAILS_ID
                )[0]
                donate_him = user_to
            except IndexError:
                pass
        if not donate_him:
            try:
                is_author = User.objects.filter(pk=settings.AUTHOR_USER_ID)[0]
                bank = Key.objects.filter(
                    owner=is_author, type__pk=KeyType.BANKING_DETAILS_ID,
                )[0]
                donate_him = is_author
                is_author = True
            except IndexError:
                pass
        if donate_him:
            result = dict(
                bank=bank.value,
                profile=donate_him.profile.data_dict(),
                tg_data=donate_him.profile.tg_data(),
                is_author=is_author,
            )
        return result
