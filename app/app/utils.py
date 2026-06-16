import datetime, time, re
from skyfield.api import load
from skyfield.framelib import ecliptic_frame

from django.conf import settings

class ServiceException(Exception):
    """
    Чтобы не плодить цепочки if (try) else ... if (try) ... else
    
    Пример:
    try:
        if not condition1:
            raise ServiceException('Condition 1 failed')
        try:
            # some code
        except SomeException:
            raise ServiceException('Condition 2 failed')
        # all good, going further
    except ServiceException as excpt:
        print(excpt.args[0])
    else:
        # all good
    """
    pass

class SkipException(Exception):
    """
    Чтобы обойти дальнейший код и выйти в окончание view
    
    Пример:
    try:
        data, status_code = self.func(request)
        raise SkipException
        много
                строк
                        кода
    except SkipException:
        pass
    return Response(data, status_code)
    """
    pass

class SQL_Mixin(object):
    """
    Для raw- вызовов
    """

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(list(zip(columns, row)))
            for row in cursor.fetchall()
        ]

    def sql_like_value(self, s):
        """
        Escape a sring for sql like expression
        """
        return s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

class FrontendMixin(object):

    def get_frontend_url(self, request, path='', ending_slash='/'):
        """
        Получить полный путь к path на front-end

        Если задан settings.FRONTEND_ROOT:
            имя хоста берем оттуда
        Иначе:
            Полагаем, что это апи вызывается по http(s)://api.some.site,
            где 'api' - обязательно
        """
        if settings.FRONTEND_ROOT:
            fe_site = settings.FRONTEND_ROOT.rstrip('/')
        else:
            host = request.get_host()
            m = re.search(r'^api\.(\S+)$', host, flags=re.I)
            if m:
                host = m.group(1).lower()
            # else
                # Затычка: frontend == backend.
                # Невозможная ситуация в реальной работе
            fe_site = '%(https)s://%(host)s' % dict(
                https='https' if request.is_secure() else 'http',
                host=host,
            )
        fe_path = path.strip('/')
        if not fe_path or '?' in path:
            ending_slash = ''
        return "%(fe_site)s/%(fe_path)s%(ending_slash)s" % dict(
            fe_site=fe_site,
            fe_path=fe_path,
            ending_slash=ending_slash,
        )

    def profile_url_by_uuid(self, request, uuid, fmt='3d-force-graph'):
        if fmt == '3d-force-graph':
            return settings.GRAPH_URL + '?user_uuid_trusts=%s' % uuid
        else:
            return self.get_frontend_url(request, 'profile') + '?id=%s' % uuid

    def profile_url(self, request, profile, fmt='3d-force-graph'):
        return self.profile_url_by_uuid(request, profile.uuid, fmt)

    def profile_link(self, request, profile,):
        url_profile = self.profile_url(request, profile,)
        link = '<a href="%(url_profile)s">%(first_name)s</a>' % dict(
            url_profile=url_profile,
            first_name=profile.user.first_name or 'Без имени',
        )
        return link

    def get_frontend_name(self, request):
        """
        Получить имя хоста front-end, без :цифры, если они есть

        Для отправки туда кук
        """
        return re.sub(r'\:\d+$', '',
            re.sub(r'^https?://', '', self.get_frontend_url(request).rstrip('/'))
        )

class FromToCountMixin(object):

    def get_from_to(self, data, from_, to_):
        """
        Вернуть валидные целые числа от и до

        data в вызывающем методе или request.GET или request.data
        """
        try:
            from_ = int(data.get(from_))
            if from_ < 0:
                from_ = None
        except (TypeError, ValueError,):
            from_ = None
        try:
            to_ = int(data.get(to_))
            if to_ < 0:
                to_ = None
            elif from_ is not None and to_ < from_:
                to_ = from_
        except (TypeError, ValueError,):
            to_ = None
        return from_, to_

class Misc(object):

    FORMAT_DATE = '%d.%m.%Y'
    FORMAT_TIME = '%H:%M:%S'

    @classmethod
    def datetime_string(cls, timestamp, with_timezone=True):
        """
        Строка времени

        Например, 13.04.2025 00:33:15 +03
        """
        dt = datetime.datetime.fromtimestamp(timestamp)
        result = dt.strftime(cls.FORMAT_DATE + ' ' + cls.FORMAT_TIME)
        if with_timezone:
            str_tz = dt.strftime('%Z')
            if not str_tz:
                str_tz = dt.astimezone().tzname()
            result += ' ' + str_tz
        return result

    @classmethod
    def get_moon_day(cls, utc_time=None):
        """
        Из unix timestamp получить номер дня по лунному календарю, 0 - 27
        """

        if not utc_time:
            utc_time = int(time.time())

        ts = load.timescale()
        d = datetime.datetime.utcfromtimestamp(utc_time)
        t = ts.utc(d.year, d.month, d.day, d.hour, d.minute, d.second)

        eph = load('de421.bsp')
        sun, moon, earth = eph['sun'], eph['moon'], eph['earth']

        e = earth.at(t)
        _, slon, _ = e.observe(sun).apparent().frame_latlon(ecliptic_frame)
        _, mlon, _ = e.observe(moon).apparent().frame_latlon(ecliptic_frame)
        phase = (mlon.degrees - slon.degrees) % 360.0
        if phase >= 360:
            phase = phase % 360.
        elif phase < 0:
            phase = 0
        return int(phase * 30 / 360)

