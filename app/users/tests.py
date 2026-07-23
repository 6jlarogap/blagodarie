import hashlib
import hmac
import datetime
import json
import time
from decimal import Decimal
from io import BytesIO
from unittest import mock

from django.contrib.auth.models import Group, User
from django.db import transaction
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from contact.models import CurrentState, Journal, Key, KeyType, OperationType
from users.models import Oauth, Offer, Profile, TelegramRelationRecheckNotice, RentalEquipmentType, RentalOffer, RentalOfferMessage, \
    RentalReservationEvent, RentalReservationIntent, RentalReservationPaymentProof, TgDesc, \
    VpnDonorPreference, VpnFeedbackTicket, VpnProfile, VpnRunwayLedgerEntry, \
    VpnServerRunway, VpnStatsSnapshot, VpnTrafficPeriod
from users.views import ApiAuthTelegram
from wote.models import Video, Vote


@override_settings(TELEGRAM_BOT_TOKEN='123456:test-token')
class TelegramPendingProfileTests(TestCase):

    bot_token = '123456:test-token'

    def setUp(self):
        self.client = APIClient()

    def create_pending(self, username='pending_name'):
        response = self.client.post('/api/profile', {
            'tg_token': self.bot_token,
            'pending_tg_username': username,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def test_subject_metadata_covers_all_kinds_and_profile_formats(self):
        expected = (
            (None, False, 'person', True, 'Человек'),
            (None, True, 'organization', True, 'Организация'),
            ('unknown', True, 'unknown', False, 'Неизвестно'),
            ('bot', True, 'bot', True, 'Бот'),
            ('group', True, 'group', True, 'Группа'),
            ('channel', True, 'channel', True, 'Канал'),
        )
        for index, (telegram_kind, is_org, kind, confirmed, label) in enumerate(expected):
            user = User.objects.create_user(username=f'visual-{index}', first_name=label)
            profile = Profile.objects.create(
                user=user,
                telegram_kind=telegram_kind,
                is_org=is_org,
                latitude=55.75 + index / 100,
                longitude=37.61 + index / 100,
            )
            responses = (
                self.client.get('/api/profile', {'uuid': str(profile.uuid)}),
                self.client.get('/api/profile_graph', {
                    'uuid': str(profile.uuid),
                    'fmt': '3d-force-graph',
                }),
                self.client.get('/api/user/points', {'uuid': str(profile.uuid)}),
            )
            for response in responses:
                self.assertEqual(response.status_code, 200, response.data)
            payloads = (
                responses[0].data,
                responses[1].data['root_node'],
                responses[2].data['points'][0],
            )
            for data in payloads:
                self.assertEqual(data['subject_kind'], kind)
                self.assertEqual(data['subject_kind_confirmed'], confirmed)
                self.assertEqual(data['subject_kind_label'], label)

    @override_settings(TELEGRAM_BOT_USERNAME='DoveraBot')
    def test_user_points_meet_with_offers_adds_owner_subject_metadata(self):
        admin = User.objects.create_user(username='meet-admin', first_name='Meet Admin')
        Group.objects.create(pk=2, name='meetgame_admin').user_set.add(admin)
        Profile.objects.create(user=admin)
        owner = User.objects.create_user(username='meet-offer-owner', first_name='Offer Owner')
        Profile.objects.create(
            user=owner,
            telegram_kind=Profile.TELEGRAM_KIND_CHANNEL,
            latitude=55.75,
            longitude=37.61,
        )
        Offer.objects.create(owner=owner, question='Channel offer', latitude=55.76, longitude=37.62)

        self.client.force_authenticate(user=admin)
        response = self.client.get('/api/user/points/', {'meet': '1', 'admin': '1', 'with_offers': '1'})
        self.assertEqual(response.status_code, 200, response.data)
        offer_point = next(point for point in response.data['points'] if point.get('is_offer'))
        self.assertEqual(offer_point['subject_kind'], 'channel')
        self.assertEqual(offer_point['subject_kind_label'], 'Канал')
        self.client.force_authenticate(user=None)

    def test_user_points_video_votes_add_subject_metadata(self):
        owner = User.objects.create_user(username='video-owner', first_name='Video Owner')
        Profile.objects.create(user=owner)
        voter = User.objects.create_user(username='video-voter', first_name='Video Voter')
        Profile.objects.create(
            user=voter,
            telegram_kind=Profile.TELEGRAM_KIND_BOT,
            latitude=55.75,
            longitude=37.61,
        )
        video = Video.objects.create(creator=owner, source=Video.SOURCE_YOUTUBE, videoid='subject-video')
        Vote.objects.create(user=voter, video=video, time=1, button=Vote.VOTE_YES)

        response = self.client.get('/api/user/points/', {
            'source': Video.SOURCE_YOUTUBE,
            'videoid': 'subject-video',
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['points'][0]['subject_kind'], 'bot')
        self.assertEqual(response.data['points'][0]['subject_kind_label'], 'Бот')

    @mock.patch('users.models.TelegramApiMixin.send_to_telegram', return_value=True)
    def test_subject_kinds_authoritative_claims_and_non_person_login_guarantees(self, _send):
        manual = User.objects.create_user(username='manual-org', first_name='Manual')
        manual_profile = Profile.objects.create(user=manual, is_org=True)
        self.assertEqual(manual_profile.subject_kind, 'organization')
        self.assertFalse(manual_profile.is_person)

        pending_data = self.create_pending('kind_claim')
        pending = Profile.objects.get(uuid=pending_data['uuid'])
        self.assertEqual(pending.subject_kind, 'unknown')
        self.assertFalse(pending.is_person)
        self.assertTrue(pending.is_org)

        claimed = self.client.post('/api/profile', {
            'tg_token': self.bot_token,
            'tg_uid': '9400',
            'username': 'kind_claim',
            'first_name': 'KindBot',
            'telegram_kind': 'bot',
            'activate': '1',
            'did_bot_start': '1',
        }, format='json')
        self.assertEqual(claimed.status_code, 200, claimed.data)
        self.assertEqual(claimed.data['subject_kind'], 'bot')
        pending.refresh_from_db()
        self.assertFalse(pending.user.is_active)
        self.assertFalse(pending.did_bot_start)
        self.assertFalse(Token.objects.filter(user=pending.user).exists())

        auth = ApiAuthTelegram()
        result = auth.process_input({
            'id': '9400', 'username': 'kind_claim', 'first_name': 'Human Claim',
        })
        pending.refresh_from_db()
        self.assertEqual(result['user_uuid'], str(pending.uuid))
        self.assertEqual(pending.subject_kind, 'person')
        self.assertTrue(pending.is_person)
        self.assertFalse(pending.is_org)
        self.assertTrue(pending.user.is_active)
        self.assertTrue(Token.objects.filter(user=pending.user).exists())

        for chat_id, chat_type, expected_kind in (
            (-1009401, 'supergroup', 'group'), (-1009402, 'channel', 'channel'),
        ):
            response = self.client.post('/api/bot/group', {
                'tg_token': self.bot_token,
                'chat_id': chat_id,
                'title': expected_kind.title(),
                'type': chat_type,
                'username': expected_kind + '_name',
            }, format='json')
            self.assertEqual(response.status_code, 200, response.data)
            profile = Oauth.objects.get(provider='telegram', uid=str(chat_id)).user.profile
            self.assertEqual(profile.subject_kind, expected_kind)
            self.assertFalse(profile.user.is_active)
            self.assertFalse(profile.did_bot_start)
            self.assertFalse(Token.objects.filter(user=profile.user).exists())

            member = self.client.post('/api/bot/groupmember', {
                'tg_token': self.bot_token,
                'group': {
                    'chat_id': chat_id,
                    'title': expected_kind.title(),
                    'type': chat_type,
                    'username': expected_kind + '_name',
                },
                'user': {'tg_uid': '9400'},
            }, format='json')
            self.assertEqual(member.status_code, 200, member.data)
            pin = self.client.put('/api/bot/group', {
                'tg_token': self.bot_token,
                'old_chat_id': chat_id,
                'chat_id': chat_id,
                'title': expected_kind.title(),
                'type': chat_type,
                'username': expected_kind + '_name',
                'pin_message_id': 42,
            }, format='json')
            self.assertEqual(pin.status_code, 200, pin.data)
            self.assertEqual(
                Oauth.objects.get(provider='telegram', uid=str(chat_id)).username,
                expected_kind + '_name',
            )

    @mock.patch('users.models.TelegramApiMixin.send_to_telegram', return_value=True)
    def test_non_person_alias_moves_without_relations_and_person_only_actions_are_rejected(self, _send):
        sender = User.objects.create_user(username='kind-sender', first_name='Sender')
        Profile.objects.create(user=sender)
        old = User.objects.create_user(username='kind-old', first_name='Old')
        old_profile = Profile.objects.create(user=old)
        old_oauth = Oauth.objects.create(provider='telegram', uid='9500', username='moving_name', user=old)
        relation = CurrentState.objects.create(user_from=sender, user_to=old, attitude=CurrentState.TRUST)

        created = self.client.post('/api/profile', {
            'tg_token': self.bot_token,
            'tg_uid': '9501',
            'username': 'moving_name',
            'first_name': 'Moving Bot',
            'telegram_kind': 'bot',
        }, format='json')
        self.assertEqual(created.status_code, 200, created.data)
        target = Profile.objects.get(uuid=created.data['uuid'])
        old_oauth.refresh_from_db()
        self.assertEqual(old_oauth.username, '')
        self.assertTrue(CurrentState.objects.filter(pk=relation.pk, user_to=old).exists())
        self.assertTrue(Profile.objects.filter(pk=old_profile.pk).exists())

        for operation_id in (OperationType.TRUST, OperationType.MISTRUST, OperationType.THANK):
            OperationType.objects.get_or_create(pk=operation_id, defaults={'title': 'kind-%s' % operation_id})
            response = self.client.post('/api/addoperation', {
                'tg_token': self.bot_token,
                'user_id_from': sender.pk,
                'user_id_to': str(target.uuid),
                'operation_type_id': operation_id,
            }, format='json')
            self.assertEqual(response.status_code, 200, response.data)

        OperationType.objects.get_or_create(pk=OperationType.ACQ, defaults={'title': 'kind-acq'})
        rejected = self.client.post('/api/addoperation', {
            'tg_token': self.bot_token,
            'user_id_from': sender.pk,
            'user_id_to': str(target.uuid),
            'operation_type_id': OperationType.ACQ,
        }, format='json')
        self.assertEqual(rejected.status_code, 400, rejected.data)

        self.client.force_authenticate(user=sender)
        with mock.patch('contact.views.TelegramApiMixin.send_to_telegram') as send:
            trusted = self.client.post('/api/addoperation', {
                'user_id_to': str(target.uuid),
                'operation_type_id': OperationType.TRUST,
            }, format='json')
        self.assertEqual(trusted.status_code, 200, trusted.data)
        send.assert_not_called()
        self.client.force_authenticate(user=None)

        message = self.client.post('/api/tg_message', {
            'tg_token': self.bot_token,
            'user_from_uuid': str(sender.profile.uuid),
            'user_to_uuid': str(target.uuid),
            'chat_id': sender.pk,
            'message_id': 1,
        }, format='json')
        self.assertEqual(message.status_code, 400, message.data)

        meet = self.client.post('/api/meet_id', {
            'tg_token': self.bot_token,
            'username': target.user.username,
        }, format='json')
        self.assertEqual(meet.status_code, 400, meet.data)

        bot_start = self.client.put('/api/profile', {
            'tg_token': self.bot_token,
            'uuid': str(target.uuid),
            'did_bot_start': True,
        }, format='json')
        self.assertEqual(bot_start.status_code, 400, bot_start.data)
        target.refresh_from_db()
        self.assertFalse(target.did_bot_start)

    @mock.patch('users.models.TelegramApiMixin.send_to_telegram', return_value=False)
    def test_pending_profile_reuses_claims_and_resets_only_active_relations(self, _send):
        pending_data = self.create_pending('Pending_Name')
        repeated = self.create_pending('pending_name')
        self.assertEqual(repeated['uuid'], pending_data['uuid'])
        self.assertFalse(repeated['created'])

        pending = Profile.objects.get(uuid=pending_data['uuid'])
        self.assertIsNone(pending.owner_id)
        self.assertFalse(pending.user.is_active)
        self.assertFalse(Oauth.objects.filter(user=pending.user).exists())
        self.assertFalse(Token.objects.filter(user=pending.user).exists())

        source = User.objects.create_user(username='relation-source', first_name='Source')
        source_profile = Profile.objects.create(user=source, r_sympa=pending.user)
        Oauth.objects.create(provider='telegram', uid='9001', username='source_name', user=source)
        CurrentState.objects.create(
            user_from=source,
            user_to=pending.user,
            attitude=CurrentState.TRUST,
            thanks_count=2,
            is_father=True,
            is_sympa=True,
            is_sympa_confirmed=True,
            is_invite_meet=True,
            is_hide_meet=True,
        )
        CurrentState.objects.create(
            user_from=pending.user,
            user_to=source,
            is_reverse=True,
            attitude=CurrentState.TRUST,
            thanks_count=2,
        )
        operation = OperationType.objects.create(pk=991, title='pending test')
        journal = Journal.objects.create(user_from=source, user_to=pending.user, operationtype=operation)
        key_type = KeyType.objects.create(title='pending sentinel')
        key = Key.objects.create(owner=pending.user, type=key_type, value='sentinel')
        owner = User.objects.create_user(username='owned-source-owner', first_name='Owner')
        Profile.objects.create(user=owner)
        owned = User.objects.create_user(username='owned-source', first_name='Owned')
        Profile.objects.create(user=owned, owner=owner)
        CurrentState.objects.create(user_from=owned, user_to=pending.user, attitude=CurrentState.ACQ)

        with self.captureOnCommitCallbacks(execute=True):
            claimed = self.client.post('/api/profile', {
                'tg_token': self.bot_token,
                'tg_uid': '9002',
                'username': 'PENDING_NAME',
                'first_name': 'Claimed',
                'did_bot_start': '1',
            }, format='json')
        self.assertEqual(claimed.status_code, 200, claimed.data)
        self.assertEqual(claimed.data['uuid'], pending_data['uuid'])
        self.assertTrue(claimed.data['created'])

        pending.refresh_from_db()
        source_profile.refresh_from_db()
        self.assertIsNone(pending.pending_tg_username)
        self.assertTrue(pending.user.is_active)
        self.assertTrue(pending.did_bot_start)
        self.assertIsNone(source_profile.r_sympa_id)
        self.assertFalse(CurrentState.objects.filter(
            user_from__in=(source, pending.user), user_to__in=(source, pending.user)
        ).exists())
        self.assertTrue(Journal.objects.filter(pk=journal.pk).exists())
        self.assertTrue(Key.objects.filter(pk=key.pk).exists())
        self.assertTrue(Token.objects.filter(user=pending.user).exists())
        notice = TelegramRelationRecheckNotice.objects.get(user=source, profile=pending)
        self.assertEqual(notice.attempts, 0)
        self.assertEqual(notice.delivered_timestamp, 0)
        self.assertTrue(TelegramRelationRecheckNotice.objects.filter(user=owner, profile=pending).exists())
        self.assertFalse(TelegramRelationRecheckNotice.objects.filter(user=owned, profile=pending).exists())

        with self.captureOnCommitCallbacks(execute=True):
            failed_retry = self.client.post('/api/profile', {
                'tg_token': self.bot_token,
                'tg_uid': '9001',
                'username': 'source_name',
                'first_name': 'Source',
            }, format='json')
        self.assertEqual(failed_retry.status_code, 200, failed_retry.data)
        notice.refresh_from_db()
        self.assertEqual(notice.attempts, 1)
        self.assertEqual(notice.delivered_timestamp, 0)

        _send.return_value = True
        with self.captureOnCommitCallbacks(execute=True):
            retried = self.client.post('/api/profile', {
                'tg_token': self.bot_token,
                'tg_uid': '9001',
                'username': 'source_name',
                'first_name': 'Source',
            }, format='json')
        self.assertEqual(retried.status_code, 200, retried.data)
        notice.refresh_from_db()
        self.assertGreater(notice.delivered_timestamp, 0)

    @mock.patch('users.models.TelegramApiMixin.send_to_telegram', return_value=True)
    def test_corrupted_pending_profile_is_never_reset(self, _send):
        stable = User.objects.create_user(username='corrupt-stable', first_name='Stable')
        stable_profile = Profile.objects.create(user=stable)
        Oauth.objects.create(provider='telegram', uid='9050', username='stable_old', user=stable)
        pending_data = self.create_pending('corrupt_name')
        pending = Profile.objects.get(uuid=pending_data['uuid'])
        source = User.objects.create_user(username='corrupt-source', first_name='Source')
        Profile.objects.create(user=source)
        relation = CurrentState.objects.create(user_from=source, user_to=pending.user, attitude=CurrentState.TRUST)
        pending.user.is_active = True
        pending.user.save(update_fields=('is_active',))

        response = self.client.post('/api/profile', {
            'tg_token': self.bot_token,
            'tg_uid': '9050',
            'username': 'corrupt_name',
            'first_name': 'Stable',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        pending.refresh_from_db()
        self.assertEqual(pending.pending_tg_username, 'corrupt_name')
        self.assertTrue(CurrentState.objects.filter(pk=relation.pk).exists())
        self.assertTrue(Profile.objects.filter(pk=stable_profile.pk).exists())

    @mock.patch('users.models.TelegramApiMixin.send_to_telegram', return_value=True)
    def test_known_uid_wins_pending_collision_without_touching_identified_relations(self, _send):
        stable = User.objects.create_user(username='stable-user', first_name='Stable')
        stable_profile = Profile.objects.create(user=stable)
        stable_oauth = Oauth.objects.create(
            provider='telegram', uid='9100', username='old_name', user=stable,
        )
        source = User.objects.create_user(username='stable-source', first_name='Source')
        Profile.objects.create(user=source)
        relation = CurrentState.objects.create(
            user_from=source, user_to=stable, attitude=CurrentState.TRUST,
        )
        pending_data = self.create_pending('new_name')
        pending = Profile.objects.get(uuid=pending_data['uuid'])

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/api/profile', {
                'tg_token': self.bot_token,
                'tg_uid': stable_oauth.uid,
                'username': 'new_name',
                'first_name': 'Stable',
            }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(str(response.data['uuid']), str(stable_profile.uuid))
        stable_oauth.refresh_from_db()
        pending.refresh_from_db()
        self.assertEqual(stable_oauth.username, 'new_name')
        self.assertIsNone(pending.pending_tg_username)
        self.assertTrue(Profile.objects.filter(pk=pending.pk).exists())
        self.assertTrue(CurrentState.objects.filter(pk=relation.pk).exists())

    @mock.patch('users.models.TelegramApiMixin.send_to_telegram', return_value=True)
    def test_reassigned_verified_alias_moves_without_relation_transfer(self, _send):
        old = User.objects.create_user(username='old-user', first_name='Old')
        old_profile = Profile.objects.create(user=old)
        old_oauth = Oauth.objects.create(provider='telegram', uid='9200', username='shared_name', user=old)
        new = User.objects.create_user(username='new-user', first_name='New')
        new_profile = Profile.objects.create(user=new)
        Oauth.objects.create(provider='telegram', uid='9201', username='other_name', user=new)
        source = User.objects.create_user(username='alias-source', first_name='Source')
        Profile.objects.create(user=source)
        relation = CurrentState.objects.create(user_from=source, user_to=old, attitude=CurrentState.ACQ)

        response = self.client.post('/api/profile', {
            'tg_token': self.bot_token,
            'tg_uid': '9201',
            'username': 'SHARED_NAME',
            'first_name': 'New',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(str(response.data['uuid']), str(new_profile.uuid))
        old_oauth.refresh_from_db()
        self.assertEqual(old_oauth.username, '')
        self.assertTrue(CurrentState.objects.filter(pk=relation.pk, user_to=old).exists())
        self.assertTrue(Profile.objects.filter(pk=old_profile.pk).exists())

    @mock.patch('users.models.TelegramApiMixin.send_to_telegram', return_value=True)
    def test_web_auth_claims_same_pending_profile_and_pending_delete_is_rejected(self, _send):
        pending_data = self.create_pending('web_claim')
        pending = Profile.objects.get(uuid=pending_data['uuid'])
        self.client.force_authenticate(user=pending.user)
        rejected = self.client.delete('/api/profile', {'uuid': str(pending.uuid)}, format='json')
        self.assertEqual(rejected.status_code, 400)
        self.assertTrue(Profile.objects.filter(pk=pending.pk).exists())

        auth = ApiAuthTelegram()
        with transaction.atomic():
            result = auth.process_input({
                'id': '9300',
                'username': 'WEB_CLAIM',
                'first_name': 'Web',
                'last_name': 'Claim',
            })
        pending.refresh_from_db()
        self.assertEqual(result['user_uuid'], str(pending.uuid))
        self.assertIsNone(pending.pending_tg_username)
        self.assertTrue(pending.user.is_active)
        self.assertTrue(Token.objects.filter(user=pending.user).exists())


class MockUrlopenResponse:

    def __init__(self, content):
        self.content = content

    def read(self):
        return self.content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class ApiAuthTelegramTests(SimpleTestCase):

    bot_token = '123456:test-token'
    auth_date = '1700000000'

    def setUp(self):
        self.factory = RequestFactory()

    def make_hash(self, auth_data):
        data_check_string = '\n'.join(
            '%s=%s' % (key, value)
            for key, value in sorted(auth_data.items(), key=lambda item: item[0])
        )
        secret_key = hashlib.sha256(self.bot_token.encode()).digest()
        return hmac.new(
            secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

    @override_settings(
        TELEGRAM_BOT_TOKEN=bot_token,
        TELEGRAM_AUTH_DATA_OUTDATED=3600,
    )
    @mock.patch('users.views.time.time', return_value=1700000100)
    def test_check_input_ignores_split_redirect_query_params(self, _mock_time):
        auth_data = {
            'id': '1539785255',
            'first_name': 'Vitalik',
            'last_name': 'Drozd',
            'username': 'vdrzd',
            'photo_url': 'https://t.me/i/userpic/320/test.jpg',
            'auth_date': self.auth_date,
        }
        params = {
            'redirect_path': 'https://d3.doverabot.ru/?user_genesis_tree=wwg8LYXwlL',
            'up': 'on',
            'down': 'on',
            'depth': '2',
            'keep_user_data': 'on',
            **auth_data,
            'hash': self.make_hash(auth_data),
        }
        request = self.factory.get('/api/auth/telegram/', data=params)

        rd = ApiAuthTelegram().check_input(request)

        self.assertEqual(
            rd.get('redirect_path'),
            'https://d3.doverabot.ru/?user_genesis_tree=wwg8LYXwlL&up=on&down=on&depth=2',
        )
        self.assertEqual(rd.get('keep_user_data'), 'on')
        self.assertNotIn('up', rd)
        self.assertNotIn('down', rd)
        self.assertNotIn('depth', rd)


class ApiRentalOfferTests(TestCase):

    bot_token = '123456:test-token'

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username='owner', first_name='Owner')
        self.owner_profile = Profile.objects.create(user=self.owner)
        self.requester = User.objects.create_user(username='requester', first_name='Requester')
        self.requester_profile = Profile.objects.create(user=self.requester)

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_create_rental_offer(self):
        response = self.client.post('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'title': 'Tent 2 places',
            'description_text': 'Сдам палатку рядом с метро.',
            'price_text': '500 руб/день',
            'latitude': 55.75,
            'longitude': 37.61,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        offer = RentalOffer.objects.get()
        self.assertEqual(offer.owner, self.owner)
        self.assertEqual(offer.title, 'Tent 2 places')
        self.assertEqual(offer.latitude, 55.75)
        self.assertEqual(offer.quantity_total, 1)
        self.assertEqual(response.data['offer']['quantity_total'], 1)
        self.assertEqual(response.data['offer']['price_text'], '500 руб/день')

    def test_search_includes_rental_media_thumbnail_urls(self):
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Photo tent',
            description_text='Палатка с фото',
        )
        media = TgDesc.objects.create(
            message_id=10,
            chat_id=20,
            caption='Фото палатки',
            file_id='telegram-photo-file',
            file_type='photo',
            uuid_pack='00000000-0000-0000-0000-000000000010',
        )
        offer.tgdesc.add(media)

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
        })

        self.assertEqual(response.status_code, 200)
        offer_data = response.data['offers'][0]
        self.assertEqual(offer_data['media'][0]['id'], media.pk)
        self.assertEqual(offer_data['media'][0]['file_type'], 'photo')
        self.assertEqual(offer_data['media'][0]['caption'], 'Фото палатки')
        self.assertIn(
            '/api/rental/media/%s/thumbnail/' % media.pk,
            offer_data['media'][0]['thumbnail_url'],
        )
        self.assertIn('offer_uuid=%s' % offer.uuid, offer_data['media'][0]['thumbnail_url'])
        self.assertIn(
            'user_uuid=%s' % self.requester_profile.uuid,
            offer_data['media'][0]['thumbnail_url'],
        )

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    @mock.patch('users.views.urllib.request.urlopen')
    def test_rental_media_thumbnail_proxies_telegram_photo(self, mock_urlopen):
        from PIL import Image

        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Photo tent',
            description_text='Палатка с фото',
        )
        media = TgDesc.objects.create(
            message_id=10,
            chat_id=20,
            caption='Фото палатки',
            file_id='telegram-photo-file',
            file_type='photo',
            uuid_pack='00000000-0000-0000-0000-000000000011',
        )
        offer.tgdesc.add(media)
        image_content = BytesIO()
        Image.new('RGB', (64, 48), 'red').save(image_content, format='JPEG')
        mock_urlopen.side_effect = [
            MockUrlopenResponse(json.dumps({
                'ok': True,
                'result': {'file_path': 'photos/file.jpg'},
            }).encode('utf-8')),
            MockUrlopenResponse(image_content.getvalue()),
        ]

        response = self.client.get('/api/rental/media/%s/thumbnail/' % media.pk, data={
            'offer_uuid': str(offer.uuid),
            'user_uuid': str(self.requester_profile.uuid),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertTrue(response.content.startswith(b'\xff\xd8'))
        self.assertEqual(mock_urlopen.call_count, 2)

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_owner_listing_controls_include_paused_archived_and_status_updates(self):
        active_offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Active tent',
            description_text='Палатка',
        )
        RentalOffer.objects.create(
            owner=self.owner,
            title='Paused tent',
            status=RentalOffer.STATUS_PAUSED,
        )
        RentalOffer.objects.create(
            owner=self.owner,
            title='Archived tent',
            status=RentalOffer.STATUS_ARCHIVED,
        )
        RentalOffer.objects.create(owner=self.requester, title='Other tent')

        response = self.client.get('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'owner_uuid': str(self.owner_profile.uuid),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {offer['title'] for offer in response.data['offers']},
            {'Active tent', 'Paused tent', 'Archived tent'},
        )

        response = self.client.get('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'owner_uuid': str(self.owner_profile.uuid),
            'status': RentalOffer.STATUS_PAUSED,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [offer['title'] for offer in response.data['offers']],
            ['Paused tent'],
        )

        response = self.client.put('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'offer_uuid': str(active_offer.uuid),
            'quantity_total': 3,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        active_offer.refresh_from_db()
        self.assertEqual(active_offer.quantity_total, 3)
        self.assertEqual(response.data['offer']['quantity_total'], 3)

        response = self.client.put('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'offer_uuid': str(active_offer.uuid),
            'quantity_total': 0,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Неверный параметр quantity_total')

        response = self.client.get('/api/rental/offer/', data={
            'owner_uuid': str(self.owner_profile.uuid),
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Неверный токен телеграм бота')

        response = self.client.put('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'offer_uuid': str(active_offer.uuid),
            'status': RentalOffer.STATUS_PAUSED,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offer']['status'], RentalOffer.STATUS_PAUSED)

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'Active',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'], [])

        response = self.client.put('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'offer_uuid': str(active_offer.uuid),
            'status': RentalOffer.STATUS_ACTIVE,
        }, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'Active',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'][0]['title'], 'Active tent')

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_search_hides_private_and_explicit_mistrust(self):
        RentalOffer.objects.create(
            owner=self.owner,
            title='Travel tent',
            description_text='Легкая палатка',
            visibility=RentalOffer.VISIBILITY_AUTHENTICATED,
        )
        RentalOffer.objects.create(
            owner=self.owner,
            title='Private tent',
            description_text='Только по ссылке',
            visibility=RentalOffer.VISIBILITY_PRIVATE,
        )

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'tent',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['offers']), 1)
        self.assertEqual(response.data['offers'][0]['title'], 'Travel tent')

        CurrentState.objects.create(
            user_from=self.requester,
            user_to=self.owner,
            attitude=CurrentState.MISTRUST,
        )
        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'tent',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'], [])

    def test_search_filters_price_and_trusted_only(self):
        other = User.objects.create_user(username='other', first_name='Other')
        Profile.objects.create(user=other)
        RentalOffer.objects.create(
            owner=self.owner,
            title='Trusted tent',
            description_text='Легкая палатка',
            price_amount=Decimal('500.00'),
            price_currency='RUB',
            visibility=RentalOffer.VISIBILITY_AUTHENTICATED,
        )
        RentalOffer.objects.create(
            owner=other,
            title='Other tent',
            description_text='Легкая палатка',
            price_amount=Decimal('400.00'),
            price_currency='RUB',
            visibility=RentalOffer.VISIBILITY_AUTHENTICATED,
        )
        RentalOffer.objects.create(
            owner=self.owner,
            title='Expensive tent',
            description_text='Легкая палатка',
            price_amount=Decimal('900.00'),
            price_currency='RUB',
            visibility=RentalOffer.VISIBILITY_AUTHENTICATED,
        )
        CurrentState.objects.create(
            user_from=self.requester,
            user_to=self.owner,
            attitude=CurrentState.TRUST,
        )

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'tent',
            'price_max': '600',
            'trusted_only': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [offer['title'] for offer in response.data['offers']],
            ['Trusted tent'],
        )

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'tent',
            'price_max': '100',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'], [])

    def test_search_ranking_supports_taxonomy_only_match(self):
        equipment_type = RentalEquipmentType.objects.create(
            slug='packraft-test',
            canonical_name='Packraft Test',
            labels={'en': ['packraft-test']},
            synonyms={'ru': ['пакрафт-тест']},
        )
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='River kit',
            description_text='Легкая лодка для маршрута',
        )
        offer.equipment_types.add(equipment_type)

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'packraft-test',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [offer['title'] for offer in response.data['offers']],
            ['River kit'],
        )

    def test_search_ranking_keeps_text_fallback(self):
        RentalOffer.objects.create(
            owner=self.owner,
            title='Dry bag',
            description_text='Гермомешок для байдарки',
        )

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'гермомешок',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'][0]['title'], 'Dry bag')

    def test_search_ranking_uses_bounded_semantic_tokens(self):
        RentalOffer.objects.create(
            owner=self.owner,
            title='Палатка MSR',
            description_text='Легкая двухместная',
        )
        RentalOffer.objects.create(
            owner=self.owner,
            title='Газовая горелка',
            description_text='Для походной кухни',
        )

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'shelter',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [offer['title'] for offer in response.data['offers']],
            ['Палатка MSR'],
        )

    def test_search_ranking_keeps_visibility_and_mistrust_as_hard_filters(self):
        RentalOffer.objects.create(
            owner=self.owner,
            title='Палатка видимая',
            description_text='Для лагеря',
            visibility=RentalOffer.VISIBILITY_AUTHENTICATED,
        )
        RentalOffer.objects.create(
            owner=self.owner,
            title='Палатка приватная',
            description_text='Не должна попасть в поиск',
            visibility=RentalOffer.VISIBILITY_PRIVATE,
        )

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'shelter',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [offer['title'] for offer in response.data['offers']],
            ['Палатка видимая'],
        )

        CurrentState.objects.create(
            user_from=self.requester,
            user_to=self.owner,
            attitude=CurrentState.MISTRUST,
        )
        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'shelter',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'], [])

    @override_settings(TELEGRAM_BOT_USERNAME='DoveraBot')
    def test_rental_map_points_have_marker_payload_and_filters(self):
        equipment_type, created = RentalEquipmentType.objects.get_or_create(
            slug='tent',
            defaults=dict(canonical_name='Tent', labels={'en': ['tent']}),
        )
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Travel tent',
            description_text='Легкая палатка рядом с метро',
            price_text='500 руб/день',
            price_amount=Decimal('500.00'),
            price_currency='RUB',
            available_from='2026-07-01',
            available_to='2026-07-10',
            latitude=55.75,
            longitude=37.61,
        )
        offer.equipment_types.add(equipment_type)
        RentalOffer.objects.create(
            owner=self.owner,
            title='Hidden tent',
            visibility=RentalOffer.VISIBILITY_PRIVATE,
            latitude=55.76,
            longitude=37.62,
        )

        response = self.client.get('/api/user/points/', data={
            'rental': 'on',
            'user_uuid': str(self.requester_profile.uuid),
            'rental_uuid': str(offer.uuid),
            'rental_equipment_type': 'tent',
            'rental_date_from': '2026-07-02',
            'rental_date_to': '2026-07-03',
            'rental_price_max': '600',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['points']), 1)
        point = response.data['points'][0]
        self.assertTrue(point['is_rental'])
        self.assertEqual(point['marker_kind'], 'rental')
        self.assertEqual(point['marker_label'], 'Прокат')
        self.assertTrue(point['icon'].startswith('data:image/svg+xml'))
        self.assertIn('rental_owner_icon', point)
        self.assertIn('https://t.me/DoveraBot?start=rent-', point['rental_url'])
        self.assertEqual(point['equipment_types'][0]['slug'], 'tent')

        response = self.client.get('/api/user/points/', data={
            'rental': 'on',
            'user_uuid': str(self.requester_profile.uuid),
            'rental_uuid': str(offer.uuid),
            'rental_price_max': '100',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['points'], [])

        response = self.client.get('/api/user/points/', data={
            'rental': 'on',
            'user_uuid': str(self.requester_profile.uuid),
            'rental_uuid': 'not-a-uuid',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['points'], [])

    def test_rental_map_with_rentals_honors_filters_and_mistrust(self):
        RentalOffer.objects.create(
            owner=self.owner,
            title='Travel tent',
            description_text='Легкая палатка рядом с метро',
            price_amount=Decimal('500.00'),
            price_currency='RUB',
            latitude=55.75,
            longitude=37.61,
        )
        RentalOffer.objects.create(
            owner=self.owner,
            title='Private tent',
            visibility=RentalOffer.VISIBILITY_PRIVATE,
            price_amount=Decimal('400.00'),
            latitude=55.76,
            longitude=37.62,
        )

        response = self.client.get('/api/user/points/', data={
            'with_rentals': 'on',
            'user_uuid': str(self.requester_profile.uuid),
            'rental_query': 'tent',
            'rental_price_max': '600',
        })

        self.assertEqual(response.status_code, 200)
        rental_points = [point for point in response.data['points'] if point.get('is_rental')]
        self.assertEqual(len(rental_points), 1)
        self.assertEqual(rental_points[0]['title'], 'Travel tent')

        CurrentState.objects.create(
            user_from=self.requester,
            user_to=self.owner,
            attitude=CurrentState.MISTRUST,
        )
        response = self.client.get('/api/user/points/', data={
            'rental': 'on',
            'user_uuid': str(self.requester_profile.uuid),
            'rental_query': 'tent',
            'rental_price_max': '600',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['points'], [])

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_taxonomy_tags_offer_and_asks_for_ambiguous_board(self):
        response = self.client.post('/api/rental/offer/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'title': 'Сноуборд Burton',
            'description_text': 'Сдам сноуборд на выходные.',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        offer = RentalOffer.objects.get()
        self.assertEqual(
            list(offer.equipment_types.values_list('slug', flat=True)),
            ['snowboard'],
        )

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'доска',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'], [])
        self.assertIn('clarification', response.data)
        self.assertEqual(response.data['clarification']['ambiguous'][0]['slug'], 'board')

        response = self.client.get('/api/rental/search/', data={
            'user_uuid': str(self.requester_profile.uuid),
            'query': 'сноуборд',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['offers'][0]['title'], 'Сноуборд Burton')

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_message_identity_and_tenth_reservation_uses_system_payment(self):
        author = User.objects.create_user(username='author', first_name='Author')
        Profile.objects.create(user=author)
        key_type, created = KeyType.objects.get_or_create(
            pk=KeyType.BANKING_DETAILS_ID,
            defaults=dict(title='Реквизиты платежей'),
        )
        Key.objects.create(owner=self.owner, type=key_type, value='owner bank')
        Key.objects.create(owner=author, type=key_type, value='system bank')
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Tent',
            description_text='Палатка',
        )

        response = self.client.post('/api/rental/message/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'message_kind': RentalOfferMessage.KIND_OWNER_OFFER,
            'chat_id': 100,
            'message_id': 200,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RentalOfferMessage.objects.get().message_id, 200)

        for number in range(1, 10):
            RentalReservationIntent.objects.create(
                offer=offer,
                requester=self.requester,
                sequence_number=number,
                status=RentalReservationIntent.STATUS_CONFIRMED,
            )

        with override_settings(AUTHOR_USER_ID=author.pk, TELEGRAM_BOT_TOKEN=self.bot_token):
            response = self.client.post('/api/rental/reservation/', data={
                'tg_token': self.bot_token,
                'user_uuid': str(self.requester_profile.uuid),
                'offer_uuid': str(offer.uuid),
                'date_from': '2026-07-01',
                'date_to': '2026-07-03',
                'source_chat_id': 100,
                'source_message_id': 200,
            }, format='json')

        self.assertEqual(response.status_code, 200)
        reservation = RentalReservationIntent.objects.order_by('-pk').first()
        self.assertEqual(reservation.sequence_number, 10)
        self.assertEqual(reservation.status, RentalReservationIntent.STATUS_AWAITING_PAYMENT)
        self.assertGreater(reservation.hold_expires_at, int(time.time()))
        self.assertEqual(reservation.recipient_kind, RentalReservationIntent.RECIPIENT_SYSTEM)
        self.assertEqual(reservation.recipient_payment_info_snapshot, 'system bank')
        self.assertEqual(response.data['payment_recipient']['username'], 'author')

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_timed_hold_requires_dates_and_rejects_overlap_until_expired(self):
        other = User.objects.create_user(username='other', first_name='Other')
        other_profile = Profile.objects.create(user=other)
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Tent',
            description_text='Палатка',
        )

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Для бронирования укажите даты начала и окончания')

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        first_reservation = RentalReservationIntent.objects.get()
        self.assertEqual(first_reservation.status, RentalReservationIntent.STATUS_AWAITING_PAYMENT)
        self.assertEqual(response.data['reservation']['hold_seconds'], 600)
        self.assertEqual(response.data['event']['payload']['hold_seconds'], 600)

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(other_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-02',
            'date_to': '2026-07-04',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'На эти даты уже есть активная бронь')

        first_reservation.hold_expires_at = int(time.time()) - 1
        first_reservation.save(update_fields=('hold_expires_at',))
        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(other_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-02',
            'date_to': '2026-07-04',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        first_reservation.refresh_from_db()
        self.assertEqual(first_reservation.status, RentalReservationIntent.STATUS_EXPIRED)
        self.assertEqual(RentalReservationIntent.objects.count(), 2)

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_quantity_capacity_allows_overlaps_up_to_listing_quantity(self):
        other = User.objects.create_user(username='other', first_name='Other')
        other_profile = Profile.objects.create(user=other)
        third = User.objects.create_user(username='third', first_name='Third')
        third_profile = Profile.objects.create(user=third)
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Two tents',
            description_text='Две одинаковые палатки',
            quantity_total=2,
        )

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(other_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-02',
            'date_to': '2026-07-04',
        }, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(third_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-02',
            'date_to': '2026-07-04',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'На эти даты уже есть активная бронь')
        self.assertEqual(RentalReservationIntent.objects.count(), 2)

    @override_settings(
        TELEGRAM_BOT_TOKEN=bot_token,
        RENTAL_RESERVATION_HOLD_SECONDS=1800,
    )
    def test_reservation_hold_duration_uses_runtime_setting(self):
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Tent',
            description_text='Палатка',
        )
        before = int(time.time())

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')

        after = int(time.time())
        self.assertEqual(response.status_code, 200)
        reservation = RentalReservationIntent.objects.get()
        self.assertGreaterEqual(reservation.hold_expires_at, before + 1800)
        self.assertLessEqual(reservation.hold_expires_at, after + 1800)
        self.assertEqual(response.data['reservation']['hold_seconds'], 1800)
        self.assertEqual(response.data['event']['payload']['hold_seconds'], 1800)

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_payment_proof_rechecks_mistrust(self):
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Tent',
            description_text='Палатка',
        )
        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        reservation_id = response.data['reservation']['id']
        CurrentState.objects.create(
            user_from=self.owner,
            user_to=self.requester,
            attitude=CurrentState.MISTRUST,
        )

        response = self.client.post('/api/rental/reservation/payment_proof/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'reservation_id': reservation_id,
            'tgdesc': {
                'message_id': 300,
                'chat_id': 400,
                'media_group_id': '',
                'caption': 'paid',
                'file_id': 'proof-file',
                'file_type': 'photo',
                'uuid_pack': '00000000-0000-0000-0000-000000000001',
            },
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Бронирование недоступно из-за недоверия')
        self.assertEqual(RentalReservationPaymentProof.objects.count(), 0)

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_reservation_runtime_owner_consumer_actions(self):
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Tent',
            description_text='Палатка',
        )

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        reservation_id = response.data['reservation']['id']
        self.assertEqual(response.data['event']['event_type'], RentalReservationEvent.EVENT_CREATED)
        self.assertEqual(response.data['requester']['username'], 'requester')
        self.assertEqual(response.data['owner']['username'], 'owner')
        self.assertEqual(response.data['reservation']['status'], RentalReservationIntent.STATUS_AWAITING_PAYMENT)

        response_forbidden = self.client.put('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'reservation_id': reservation_id,
            'action': RentalReservationEvent.EVENT_OWNER_ACCEPT,
        }, format='json')
        self.assertEqual(response_forbidden.status_code, 403)

        response = self.client.put('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'reservation_id': reservation_id,
            'action': RentalReservationEvent.EVENT_OWNER_ACCEPT,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['reservation']['status'], RentalReservationIntent.STATUS_OWNER_ACCEPTED)
        self.assertEqual(response.data['event']['actor_role'], RentalReservationEvent.ROLE_OWNER)

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['created'], False)
        self.assertEqual(response.data['reservation']['id'], reservation_id)
        self.assertEqual(response.data['reservation']['status'], RentalReservationIntent.STATUS_OWNER_ACCEPTED)

        response = self.client.post('/api/rental/reservation/payment_proof/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'reservation_id': reservation_id,
            'tgdesc': {
                'message_id': 301,
                'chat_id': 401,
                'media_group_id': '',
                'caption': 'paid',
                'file_id': 'proof-file',
                'file_type': 'photo',
                'uuid_pack': '00000000-0000-0000-0000-000000000002',
            },
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['reservation']['status'], RentalReservationIntent.STATUS_PAYMENT_PROOF_SUBMITTED)
        self.assertEqual(response.data['event']['actor_role'], RentalReservationEvent.ROLE_REQUESTER)
        self.assertEqual(response.data['event']['event_type'], RentalReservationEvent.EVENT_PAYMENT_PROOF_SUBMITTED)
        self.assertEqual(response.data['proof']['uuid_pack'], '00000000-0000-0000-0000-000000000002')
        self.assertEqual(RentalReservationPaymentProof.objects.count(), 1)
        self.assertEqual(TgDesc.objects.get().file_id, 'proof-file')

        response = self.client.put('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'reservation_id': reservation_id,
            'action': RentalReservationEvent.EVENT_OWNER_CONFIRM,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['reservation']['status'], RentalReservationIntent.STATUS_CONFIRMED)
        self.assertEqual(len(response.data['events']), 4)

        response = self.client.put('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'reservation_id': reservation_id,
            'action': RentalReservationEvent.EVENT_CANCEL,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Заявка уже закрыта')

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_owner_can_reject_payment_proof_as_audited_terminal_dispute(self):
        other = User.objects.create_user(username='other', first_name='Other')
        other_profile = Profile.objects.create(user=other)
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Tent',
            description_text='Палатка',
        )

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        reservation_id = response.data['reservation']['id']

        response = self.client.post('/api/rental/reservation/payment_proof/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'reservation_id': reservation_id,
            'tgdesc': {
                'message_id': 302,
                'chat_id': 402,
                'media_group_id': '',
                'caption': 'paid',
                'file_id': 'proof-file',
                'file_type': 'photo',
                'uuid_pack': '00000000-0000-0000-0000-000000000004',
            },
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['reservation']['status'],
            RentalReservationIntent.STATUS_PAYMENT_PROOF_SUBMITTED,
        )

        response_forbidden = self.client.put('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'reservation_id': reservation_id,
            'action': RentalReservationEvent.EVENT_PAYMENT_PROOF_REJECTED,
        }, format='json')
        self.assertEqual(response_forbidden.status_code, 403)

        response = self.client.put('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.owner_profile.uuid),
            'reservation_id': reservation_id,
            'action': RentalReservationEvent.EVENT_PAYMENT_PROOF_REJECTED,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['reservation']['status'], RentalReservationIntent.STATUS_CANCELLED)
        self.assertEqual(response.data['event']['event_type'], RentalReservationEvent.EVENT_PAYMENT_PROOF_REJECTED)
        self.assertEqual(response.data['event']['status_to'], RentalReservationIntent.STATUS_CANCELLED)
        self.assertEqual(response.data['event']['actor_role'], RentalReservationEvent.ROLE_OWNER)
        self.assertIn(
            RentalReservationEvent.EVENT_PAYMENT_PROOF_REJECTED,
            [event['event_type'] for event in response.data['events']],
        )
        self.assertEqual(CurrentState.objects.count(), 0)

        response = self.client.get('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'status_group': 'recent_closed',
            'reservation_id': reservation_id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['reservations'][0]['events'][-1]['event_type'],
            RentalReservationEvent.EVENT_PAYMENT_PROOF_REJECTED,
        )

        response = self.client.post('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(other_profile.uuid),
            'offer_uuid': str(offer.uuid),
            'date_from': '2026-07-01',
            'date_to': '2026-07-03',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['reservation']['id'], reservation_id)

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_reservation_history_filters_roles_and_terminal_status_groups(self):
        requester_owned_offer = RentalOffer.objects.create(
            owner=self.requester,
            title='Requester board',
        )
        owner_offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Owner tent',
        )
        open_as_requester = RentalReservationIntent.objects.create(
            offer=owner_offer,
            requester=self.requester,
            date_from=datetime.date(2026, 7, 1),
            date_to=datetime.date(2026, 7, 3),
            status=RentalReservationIntent.STATUS_AWAITING_PAYMENT,
            hold_expires_at=int(time.time()) + 600,
        )
        open_as_owner = RentalReservationIntent.objects.create(
            offer=requester_owned_offer,
            requester=self.owner,
            date_from=datetime.date(2026, 8, 1),
            date_to=datetime.date(2026, 8, 2),
            status=RentalReservationIntent.STATUS_PAYMENT_PROOF_SUBMITTED,
            hold_expires_at=int(time.time()) + 600,
        )
        closed_as_requester = RentalReservationIntent.objects.create(
            offer=owner_offer,
            requester=self.requester,
            date_from=datetime.date(2026, 9, 1),
            date_to=datetime.date(2026, 9, 2),
            status=RentalReservationIntent.STATUS_CONFIRMED,
        )
        expired_as_requester = RentalReservationIntent.objects.create(
            offer=owner_offer,
            requester=self.requester,
            date_from=datetime.date(2026, 9, 3),
            date_to=datetime.date(2026, 9, 4),
            status=RentalReservationIntent.STATUS_OWNER_ACCEPTED,
            hold_expires_at=int(time.time()) - 1,
        )
        RentalReservationIntent.objects.create(
            offer=owner_offer,
            requester=self.requester,
            date_from=datetime.date(2026, 10, 1),
            date_to=datetime.date(2026, 10, 2),
            status=RentalReservationIntent.STATUS_CANCELLED,
        )
        RentalReservationEvent.objects.create(
            reservation=open_as_requester,
            actor=self.requester,
            actor_role=RentalReservationEvent.ROLE_REQUESTER,
            event_type=RentalReservationEvent.EVENT_CREATED,
            status_to=RentalReservationIntent.STATUS_AWAITING_PAYMENT,
        )
        RentalReservationPaymentProof.objects.create(
            reservation=open_as_owner,
            sender=self.owner,
            uuid_pack='00000000-0000-0000-0000-000000000003',
            recipient_kind=RentalReservationIntent.RECIPIENT_OWNER,
        )
        other = User.objects.create_user(username='other', first_name='Other')
        Profile.objects.create(user=other)
        RentalReservationIntent.objects.create(
            offer=owner_offer,
            requester=other,
            status=RentalReservationIntent.STATUS_AWAITING_PAYMENT,
            hold_expires_at=int(time.time()) + 600,
        )

        response = self.client.get('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'status_group': 'open',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item['reservation']['id'] for item in response.data['reservations']},
            {open_as_requester.pk, open_as_owner.pk},
        )
        self.assertEqual(
            {
                item['reservation']['id']: item['viewer_role']
                for item in response.data['reservations']
            },
            {
                open_as_requester.pk: RentalReservationEvent.ROLE_REQUESTER,
                open_as_owner.pk: RentalReservationEvent.ROLE_OWNER,
            },
        )

        response = self.client.get('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'role': RentalReservationEvent.ROLE_REQUESTER,
            'status_group': 'open',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['reservation']['id'] for item in response.data['reservations']],
            [open_as_requester.pk],
        )
        self.assertEqual(response.data['reservations'][0]['events'][0]['event_type'], 'created')

        response = self.client.get('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'role': RentalReservationEvent.ROLE_OWNER,
            'status_group': 'open',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['reservation']['id'] for item in response.data['reservations']],
            [open_as_owner.pk],
        )
        self.assertEqual(len(response.data['reservations'][0]['payment_proofs']), 1)

        response = self.client.get('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'status_group': 'recent_closed',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                item['reservation']['status']
                for item in response.data['reservations']
            },
            {
                RentalReservationIntent.STATUS_CONFIRMED,
                RentalReservationIntent.STATUS_CANCELLED,
                RentalReservationIntent.STATUS_EXPIRED,
            },
        )
        self.assertIn(
            closed_as_requester.pk,
            {item['reservation']['id'] for item in response.data['reservations']},
        )
        self.assertIn(
            expired_as_requester.pk,
            {item['reservation']['id'] for item in response.data['reservations']},
        )

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_reservation_history_requires_bot_token_and_hides_unrelated_rows(self):
        offer = RentalOffer.objects.create(
            owner=self.owner,
            title='Tent',
        )
        reservation = RentalReservationIntent.objects.create(
            offer=offer,
            requester=self.requester,
            status=RentalReservationIntent.STATUS_AWAITING_PAYMENT,
            hold_expires_at=int(time.time()) + 600,
        )
        intruder = User.objects.create_user(username='intruder', first_name='Intruder')
        intruder_profile = Profile.objects.create(user=intruder)

        response = self.client.get('/api/rental/reservation/', data={
            'user_uuid': str(self.requester_profile.uuid),
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Неверный токен телеграм бота')

        response = self.client.get('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(intruder_profile.uuid),
            'status_group': 'all',
            'reservation_id': reservation.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['reservations'], [])

        response = self.client.get('/api/rental/reservation/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.requester_profile.uuid),
            'role': 'bad-role',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Неверная роль в истории брони')


class ApiVpnMvpTests(TestCase):

    bot_token = '123456:test-token'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='vpnuser', first_name='Vpn User')
        self.profile = Profile.objects.create(user=self.user)

    @override_settings(
        TELEGRAM_BOT_TOKEN=bot_token,
        VPN_DEFAULT_CONFIG_URI_TEMPLATE='vless://%(token)s@current.example#%(label)s',
        VPN_PROFILE_TOKEN_TTL=7 * 86400,
    )
    def test_weekly_token_rotation_expires_old_subscription_token(self):
        response = self.client.post('/api/vpn/profile/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.profile.uuid),
            'action': 'fresh',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        vpn_profile = VpnProfile.objects.get(user=self.user)
        old_token = vpn_profile.subscription_token

        response = self.client.post('/api/vpn/profile/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.profile.uuid),
            'action': 'fresh',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        vpn_profile.refresh_from_db()
        new_token = vpn_profile.subscription_token
        self.assertNotEqual(old_token, new_token)

        response = self.client.get('/api/vpn/subscription/%s/' % old_token)
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/api/vpn/subscription/%s/' % new_token)
        self.assertEqual(response.status_code, 200)
        self.assertIn(new_token, response.content.decode('utf-8'))

    def test_xray_stats_import_stores_sanitized_counters_and_rollups(self):
        vpn_profile = VpnProfile.objects.create(
            user=self.user,
            config_uri='vless://SECRET-current-server-config',
        )
        payload = {
            'stats': [
                {
                    'name': 'user>>>%s>>>traffic>>>uplink' % vpn_profile.label,
                    'value': 1000,
                    'config_uri': 'SECRET-current-server-config',
                },
                {
                    'name': 'user>>>%s>>>traffic>>>downlink' % vpn_profile.label,
                    'value': 2000,
                    'password': 'SECRET',
                },
            ],
        }
        result = VpnStatsSnapshot.import_xray_counters(payload, captured_at=100000)
        self.assertEqual(result['imported'], 1)
        snapshot = VpnStatsSnapshot.objects.get()
        self.assertEqual(snapshot.source_label, vpn_profile.label)
        self.assertNotIn('SECRET', json.dumps(snapshot.data_dict(), default=str))

        VpnStatsSnapshot.import_xray_counters({
            vpn_profile.label: {
                'uplink': 1500,
                'downlink': 3000,
                'config_uri': 'SECRET-current-server-config',
            },
        }, captured_at=100100)
        period = VpnTrafficPeriod.objects.get(period_kind=VpnTrafficPeriod.KIND_WEEK)
        self.assertEqual(period.total_bytes(), 1500)

    @override_settings(TELEGRAM_BOT_TOKEN=bot_token)
    def test_public_dashboard_uses_usage_bands_not_named_exact_gb(self):
        other = User.objects.create_user(username='exactname', first_name='Exact Name')
        other_profile = Profile.objects.create(user=other)
        vpn_profile = VpnProfile.objects.create(user=self.user, config_uri='vless://one')
        other_vpn = VpnProfile.objects.create(user=other, config_uri='vless://two')
        today = datetime.date.today()
        VpnTrafficPeriod.objects.create(
            profile=vpn_profile,
            period_kind=VpnTrafficPeriod.KIND_MONTH,
            period_start=VpnTrafficPeriod.current_start(VpnTrafficPeriod.KIND_MONTH, today=today),
            downlink_bytes=5 * 1024 * 1024 * 1024,
        )
        VpnTrafficPeriod.objects.create(
            profile=other_vpn,
            period_kind=VpnTrafficPeriod.KIND_MONTH,
            period_start=VpnTrafficPeriod.current_start(VpnTrafficPeriod.KIND_MONTH, today=today),
            downlink_bytes=60 * 1024 * 1024 * 1024,
        )

        response = self.client.get('/api/vpn/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('exact_users', response.data)
        response_json = json.dumps(response.data, default=str)
        self.assertNotIn('exactname', response_json)
        self.assertNotIn('Exact Name', response_json)
        month_bands = {
            item['band']: item['count']
            for item in response.data['usage_graph']['month']
        }
        self.assertEqual(month_bands['1-10 GB'], 1)
        self.assertEqual(month_bands['50+ GB'], 1)

        admin = User.objects.create_user(
            username='vpnadmin',
            first_name='Vpn Admin',
            is_superuser=True,
            is_staff=True,
        )
        admin_profile = Profile.objects.create(user=admin)
        response = self.client.get('/api/vpn/dashboard/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(admin_profile.uuid),
            'exact': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('exact_users', response.data)
        self.assertIn('exactname', json.dumps(response.data['exact_users'], default=str))

    def test_donor_highlights_are_opt_in(self):
        visible = User.objects.create_user(username='visible-donor', first_name='Visible Donor')
        hidden = User.objects.create_user(username='hidden-donor', first_name='Hidden Donor')
        Profile.objects.create(user=visible)
        Profile.objects.create(user=hidden)
        VpnDonorPreference.objects.create(user=visible, is_visible=True, public_name='Visible Friend')
        VpnDonorPreference.objects.create(user=hidden, is_visible=False, public_name='Hidden Friend')
        VpnRunwayLedgerEntry.objects.create(
            user=visible,
            entry_type=VpnRunwayLedgerEntry.ENTRY_DONATION,
            amount=Decimal('100.00'),
        )
        VpnRunwayLedgerEntry.objects.create(
            user=hidden,
            entry_type=VpnRunwayLedgerEntry.ENTRY_DONATION,
            amount=Decimal('200.00'),
        )

        response = self.client.get('/api/vpn/dashboard/')
        self.assertEqual(response.status_code, 200)
        highlights_json = json.dumps(response.data['funding']['donor_highlights'], default=str)
        self.assertIn('Visible Friend', highlights_json)
        self.assertNotIn('Hidden Friend', highlights_json)

    @override_settings(
        TELEGRAM_BOT_TOKEN=bot_token,
        VPN_DEFAULT_CONFIG_URI_TEMPLATE='vless://%(token)s@current.example#%(label)s',
    )
    def test_fresh_prompt_is_current_server_funding_copy(self):
        VpnServerRunway.objects.create(
            label='current',
            prepaid_until=datetime.date.today() + datetime.timedelta(days=10),
            upcoming_payment_amount=Decimal('900.00'),
            currency='RUB',
        )
        response = self.client.post('/api/vpn/profile/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.profile.uuid),
            'action': 'fresh',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        prompt = response.data['donation_prompt']
        self.assertIn('Server runway:', prompt)
        self.assertIn('Fair share:', prompt)
        self.assertNotIn('new server', prompt.lower())
        self.assertNotIn('rent a new server', prompt.lower())
        self.assertNotIn('новый сервер', prompt.lower())

    @override_settings(
        TELEGRAM_BOT_TOKEN=bot_token,
        VPN_DEFAULT_CONFIG_URI_TEMPLATE='',
    )
    def test_fresh_without_current_config_records_structured_failure(self):
        response = self.client.post('/api/vpn/profile/', data={
            'tg_token': self.bot_token,
            'user_uuid': str(self.profile.uuid),
            'action': 'fresh',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('artifact_label', response.data)
        ticket = VpnFeedbackTicket.objects.get()
        self.assertEqual(ticket.reason, VpnFeedbackTicket.REASON_CONFIG_FAILED)
        self.assertEqual(ticket.artifact_label, response.data['artifact_label'])
