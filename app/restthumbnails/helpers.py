from django.conf import settings
from django.utils.crypto import salted_hmac

from restthumbnails import exceptions

try:
    from PIL import ImageColor
except ImportError:
    import ImageColor

import re


RE_SIZE = re.compile(r'(\d+)?x(\d+)?$')


def parse_size(size):
    """
    Parse a string in the format "[X]x[Y]" and return the dimensions as a tuple
    of integers. Raise InvalidSizeError if the string is not valid.

    >>> parse_size("200x200")
    (200, 200)
    >>> parse_size("200x")
    (200, 0)
    >>> parse_size("x200")
    (0, 200)
    """
    match = RE_SIZE.match(str(size))
    if not match or not any(match.groups()):
        raise exceptions.InvalidSizeError(
            "'%s' is not a valid size string." % size)
    return [0 if not x else int(x) for x in match.groups()]


def parse_method(method):
    # FIXME: available processors should be a setting

    # Добавка к методу crop:
    # (1) просто crop:
    #       * уместить thumbnail в size, ничего не потеряв в избражении
    #         (если чтобы уместить в size, надо обрезать),
    #       * ничего не добавив в size (как при scale, чтобы
    #         вместить недостающее)
    #       * при наличие свободного места в рамке размером size,
    #         залить это место белым цветом
    # (2) crop-rgb<6-hex-digits>:
    #       Тоже самое, что (1), но с цветом #<6-hex-digits>
    # (3) crop-<WellKnowColor>:
    #       Тоже самое, что (1), но с цветом <WellKnowColor>
    #       из PIL.ImageColor.colormap,
    #       https://github.com/python-pillow/Pillow/blob/main/src/PIL/ImageColor.py,
    #       который наверняка соответствует: https://www.w3.org/TR/css-color-3/
    # (4)
    #   crop-frame-N
    #   crop-rgb<6-hex-digits>-frame-N
    #   crop-<WellKnowColor>-frame-N
    #       Вокруг прямоугольника иконки (thumbnail) с его размером size
    #       рисуется рамка толщиной N пикселей с заданным цветом
    #       rgb<6-hex-digits> или <WellKnowColor> или
    #       белым цветом, если не цвет не задан.
    #   (!) То есть реальный размер иконки увеличивается на N пикселей
    #       со всех сторон.
    #
    valid = True
    crop_background = 'white'
    frame = 0
    if method == 'crop':
        pass
    else:
        m = re.search(r'^crop\-rgb([0-9A-Fa-f]{6})', method)
        if m:
            crop_background = '#%s' % m.group(1)
        else:
            m = re.search(r'^crop\-(\w+)', method)
            if m:
                crop_background = m.group(1).lower()
                if crop_background not in ImageColor.colormap:
                    valid = False
        if valid and method.startswith('crop'):
            m = re.search(r'\-frame\-(\d+)$', method)
            if m:
                frame = int(m.group(1))
    if valid and not method.startswith('crop') and method not in ('smart', 'scale',):
        valid = False
    if not valid:
        raise exceptions.InvalidMethodError(
            "'%s' is not a valid method string." % method)
    return method, crop_background, frame


def get_secret(source, size, method, extension):
    """
    Get a unique hash based on file path, size, method and SECRET_KEY.
    """
    secret_sauce = '-'.join((source, size, method, extension))
    return salted_hmac(source, secret_sauce).hexdigest()


def get_key(source, size, method, extension):
    """
    Get a unique key suitable for the cache backend.
    """
    from restthumbnails import defaults
    return '-'.join((
        defaults.KEY_PREFIX, get_secret(source, size, method, extension)))


def get_thumbnail(source, size, method, extension, secret):
    from restthumbnails import defaults
    instance = defaults.thumbnail_file()(
        source=source,
        size=size,
        method=method,
        extension=extension)
    if instance.secret != secret and False:
        raise exceptions.InvalidSecretError(
            "Secret '%s' does not match." % secret)
    return instance


def get_thumbnail_proxy(source, size, method, extension):
    from restthumbnails import defaults
    return defaults.thumbnail_proxy()(
        source=source,
        size=size,
        method=method,
        extension=extension)
