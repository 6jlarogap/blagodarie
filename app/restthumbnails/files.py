from logging import getLogger

from restthumbnails import processors, exceptions
from restthumbnails.base import ThumbnailBase

import os

from django.conf import settings
from django.core.files.base import ContentFile

logger = getLogger(__name__)


class ThumbnailFileBase(ThumbnailBase):
    @property
    def name(self):
        raise NotImplementedError

    @property
    def path(self):
        raise NotImplementedError

    @property
    def url(self):
        raise NotImplementedError

    def generate(self):
        return self._generate()


class ThumbnailFile(ThumbnailFileBase):
    """
    Manages the generation of thumbnails using the storage backends
    defined in settings.

    >>> thumb = ThumbnailFile('path/to/file.jpg', (200, 200), 'crop', '.jpg')
    >>> thumb.generate()
    True
    >>> thumb.url
    '/path/to/file.jpg/200x200/crop/<random_hash>.jpg'

    """
    def __init__(self, *args, **kwargs):
        from restthumbnails import defaults
        self.storage = defaults.storage_backend()
        self.source_storage = defaults.source_storage_backend()
        super(ThumbnailFile, self).__init__(*args, **kwargs)

    def _exists(self):
        return self.storage.exists(self.path)

    def _source_exists(self):
        return self.source_storage.exists(self.source)

    @property
    def name(self):
        return self.file_signature % {
            'source': os.path.normpath(self.source),
            'size': self.size_string,
            'method': self.method,
            'secret': self.secret,
            'extension': self.extension}

    @property
    def path(self):
        return self.storage.path(self.name)

    @property
    def url(self):
        return self.storage.url(self.name)

    def generate(self):
        if self._source_exists():
            if not self._exists():
                # work only with allowed sizes.
                min_ = settings.THUMBNAILS_ALLOWED_SIZE_RANGE['min']
                max_ = settings.THUMBNAILS_ALLOWED_SIZE_RANGE['max']
                if min_ <= self.size[0] <= max_ or \
                   min_ <= self.size[1] <= max_:

                    im = processors.get_image(self.source_storage.open(self.source))
                    im = processors.scale_and_crop(
                        im, self.size, self.method,
                        crop_background=self.crop_background,
                        frame=self.frame,
                    )
                    im = processors.colorspace(im)
                    if getattr(im, 'mode', '').upper() == 'RGBA':
                        im = im.convert('RGB')
                    im = processors.save_image(im)
                    self.storage.save(self.name, im)
                    return True
            return False
        raise exceptions.SourceDoesNotExist(self.source)

class ThumbnailContentFile(object):
    """
    Принимает файл, делает из него ContentFile в соответствии с заданным качеством

    -   source,  любой объект, имеющий метод .read(),
        например, файл из request
    -   minsize, минимальный размер фото 
        (число пикселей), при котором делается
        минимизация фото
    -   quality. допустимое качество
    """

    def __init__(self, source, minsize=0, quality=50):
        self.source = source
        self.quality = quality
        self.minsize = minsize

    def generate(self):
        """
        Возвращает ContentFile или None, если это не графический файл
        """
        return processors.get_minimized_contentfile(
            source=self.source,
            quality=self.quality,
            minsize=self.minsize,
        )
