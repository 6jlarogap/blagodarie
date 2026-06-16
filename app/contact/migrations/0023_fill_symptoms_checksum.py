from django.db import migrations

from contact.models import SymptomChecksumManage

def reverse_it(apps, schema_editor):
    pass

def operation(apps, schema_editor):
    SymptomChecksumManage.compute_checksum()

class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0022_auto_20200505_2352'),
    ]

    operations = [
        migrations.RunPython(operation, reverse_it),
    ]
