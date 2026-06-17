import hashlib
import hmac
from unittest import mock

from django.test import RequestFactory, SimpleTestCase, override_settings

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
