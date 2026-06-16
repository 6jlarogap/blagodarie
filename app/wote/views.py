import os, time

from django.db import transaction
from django.db.models import Count
from django.db.models.query_utils import Q

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated

from app.utils import ServiceException, FromToCountMixin

from users.models import Profile, TelegramApiMixin
from contact.models import CurrentState
from wote.models import Video, Vote

class ApiWoteVideoMixin(object):

    def check_input_video(self, request):
        if not request.data.get('source') or \
            request.data['source'] not in dict(Video.VIDEO_SOURCES) or \
            not request.data.get('videoid'):
            raise ServiceException('Не задан(ы) или не верн(ы) параметры source, videoid')


class ApiWoteVote(ApiWoteVideoMixin, APIView):

    @transaction.atomic
    def post(self, request):
        """
        Отдать голос для видео. Требует аутентификации.

        Аутентификация достигается передачей вместе с запросом
        заголовка Authorization: Token <auth_token из куки auth_datа>

        http(s)://<api-host>/api/wote/vote/
        Post запрос. На входе json. Например:
        {
            // video source: возможны yt, rt, vk, bn, pt, по умолчанию yt
            // И ничто другое, кроме как в ./models.py:Video.VIDEO_SOURCES
            "source": "yt",
            "videoid": "Ac5cEy5llr4",
            
            // Название кнопки: возможны yes, no, not
            // И ничто другое, кроме как в ./models.py:Vote.VOTES
            "button": "yes",

            // Время от старта видео
            "time": 50,
        }
        Если видео с source, videoid не существует, то создается.
        Если успешно, возвращает json {}, статус: HTTP_200_OK

        Если запрос анонимный, то статус ответа HTTP_401_UNAUTHORIZED
        Если ошибка в переданных параметрах source, videoid, time,
        то статус HTTP_400_BAD_REQUEST,
        текст json: { "message": "<сообщение об ошибке>" }
        """
        if not request.user.is_authenticated:
            raise NotAuthenticated
        try:
            self.check_input_video(request)

            if not (button :=  request.data.get('button')) or \
               button not in dict(Vote.VOTES):
                raise ServiceException('Не задан или не верен параметры button')
            err_mes_time = 'Не задан или не верен параметр time'
            try:
                time_ = int(request.data.get('time'))
            except (TypeError, ValueError):
                raise ServiceException(err_mes_time)
            if time_ < 0:
                raise ServiceException(err_mes_time)

            video, created_video = Video.objects.get_or_create(
                source=request.data['source'],
                videoid=request.data['videoid'],
                defaults=dict(creator=request.user),
            )
            vote, created_vote = Vote.objects.select_for_update().get_or_create(
                user=request.user,
                video=video,
                time=time_,
                defaults=dict(button=button)
            )
            if not created_vote:
                vote.update_timestamp = int(time.time())
                vote.button = button
                vote.save(update_fields=('update_timestamp', 'button',))
            data = {}
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            transaction.set_rollback(True)
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

    def delete(self, request):
        """
        Удалить голос для видео. Требует аутентификации.

        Аутентификация достигается передачей вместе с запросом
        заголовка Authorization: Token <auth_token из куки auth_datа>

        http(s)://<api-host>/api/wote/vote/
        Delete запрос. На входе json. Например:
        {
            // video source: возможны yt, rt, vk, bn, pt, по умолчанию yt
            // И ничто другое, кроме как в ./models.py:Video.VIDEO_SOURCES
            "source": "yt",
            "videoid": "Ac5cEy5llr4",
            
            // Время от старта видео
            "time": 50,
        }
        Если успешно, возвращает json {}, статус: HTTP_200_OK

        Если запрос анонимный, то статус ответа HTTP_401_UNAUTHORIZED
        Если не найдено видео или не найден такой голос этого юзера или
        если ошибка в переданных параметрах source, videoid, time,
        то статус HTTP_400_BAD_REQUEST,
        текст json: { "message": "<сообщение об ошибке>" }
        """
        if not request.user.is_authenticated:
            raise NotAuthenticated
        try:
            self.check_input_video(request)
            try:
                vote = Vote.objects.get(
                    user=request.user,
                    video__source=request.data['source'],
                    video__videoid=request.data['videoid'],
                    time=int(request.data['time']),
                )
            except (TypeError, ValueError, KeyError, Vote.DoesNotExist, ):
                raise ServiceException('Не найдено видео или голос')
            vote.delete()
            data = {}
            status_code = status.HTTP_200_OK
        except ServiceException as excpt:
            data = dict(message=excpt.args[0])
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=status_code)

    def get(self, request):
        '''
        Показать все голоса по видео.

        Get запрос. Например:
        http(s)://<api-host>/api/wote/vote/?source=yt&videoid=Ac5cEy5llr4

        Возвращает json (пример):
        {
            "video": {
                "source": "yt",
                "videoid": "Ac5cEy5llr4",
                "insert_timestamp": 1684751776
            },
            "votes": [
                {
                    "user": {
                        "uuid": "8f686101-c5a2-46d0-a5ee-ffffffffffff"
                    },
                    "time": 40,
                    "button": "no",
                    "insert_timestamp": 1684751776,
                    "update_timestamp": 1685527009
                },
                ...
            ],
            "users": [
                {
                    "uuid": "8f686101-c5a2-46d0-a5ee-ffffffffffff",
                    "first_name": "Иван Иванов",
                    "photo": "https://path/to/photo.jpg"
                }
            ]
        }
        Возвратит json { "video": null, "votes": [], "users": [] } со статусом 404,
        если не заданы или заданы неверные source, videoid,
        или не найдено видео с source, videoid.
        '''
        
        votes = []
        users = []
        try:
            video = Video.objects.get(
                source=request.GET.get('source', Video.SOURCE_YOUTUBE),
                videoid=request.GET.get('videoid', ''),
            )
        except Video.DoesNotExist:
            status_code = status.HTTP_404_NOT_FOUND
            video_dict = None
        else:
            video_dict = video.data_dict()
            user_pks = []
            for vote in Vote.objects.select_related(
                    'user', 'user__profile'
                ).filter(video=video).order_by('time'):
                votes.append(vote.data_dict(put_user=True))
                if vote.user.pk not in user_pks:
                    user_pks.append(vote.user.pk)
                    users.append(dict(
                        uuid=vote.user.profile.uuid,
                        first_name=vote.user.first_name,
                        photo=vote.user.profile.choose_photo(request) if request else '',
                    ))
            status_code = status.HTTP_200_OK
        data = dict(video=video_dict, votes=votes, users=users)
        return Response(data=data, status=status_code)

api_wote_vote = ApiWoteVote.as_view()

class ApiWoteVoteSums(FromToCountMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        Показать суммы голосов по видео по каждой кнопке по времени ее нажатия.

        Get запрос. Например:
        http(s)://<api-host>/api/wote/vote/sums/?source=yt&videoid=Ac5cEy5llr4

        Возможны еще параметры:
            from:   с такой секунды видео начинать
            to:     по какую секунду видео показывать

        Возвращает json (пример):
        {
            buttons {
                // Обозначения кнопок
                "yes": [
                    { "time": 42, "count": 1 },
                    { "time": 50, "count": 2 }
                ],
                "no": [
                    { "time": 10, "count": 2 }
                ],
                "not": [
                    { "time": 20, "count": 3 }
                ]
            }
        }
        Если видео не найдено, или нет голосов по существующему видео,
        то результат: { {"buttons": "yes": [], "no": [], "not": [] } }
        '''
        buttons = dict()
        for button in dict(Vote.VOTES):
            buttons[button] = []
        q = Q(
            video__source=request.GET.get('source', Video.SOURCE_YOUTUBE),
            video__videoid=request.GET.get('videoid', '')
        )
        from_, to_ = self.get_from_to(request.GET, 'from', 'to')
        if from_ is not None:
            q &= Q(time__gte=from_)
        if to_ is not None:
            q &= Q(time__lte=to_)
        for rec in Vote.objects.values(
                'time', 'button'
           ).filter(q
           ).annotate(count=Count('id')
           ).order_by('time'):
            try:
                buttons[rec['button']].append(dict(time=rec['time'], count=rec['count']))
            except KeyError:
                # fool proof: вдруг какие кнопки будут удалены из системы?
                pass
        data = dict(buttons=buttons)
        return Response(data=data, status=status.HTTP_200_OK)

api_wote_vote_sums = ApiWoteVoteSums.as_view()


class ApiVoteGraph(FromToCountMixin, TelegramApiMixin, APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Получить результаты голосования по видео для представления в 3d-force-graph

        Включая связи доверия

        Get запрос. Например:
        http(s)://<api-host>/api/wote/vote/graph/?source=yt&videoid=Ac5cEy5llr4

        Возможны еще параметры:
            from:   с такой секунды видео начинать
            to:     по какую секунду видео показывать

        Возвращает json (пример):
        {
            "title": "yt-Ac5cEy5llr4",
            "bot_username": "DevBlagoBot",
            "nodes": [
                // Варианты кнопок
                {
                    "id": -1,
                    "first_name": "Да",
                    "photo": "https://<api-host>/thumb/images/poll_answer_1.jpg/128x128~crop-green-frame-10~12.jpg"
                },
                {
                    "id": -2,
                    "first_name": "Нет",
                    "photo": "https://<api-host>/thumb/images/poll_answer_2.jpg/128x128~crop-red-frame-10~12.jpg"
                },
                {
                    "id": -3,
                    "first_name": "Не ясно",
                    "photo": "https://<api-host>/thumb/images/poll_answer_3.jpg/128x128~crop-yellow-frame-10~12.jpg"
                },
                // пользователи
                {
                    "id": 326,
                    "first_name": "Иван",
                    "photo": "https://<api-host>/thumb/profile-photo/2023/05/15/326/photo.jpg/64x64~crop~12.jpg",
                    "gender": "m"
                },
                {
                    "id": 1506,
                    "first_name": "Марья",
                    "photo": "https://<api-host>/thumb/profile-photo/2023/05/16/1506/photo.jpg/64x64~crop~12.jpg",
                    "gender": "m"
                }
            ],
            "links": [
                // Нажатьые пользователем (source) кнопки (target)
                {
                    "source": 326,
                    "target": -2,
                    "is_video_vote": true
                },
                {
                    "source": 1506,
                    "target": -3,
                    "is_video_vote": true
                },
                // Доверия, недоверия, знакомства от пользователя (source) к пользователю (target)
                {
                    "source": 326,
                    "target": 1506,
                    "attitude": false
                }
            ]
        }
        """
        source = request.GET.get('source', Video.SOURCE_YOUTUBE)
        videoid = request.GET.get('videoid', '')
        nodes = []
        links = []
        votes_names = dict(Vote.VOTES)
        votes_image = Vote.VOTES_IMAGE.copy()
        n = 0
        for button in votes_image:
            n -= 1
            votes_image[button]['number'] = n
        # Узлы для нажатых кнопок:
        # id: yes: -1, no: -2, not: -3
        # first_name: Да, Нет, Не ясно
        # photo: для каждой своя картинка
        #
        for button in Vote.VOTES_IMAGE:
            nodes.append({
                'id': votes_image[button]['number'],
                'first_name': votes_names[button],
                'photo': Profile.image_thumb(
                    request,
                    votes_image[button]['image'],
                    width=512, height=512,
                ),
            })
        data = dict(
            title='%(source)s-%(videoid)s' % dict(
                source = source if source else '<неизвестно>',
                videoid = videoid if videoid else '<неизвестно>',
        ))
        user_pks = []
        q = Q(video__source=source, video__videoid=videoid)
        from_, to_ = self.get_from_to(request.GET, 'from', 'to')
        if from_ is not None:
            q &= Q(time__gte=from_)
        if to_ is not None:
            q &= Q(time__lte=to_)
        for rec in Vote.objects.filter(q
            ).select_related(
                'user', 'user__profile'
            ).values(
                'user__id', 'user__first_name',
                'user__profile__gender', 'user__profile__photo',
                'user__profile__uuid',
                'button'
            ).distinct('user', 'button'):
            if rec['user__id'] not in user_pks:
                nodes.append({
                    'id': rec['user__id'],
                    'first_name': rec['user__first_name'],
                    'uuid': rec['user__profile__uuid'],
                    'photo': Profile.image_thumb(request, rec['user__profile__photo']),
                    'gender': rec['user__profile__gender'],
                })
                user_pks.append(rec['user__id'])
            links.append(dict(
                source=rec['user__id'],
                target=votes_image[rec['button']]['number'],
                is_video_vote=True,
            ))
        if request.user.is_authenticated and request.user.id not in user_pks:
            user_pks.append(request.user.id)
            nodes.append(request.user.profile.data_dict(request=request, fmt='3d-force-graph'))

        q_connections = Q(
            attitude__isnull=False, is_reverse=False,
            user_from__in=user_pks, user_to__in=user_pks
        )
        for cs in CurrentState.objects.filter(q_connections).select_related(
                    'user_from__profile', 'user_to__profile',).distinct():
            links.append(cs.data_dict(show_attitude=True, fmt='3d-force-graph'))

        bot_username = self.get_bot_username()
        data.update(bot_username=bot_username, nodes=nodes, links=links)
        return Response(data=data, status=status.HTTP_200_OK)

api_wote_vote_graph = ApiVoteGraph.as_view()

class ApiVoteMy(FromToCountMixin, TelegramApiMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Получить нажатия кнопок авторизованного пользователя по видео

        Get запрос. Например:
        http(s)://<api-host>/api/wote/vote/my/?source=yt&videoid=Ac5cEy5llr4

        Возможны еще параметры:
            from:   с такой секунды видео начинать
            to:     по какую секунду видео показывать

        Возвращает json (пример):
        {
            "votes": [
                {
                    "time": 40,
                    "button": "no",
                    "update_timestamp": 1685527009
                },
                {
                    "time": 45,
                    "button": "yes",
                    "update_timestamp": 1685527209
                },
                ...
            ],
        }
        Голоса выводятся по возрастанию времени (time) на видео,
        когда была нажата кнопка

        Возвратит json { "votes": [], } со статусом 404,
        если не заданы или заданы неверные source, videoid,
        или не найдено видео с source, videoid.
        """
        votes = []
        try:
            video = Video.objects.get(
                source=request.GET.get('source', Video.SOURCE_YOUTUBE),
                videoid=request.GET.get('videoid', ''),
            )
        except Video.DoesNotExist:
            status_code = status.HTTP_404_NOT_FOUND
        else:
            q = Q(video=video, user=request.user,)
            from_, to_ = self.get_from_to(request.GET, 'from', 'to')
            if from_ is not None:
                q &= Q(time__gte=from_)
            if to_ is not None:
                q &= Q(time__lte=to_)
            votes = [
                vote.data_dict() for vote in Vote.objects.filter(q).order_by('time')
            ]
            status_code = status.HTTP_200_OK
        data = dict(votes=votes,)
        return Response(data=data, status=status.HTTP_200_OK)

api_wote_vote_my = ApiVoteMy.as_view()
