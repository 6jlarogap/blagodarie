import time, datetime, re, os, shutil
import pytils, base64
import urllib.request, urllib.error

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.apps import apps
get_model = apps.get_model
from django.core.files.base import ContentFile
from django.templatetags.static import static

from app.utils import ServiceException

from restthumbnails.files import ThumbnailContentFile

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

from django.conf import settings

class UnclearDate:

    SAFE_STR_REGEX = r'^(\d{4})(?:\-(\d{2}))?(?:\-(\d{2}))?$'

    VALUE_ERROR_CREATE = 'Invalid data to make an UnclearDate object'

    def __init__(self, year, month=None, day=None):
        self.d = datetime.date(year, month or 1, day or 1)
        self.no_day = not day
        self.no_month = not month

    def strftime(self, format):
        if self.no_day:
            # Убираем день с возможными разделителями (.-/) слева или справа
            format = re.sub(r'\.\%d|\%d\.|\-\%d|\%d\-|\/\%d|\%d\/', '', format)
            # Убираем день, если формат был без разделителей
            format = re.sub(r'\%d', '', format)
        if self.no_month:
            # Убираем месяц с возможными разделителями (.-/) слева или справа
            format = re.sub(r'\.\%m|\%m\.|\-\%m|\%m\-|\/\%m|\%m\/', '', format)
            # Убираем месяц, если формат был без разделителей
            format = re.sub(r'\%m', '', format)

        if self.d.year < 1900:
            # Есть проблема в datetime.strftime() с годами раньше 1900 (ValueError exception)
            # кроме того:
            #   1600, 1200, ...: в феврале 29 дней (как в 2000)
            #   1800, 1700, 1500, ...: в феврале 28 дней (как в 1900)
            d_base = 1900 if self.d.year % 400 else 2000
            d1 = datetime.date(d_base + self.d.year % 100, self.d.month, self.d.day)
            return d1.strftime(format).replace(str(d1.year), str(self.d.year).rjust(4, '0'))
        return self.d.strftime(format)

    def get_datetime(self):
        return self.d

    def __repr__(self):
        return '<UnclearDate: %s>' % self.strftime('%d.%m.%Y')

    def __str__(self):
        return self.strftime('%d.%m.%Y')

    def str_safe(self, format='d.m.y'):
        """
        YYYY or YYYY-MM or YYYY-MM-DD

        Возможен возврат ДД.ММ.ГГГГ, ММ.ГГГГ, ГГГГ при формате 'd.m'y'
        """
        result = "%04d" % self.d.year
        if format == 'd.m.y':
            if not self.no_month:
                result = '%02d.%s' % (self.d.month, result)
            if not self.no_day:
                result = '%02d.%s' % (self.d.day, result)
        else:
            if not self.no_month:
                result += '-%02d' % self.d.month
            if not self.no_day:
                result += '-%02d' % self.d.day
        return result

    @classmethod
    def str_safe_from_rec(cls, rec, date, format='d.m.y'):
        """
        Сделать yyyy-mm-dd, yyyy-mm, yyyy или None из словря rec, поля date

        Применяется при получении сырых данных, в которых есть
        rec['date'], а также rec['date_no_day'], rec['date_no_month']
        """
        result = None
        if rec[date]:
            ymd = rec[date].strftime("%Y-%m-%d")
            if format == 'd.m.y':
                result = ymd[0:4]
                if not rec[date + '_no_month']:
                    result = ymd[5:2] + result + "."
                if not rec[date + '_no_day']:
                    result = ymd[8:2] + result + "."
            else:
                result = ymd
                if rec[date + '_no_day']:
                    result = result[0:-3]
                    if rec[date + '_no_month']:
                        result = result[0:-3]
        return result

    @classmethod
    def from_str_safe(cls, s, format='d.m.y'):
        """
        Сделать UnclearDate из yyyy-mm-dd, yyyy-mm, yyyy, или из None ('null')

        Возможные форматы:
            'd.m.y': например, 11.12.1912 12.1912, 1912
            'd M y': например, 11 Dec 1912, Dec 1912, 1912
            иначе полагается формат 1912-12-11
        При неверном формате возвращает None
        """
        if s:
            s = s.strip()
        if not s or s.lower() == 'null':
            return None
        try:
            if format == 'd.m.y':
                year, month, day = cls.from_str_dmy(s)
            elif format == 'd M y':
                year, month, day = cls.from_str_dMONy(s)
            else:
                m = re.search(cls.SAFE_STR_REGEX, s)
                if not m:
                    raise ValueError(cls.VALUE_ERROR_CREATE)
                day = m.group(3)
                month = m.group(2)
                year = m.group(1)
            return cls(
                int(year),
                month and int(month) or None,
                day and int(day) or None,
            )
        except (ValueError, ServiceException):
            return None

    @property
    def month(self):
        return self.d.month

    @property
    def year(self):
        return self.d.year

    @property
    def day(self):
        return self.d.day

    def prepare_compare(self, other):
        """
        Подготовить даты к сравнению

        Возвращает строки обеих дат
        1999 и 7.7.1999 дожны стать обе '1999-07-07'
        """
        if isinstance(other, datetime.date):
            other = UnclearDate(other.year, other.month, other.day)

        if not self.no_month and not other.no_month:
            self_month = self.month
            other_month = other.month
        elif not self.no_month and other.no_month:
            other_month = self_month = self.month
        elif self.no_month and not other.no_month:
            self_month = other_month = other.month
        elif self.no_month and other.no_month:
            self_month = other_month = 0

        if not self.no_day and not other.no_day:
            self_day = self.day
            other_day = other.day
        elif not self.no_day and other.no_day:
            other_day = self_day = self.day
        elif self.no_day and not other.no_day:
            self_day = other_day = other.day
        elif self.no_day and other.no_day:
            self_day = other_day = 0

        fmt = "%04d-%02d-%02d"
        self_date = fmt % (self.year, self_month, self_day)
        other_date = fmt % (other.year, other_month, other_day)
        return (self_date , other_date, )

    # Было бы удобнее воспользоваться __cmp__(), но
    # нам эти даты надо сравнивать на больше или меньше,
    # а сравнивать на равенство 07.07.1999 и 1999?
    # Пока такой потребности не было.
    # Кроме того, cmp() is deprecated в python 3

    def __lt__(self, other):
        self_date, other_date = self.prepare_compare(other)
        return self_date < other_date

    def __gt__(self, other):
        self_date, other_date = self.prepare_compare(other)
        return self_date > other_date

    @classmethod
    def from_str_dMONy(cls, s):
        """
        year, month, day из даты типа '1 JAN 1970'

        Или ValueError
        """
        months = ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',)
        pattern_month = '(' + '|'.join(months) + ')'
        pattern = r'^(\d{1,2})\s+%s\s+(\d{4})$' % pattern_month
        s = s.strip()
        m = re.search(pattern, s, flags=re.I)
        if m:
            year = int(m.group(3))
            month = months.index(m.group(2).lower()) + 1
            day = int(m.group(1))
        else:
            pattern = r'^%s\s+(\d{4})$' % pattern_month
            m = re.search(pattern, s, flags=re.I)
            if m:
                year = int(m.group(2))
                month = months.index(m.group(1).lower()) + 1
                day = None
            else:
                m = re.search(r'^(\d{4})$', s)
                if m:
                    year = int(m.group(1))
                    month = None
                    day = None
        if m:
            datetime.datetime.strptime("%04d-%02d-%02d" % (year, month or 1, day or 1), "%Y-%m-%d")
        else:
            raise ValueError(cls.VALUE_ERROR_CREATE)
            # может быть ValueError
        return year, month, day

    @classmethod
    def from_str_dmy(cls, s):
        """
        year, month, day из даты типа '01.12.1970'

        Или ValueError
        """
        m = re.search(r'^(\d{2})[\.\/\-]?(\d{2})[\.\/\-]?(\d{4})$', s)
        if m:
            year = int(m.group(3))
            month = int(m.group(2))
            day = int(m.group(1))
        else:
            m = re.search(r'^(\d{2})[\.\/\-]?(\d{4})$', s)
            if m:
                year = int(m.group(2))
                month = int(m.group(1))
                day = None
            else:
                m = re.search(r'^(\d{4})$', s)
                if m:
                    year = int(m.group(1))
                    month = None
                    day = None
        if m:
            datetime.datetime.strptime("%04d-%02d-%02d" % (year, month or 1, day or 1), "%Y-%m-%d")
        else:
            raise ValueError(cls.VALUE_ERROR_CREATE)
            # может быть ValueError
        return year, month, day

    @classmethod
    def check_safe_str(cls, s, check_today=False, format='d.m.y'):
        """
        Проверка правильности строки "гггг-мм-дд", "гггг-мм", "гггг", или None ("null"), если дата не задана

        check_today - надо ли еще проверять, чтобы не было больше текущей даты
        Может возвратить непустое сообщение об ошибке
        """
        message = ''
        if isinstance(s, str):
            s = s.strip()
            if s.lower() == 'null':
                s = None
        if s:
            try:

                if format == 'd.m.y':
                    try:
                        year, month, day = cls.from_str_dmy(s)
                    except ValueError:
                        raise ServiceException(_(
                            "Неверный формат даты. "
                            "Допускается ДД.ММ.ГГГГ, ММ.ГГГГ, ГГГГ"))

                else:
                    m = re.search(cls.SAFE_STR_REGEX, s)
                    if not m:
                        raise ServiceException(_("Неверный формат даты. Допускается ГГГГ-ММ-ДД, ГГГГ-ММ, ГГГГ"))
                    year = m.group(1)
                    month = m.group(2)
                    day = m.group(3)

                    year = int(year)
                    if month:
                        month = int(month)
                    else:
                        month = None
                    if day:
                        day = int(day)
                    else:
                        day = None

                if not year:
                    raise ServiceException(_("Неверный год"))
                if month is not None and not (1 <= month <= 12):
                    raise ServiceException(_("Неверный месяц"))
                if day is not None and not (1 <= day <= 31):
                    raise ServiceException(_("Неверный день"))

                if month and day:
                    try:
                        datetime.datetime.strptime("%04d-%02d-%02d" % (year, month, day), "%Y-%m-%d")
                    except ValueError:
                        raise ServiceException(_("Неверная дата"))

                if check_today:
                    t_month = month if month else 1
                    t_day = day if day else 1
                    if datetime.date.today() < datetime.date(year, t_month, t_day):
                        raise ServiceException(_("Дата больше текущей"))
            except ServiceException as excpt:
                message = excpt.args[0]
        return message

    def diff(self, d):
        """
        Сравнить эту UnclearDate c d (UnlearDate or date or datetime)

        Результат: relativedelta: словарь, включающий years, months, days
        """
        if not self or not d:
            raise ValueError(_('Одна или обе даты для сравнения не заданы'))
        last = self.d
        if self.no_month:
            try:
                last = datetime.date(self.d.year, month=12, day=31)
            # Мало ли что там было при переходе из одного календаря в другой?
            except ValueError:
                pass
        elif self.no_day:
            for last_day_of_month in range(31, 0, -1):
                try:
                    last = datetime.date(self.d.year, month=self.d.month, day=last_day_of_month)
                except ValueError:
                    pass
                else:
                    break
        if isinstance(d, UnclearDate):
            first = d.d
            try:
                if d.no_month:
                    first = datetime.date(d.d.year, month=1, day=1)
                elif d.no_day:
                    first = datetime.date(d.d.year, month=d.d.month, day=1)
            except ValueError:
                pass
        elif isinstance(d, datetime.datetime) or isinstance(d, datetime.date):
            first = d
        else:
            raise ValueError(_('Неверный тип данного для даты для сравнения'))
        return relativedelta(last, first)

class UnclearDateCreator(object):
    # http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

    def __init__(self, field):
        self.field = field
        self.no_day_name = '%s_no_day' % self.field.name
        self.no_month_name = '%s_no_month' % self.field.name

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        date = obj.__dict__[self.field.name]
        if date is None:
            return None
        else:
            y = date.year
            if getattr(obj, self.no_month_name):
                m = None
            else:
                m = date.month
            if getattr(obj, self.no_day_name):
                d = None
            else:
                d = date.day
            return UnclearDate(y, m, d)

    def __set__(self, obj, value):
        if isinstance(value, UnclearDate):
            obj.__dict__[self.field.name] = value.d
            setattr(obj, self.no_month_name, value.no_month)
            setattr(obj, self.no_day_name, value.no_day)
        else:
            obj.__dict__[self.field.name] = self.field.to_python(value)

class UnclearDateModelField(models.DateField):
    # http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

    def contribute_to_class(self, cls, name):
        no_month_field = models.BooleanField(editable=False, default=False)
        no_day_field = models.BooleanField(editable=False, default=False)
        no_month_field.creation_counter = self.creation_counter
        no_day_field.creation_counter = self.creation_counter
        cls.add_to_class('%s_no_month' % name, no_month_field)
        cls.add_to_class('%s_no_day' % name, no_day_field)

        super(UnclearDateModelField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, UnclearDateCreator(self))

    def get_db_prep_save(self, value, connection):
        if isinstance(value, UnclearDate):
            value = value.d
        return super(UnclearDateModelField, self).get_db_prep_save(value, connection)

    def to_python(self, value):
        if isinstance(value, UnclearDate):
            return value

        return super(UnclearDateModelField, self).to_python(value)

    def formfield(self, **kwargs):
        from app.forms import UnclearDateField, UnclearSelectDateWidget
        defaults = {
            'form_class': UnclearDateField,
            'widget': UnclearSelectDateWidget,
            }
        kwargs.update(defaults)
        return super(UnclearDateModelField, self).formfield(**kwargs)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value.strftime('%Y-%m-%d')

class BaseModelInsertTimestamp(models.Model):

    class Meta:
        abstract = True

    insert_timestamp = models.BigIntegerField(_("Когда добавлено"), default=0, db_index=True)

    def fill_insert_timestamp(self):
        if not self.insert_timestamp:
            self.insert_timestamp = int(time.time())

    def save(self, *args, **kwargs):
        self.fill_insert_timestamp()
        return super(BaseModelInsertTimestamp, self).save(*args, **kwargs)

class BaseModelInsertUpdateTimestamp(BaseModelInsertTimestamp):

    class Meta:
        abstract = True

    update_timestamp = models.BigIntegerField(_("Когда изменено"), default=0, db_index=True)

    def fill_update_timestamp(self):
        if not self.update_timestamp:
            self.update_timestamp = int(time.time())

    def save(self, *args, **kwargs):
        self.fill_update_timestamp()
        return super(BaseModelInsertUpdateTimestamp, self).save(*args, **kwargs)

class GeoPointModel(models.Model):
    """
    Базовая GEO модель
    """
    latitude = models.FloatField(_("Широта"), blank=True, null=True)
    longitude = models.FloatField(_("Долгота"), blank=True, null=True)

    class Meta:
        abstract = True

class GeoPointAddressModel(GeoPointModel):
    """
    Базовая GEO модель, с расшифровкой координат в адрес
    """
    address = models.TextField(verbose_name=_("Адрес"), null=True, blank=True)

    @classmethod
    def coordinates_to_address(cls, latitude, longitude):
        result = None
        if latitude is not None and longitude is not None:
            geolocator = Nominatim(user_agent='blagodarie.org.geocoder')
            reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
            raw = reverse('%s,%s' % (latitude, longitude,))
            if raw:
                result = raw.address
        return result

    def put_geodata(self, latitude, longitude, save=True):
        if latitude != self.latitude or longitude != self.longitude:
            changed = True
            self.latitude = latitude
            self.longitude = longitude
            if latitude is not None and longitude is not None:
                self.address = GeoPointAddressModel.coordinates_to_address(self.latitude, self.longitude)
            else:
                self.address = None
            if save:
                self.save(update_fields=('latitude', 'longitude', 'address',))
        else:
            changed = False
        return changed

    class Meta:
        abstract = True


def files_upload_to(instance, filename):
    if hasattr(instance, 'photo_original_filename'):
        instance.photo_original_filename = filename
    fname = '.'.join(map(pytils.translit.slugify, filename.rsplit('.', 1)))
    today = datetime.date.today()

    # Путь к сохраняемому файлу:
    #   - первая составляющая (каталог): - /то, к чему относятся файлы/
    #   - год/месяц/день, чтоб не допускать огромное множество файлов
    #     (каталогов) в одной папке. Заодно и дата создания наглядна
    #   - первичный ключ того объекта, проверку на доступ к которому
    #     будем осуществлять
    #   - имя файла, оттуда убраны нелатинские символы, знаки препинания
    #     и т.п.
    today_pk_dir = "{0:d}/{1:02d}/{2:02d}".format(today.year, today.month, today.day)
    today_pk_dir += "/%s"

    if isinstance(instance, get_model('users', 'Profile')):
        return os.path.join('profile-photo',
                today_pk_dir % instance.user.pk, fname)
    else:
        return os.path.join('files', fname)

class FilesMixin(object):

    def file_field(self):
        if hasattr(self, 'photo'):
            file_ = self.photo
        else:
            file_ = None
        return file_

    def delete_from_media(self):
        file_ = self.file_field()
        if file_ and file_.path and os.path.exists(file_.path):
            try:
                dir_ = os.path.dirname(file_.path)
                os.remove(file_.path)
                os.removedirs(dir_)
            except OSError:
                pass
            thmb = os.path.join(settings.THUMBNAILS_STORAGE_ROOT, file_.name)
            if os.path.exists(thmb):
                try:
                    dir_ = os.path.dirname(thmb)
                    shutil.rmtree(thmb)
                    os.removedirs(dir_)
                except OSError:
                    pass

    def delete(self):
        self.delete_from_media()
        super(FilesMixin, self).delete()

class PhotoModel(FilesMixin, models.Model):
    """
    Базовый (дополнительный) класс для моделей, у которых есть фото объекта
    """

    # Имя по умолчанию для файла, если таковое не задано в потоке
    #
    DEFAULT_FNAME = 'photo.jpg'
    DEFAULT_AVATAR_IN_MEDIA = 'images/default_avatar.jpg'
    DEFAULT_AVATAR_IN_MEDIA_MALE = 'images/no-photo-gender-male.jpg'
    DEFAULT_AVATAR_IN_MEDIA_FEMALE = 'images/no-photo-gender-female.jpg'
    DEFAULT_AVATAR_IN_MEDIA_NONE = 'images/no-photo-gender-none.jpg'

    THUMB_WIDTH = 128
    THUMB_HEIGHT = 128
    THUMB_METHOD = 'crop'

    class Meta:
        abstract = True

    photo = models.ImageField("Фото", max_length=255, upload_to=files_upload_to, blank=True, null=True)
    photo_original_filename = models.CharField(max_length=255, editable=False, default='')

    @classmethod
    def get_photo(
        cls,
        request=None,
        content=None,
        max_photo_size=None,
        quality=None,
        quality_min_size=None,
        photo_content='binary'
    ):
        """
        Получить содержимое, которое положим потом в поле photo

        На входе или request.data.get('photo') или content
        """
        if not content:
            if request:
                content = request.data.get('photo') or None
        if content:
            name = getattr(content, 'name', cls.DEFAULT_FNAME)
            is_base64 = photo_content == 'base64'
            if isinstance(content, bytes):
                pass
            elif isinstance(content, str):
                if is_base64:
                    content = base64.b64decode(content)
                else:
                    content = content.encode()
            else:
                if is_base64:
                    content = base64.b64decode(content.read())
                else:
                    content = content.read()
            content = ContentFile(content, name)
            if not max_photo_size:
                max_photo_size = settings.PHOTO_MAX_SIZE
            if not quality:
                quality = settings.PHOTO_QUALITY
            if content.size > max_photo_size * 1024 * 1024:
                raise ServiceException("Размер загружаемого файла превышает %d Мб" % max_photo_size)
            if not quality_min_size:
                quality_min_size = settings.PHOTO_QUALITY_MIN_SIZE or 0
            content = ThumbnailContentFile(
                content,
                quality=quality,
                minsize=quality_min_size,
            ).generate()
            if not content:
                raise ServiceException("Загружаемый файл фото не является изображением")
        return content

    @classmethod
    def tweek_photo_url(cls, photo_url, google_photo_size=None):
        """
        Подправить photo_url с учетом google_photo_size
        """
        result = photo_url
        if not google_photo_size:
            google_photo_size = settings.GOOGLE_PHOTO_SIZE
        m = re.search(
            #      1       2     3      4     5
            r'^(https?://)(\S*)(google)(\S+)(\=s\d+\-c)$',
            result,
            flags=re.I
        )
        if m:
            result = m.group(1) + m.group(2) + m.group(3) + m.group(4) + \
                    '=s' + str(google_photo_size) + '-c'
        else:
            m = re.search(
                #     1        2     3      4     5         6
                r'^(https?://)(\S*)(google)(\S+)(/s\d+\-c/)(\S*)$',
                result,
                flags=re.I
            )
            if m:
                result = m.group(1) + m.group(2) + m.group(3) + m.group(4) + \
                            '/s' + str(google_photo_size) + '-c/' + m.group(6)
        return result

    def put_photo_from_url(
        self,
        photo_url,
        max_photo_size=None,
        quality=None,
        quality_min_size=None,
    ):
        """
        Положить фото в поле photo, считываемое из photo_url
        """
        result = False
        if photo_url:
            photo_url = PhotoModel.tweek_photo_url(photo_url)
            try:
                req = urllib.request.Request(photo_url)
                r = urllib.request.urlopen(req, timeout=20)
                if r.getcode() == 200:
                    content = PhotoModel.get_photo(
                        content=r.read(),
                        max_photo_size=max_photo_size,
                        quality=quality,
                        quality_min_size=quality_min_size,
                    )
                    if content:
                        self.photo.save(PhotoModel.DEFAULT_FNAME, content)
                        result = True
            except urllib.error.URLError:
                pass
        return result

    @classmethod
    def choose_photo_of(cls, request, photo):
        result = ''
        if photo:
            result = request.build_absolute_uri(settings.MEDIA_URL + photo)
        return result

    def choose_photo(self, request):
        """
        Выбрать фото пользователя
        """
        return PhotoModel.choose_photo_of(request, self.photo and self.photo.name or '')

    @classmethod
    def get_gendered_default_avatar(cls,
            gender,
            female_avatar=DEFAULT_AVATAR_IN_MEDIA_FEMALE,
            male_avatar=DEFAULT_AVATAR_IN_MEDIA_MALE,
            none_avatar=DEFAULT_AVATAR_IN_MEDIA_NONE,
        ):
        """
        Выбрать аватар по умолчанию в зависимости от пола
        """
        if gender == 'f':
            result = female_avatar
        elif gender == 'm':
            result = male_avatar
        else:
            result = none_avatar
        return result

    @classmethod
    def image_thumb(cls, request, fname,
            width=THUMB_WIDTH, height=THUMB_HEIGHT,
            method=THUMB_METHOD,
            put_default_avatar=False,
            default_avatar_in_media=DEFAULT_AVATAR_IN_MEDIA,
            mark_dead=False,
        ):
        if not fname and put_default_avatar:
            fname = default_avatar_in_media
        if fname:
            if mark_dead:
                # Если отметить как умершего, то в рамке размером 1/16 ребра прямоугольника,
                method='crop-black-frame-%s' % int((width + height)/2/16)
            path = '%(path_to_media)s%(fname)s/%(width)sx%(height)s~%(method)s~12.jpg'  % dict(
                    path_to_media=settings.THUMBNAILS_STORAGE_BASE_PATH,
                    fname=fname,
                    width=width,
                    height=height,
                    method=method,
            )
            return request.build_absolute_uri(path)
        else:
            return ''

    def choose_thumb(self, request,
        width=THUMB_WIDTH, height=THUMB_HEIGHT,
        method=THUMB_METHOD,
        put_default_avatar=False,
        default_avatar_in_media=DEFAULT_AVATAR_IN_MEDIA,
        mark_dead=False,
    ):
        fname = self.photo.name if self.photo else ''
        return PhotoModel.image_thumb(request, fname,
            width=width, height=height, method=method,
            put_default_avatar=put_default_avatar,
            default_avatar_in_media=default_avatar_in_media,
            mark_dead=mark_dead,
        )


class GenderMixin(object):
    """
    Применяется в 2 или более моделях
    """

    GENDER_MALE = 'm'
    GENDER_FEMALE = 'f'
    GENDER_CHOICES = (
        (GENDER_MALE, _('Мужской')),
        (GENDER_FEMALE, _('Женский')),
    )

    def check_gender(self, request):
        if 'gender' in request.data:
            if request.data.get('gender') not in (
                '',
                GenderMixin.GENDER_MALE,
                GenderMixin.GENDER_FEMALE,
                None,
               ):
                raise ServiceException(
                    "Задан неверный пол: допустимы '%s', '%s' или пусто" % (
                    GenderMixin.GENDER_MALE, GenderMixin.GENDER_FEMALE,
                ))
