# merge_accounts.py
#
# Слить две учетные записи в одну
#
# Параметры:
#   uuid_to     куда сливаем
#   uuid_from   Откуда сливаем

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from users.models import Profile

class Command(BaseCommand):
    help = 'Merge account uuid_from to account uuid_to'
    
    def add_arguments(self, parser):
        parser.add_argument('uuid_to', type=str, help='uuid_to, destination account')
        parser.add_argument('uuid_from', type=str, help='uuid_from, account to merge')

    def handle(self, *args, **kwargs):
        uuid_to = kwargs['uuid_to']
        uuid_from = kwargs['uuid_from']
        try:
            profile_to = Profile.objects.select_related('user').get(uuid=uuid_to)
        except (ValidationError, Profile.DoesNotExist,):
            print("uuid_to: '%s' not found" % uuid_to)
            exit()
        try:
            profile_from = Profile.objects.select_related('user').get(uuid=uuid_from)
        except (ValidationError, Profile.DoesNotExist,):
            print("uuid_from: '%s' not found" % uuid_from)
            exit()
        if profile_from == profile_to:
            print('Same profiles. That is not allowed')
        profile_to.merge(profile_from)
