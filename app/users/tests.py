import hashlib
import hmac
from unittest import mock

from django.contrib.auth.models import User
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from contact.models import CurrentState, Key, KeyType
from users.models import Profile, RentalEquipmentType, RentalOffer, RentalOfferMessage, RentalReservationIntent
from users.views import ApiAuthTelegram


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
        self.assertEqual(response.data['offer']['price_text'], '500 руб/день')

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
                'source_chat_id': 100,
                'source_message_id': 200,
            }, format='json')

        self.assertEqual(response.status_code, 200)
        reservation = RentalReservationIntent.objects.order_by('-pk').first()
        self.assertEqual(reservation.sequence_number, 10)
        self.assertEqual(reservation.recipient_kind, RentalReservationIntent.RECIPIENT_SYSTEM)
        self.assertEqual(reservation.recipient_payment_info_snapshot, 'system bank')
        self.assertEqual(response.data['payment_recipient']['username'], 'author')
