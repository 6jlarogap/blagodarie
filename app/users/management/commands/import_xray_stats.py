import json
import sys

from django.core.management.base import BaseCommand, CommandError

from users.models import VpnStatsSnapshot


class Command(BaseCommand):
    help = 'Import sanitized per-user Xray traffic counters for VPN profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            nargs='?',
            help='JSON file with Xray stats. Reads stdin when omitted.',
        )
        parser.add_argument(
            '--captured-at',
            type=int,
            default=None,
            help='Unix timestamp for the snapshot. Defaults to current time.',
        )

    def handle(self, *args, **kwargs):
        json_file = kwargs.get('json_file')
        try:
            if json_file:
                with open(json_file, encoding='utf-8') as fh:
                    payload = json.load(fh)
            else:
                payload = json.load(sys.stdin)
        except (OSError, json.JSONDecodeError) as excpt:
            raise CommandError('Failed to read Xray stats JSON: %s' % excpt)

        result = VpnStatsSnapshot.import_xray_counters(
            payload,
            captured_at=kwargs.get('captured_at'),
        )
        self.stdout.write(
            'Imported %s VPN stats snapshots; skipped labels: %s' % (
                result['imported'],
                ', '.join(result['skipped_labels']) if result['skipped_labels'] else '-',
            )
        )
