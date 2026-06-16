from django.db import models
from django.conf import settings

from app.models import BaseModelInsertUpdateTimestamp, BaseModelInsertTimestamp


class Video(BaseModelInsertTimestamp):

    SOURCE_YOUTUBE = 'yt'
    SOURCE_RUTUBE = 'rt'
    SOURCE_VKONTAKTE = 'vk'
    SOURCE_BASTYON = 'bn'
    SOURCE_PEERTUBE = 'pt'

    VIDEO_SOURCES = (
        (SOURCE_YOUTUBE, 'Google'),
        (SOURCE_RUTUBE, 'RuTube'),
        (SOURCE_VKONTAKTE, 'ВКонтакте'),
        (SOURCE_BASTYON, 'Bastyon'),
        (SOURCE_PEERTUBE, 'PeerTube'),
    )

    creator = models.ForeignKey('auth.User', verbose_name='Владелец', on_delete=models.CASCADE,)
    source = models.CharField('Источник', max_length=2, choices=VIDEO_SOURCES)
    # Ссылка для авторизации через tg bot имеет вид:
    # start=wote-rt-<videoid>, не длиннее 64 символов,
    # отсюда и макс длина videoid = 50
    videoid = models.CharField('Видео Id', max_length=50)

    class Meta:
        unique_together = ('source', 'videoid',)

    def data_dict(self):
        return dict(
            source=self.source,
            videoid=self.videoid,
            insert_timestamp=self.insert_timestamp,
        )

    @classmethod
    def video_vote_url(cls, source, videoid):
        if source == cls.SOURCE_YOUTUBE:
            result = settings.VIDEO_VOTE_URL + '#https://www.youtube.com/watch?v=' + videoid
        else:
            result = '%s-%s' % (source, videoid)
        return result

    def __str__(self):
        return '%s-%s' % (self.source, self.videoid,)

class Vote(BaseModelInsertUpdateTimestamp):

    VOTE_YES = 'yes'
    VOTE_NO = 'no'
    VOTE_NOT = 'not'

    VOTES = (
        (VOTE_YES, 'Да'),
        (VOTE_NO, 'Нет'),
        (VOTE_NOT, 'Не ясно'),
    )

    #   Под каждый из голосов (кнопок)
    #       - какая картинка
    #       - какой цвет для обрамления юзера на карте, если
    #         он выбрал такой голос (кнопку)

    VOTES_IMAGE = {
        VOTE_YES: dict (
            image='images/vote-yes.jpg',
            color='green',
            sort_order=0,
        ),
        VOTE_NO: dict (
            image='images/vote-no.jpg',
            color='red',
            sort_order=1,
        ),
        VOTE_NOT: dict (
            image='images/vote-not.jpg',
            color='blue',
            sort_order=2,
        ),
    }

    user = models.ForeignKey('auth.User', verbose_name='Пользователь', on_delete=models.CASCADE,)
    video = models.ForeignKey(Video, verbose_name='Видео', on_delete=models.CASCADE,)
    time = models.PositiveIntegerField('Время', default=0)
    button = models.CharField('Кнопка', max_length=10, choices=VOTES)

    class Meta:
        unique_together = ('user', 'video', 'time',)

    def data_dict(self, put_user=False):
        result = dict(
            time=self.time,
            button=self.button,
            update_timestamp=self.update_timestamp,
        )
        if put_user:
            result.update(user=dict(uuid=self.user.profile.uuid)),
        return result

    def __str__(self):
        return '%s: %s-%s, %s: %s' % (
            self.user.first_name,
            self.video.source,
            self.video.videoid,
            self.time,
            self.button,
        )
