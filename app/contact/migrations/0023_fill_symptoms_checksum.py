import hashlib
import json
from collections import OrderedDict

from django.db import migrations

def reverse_it(apps, schema_editor):
    pass

def _has_field(model, field_name):
    return any(field.name == field_name for field in model._meta.get_fields())

def _compute_checksum(apps):
    Checksum = apps.get_model('contact', 'Checksum')
    Symptom = apps.get_model('contact', 'Symptom')
    SymptomGroup = apps.get_model('contact', 'SymptomGroup')

    checksum, created_ = Checksum.objects.get_or_create(
        name='symptom',
        defaults=dict(value=''),
    )

    symptom_group_query = SymptomGroup.objects.all()
    if _has_field(SymptomGroup, 'deprecated'):
        symptom_group_query = symptom_group_query.filter(deprecated=False)

    symptom_groups = []
    for symptomgroup in symptom_group_query.order_by('pk'):
        orderered_dict = OrderedDict()
        orderered_dict['id'] = symptomgroup.pk
        orderered_dict['name'] = symptomgroup.name
        orderered_dict['parent_id'] = symptomgroup.parent.pk if symptomgroup.parent else None
        symptom_groups.append(orderered_dict)

    symptom_query = Symptom.objects.all()
    if _has_field(Symptom, 'deprecated'):
        symptom_query = symptom_query.filter(deprecated=False)
    if _has_field(SymptomGroup, 'deprecated'):
        symptom_query = symptom_query.filter(group__deprecated=False)

    symptoms = []
    for symptom in symptom_query.distinct().order_by('pk'):
        orderered_dict = OrderedDict()
        orderered_dict['id'] = symptom.pk
        orderered_dict['name'] = symptom.name
        orderered_dict['group_id'] = symptom.group.pk if symptom.group else None
        orderered_dict['order'] = symptom.order
        symptoms.append(orderered_dict)

    all_dict = OrderedDict()
    all_dict['symptom_groups'] = symptom_groups
    all_dict['symptoms'] = symptoms
    all_str = json.dumps(all_dict, separators=(',', ':'), ensure_ascii=False)
    md5sum = hashlib.md5(all_str.encode('utf-8')).hexdigest()
    if checksum.value != md5sum:
        checksum.value = md5sum
        checksum.save()

def operation(apps, schema_editor):
    _compute_checksum(apps)

class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0022_auto_20200505_2352'),
    ]

    operations = [
        migrations.RunPython(operation, reverse_it),
    ]
