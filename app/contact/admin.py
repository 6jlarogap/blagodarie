import time

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse

from app.admin import PreventBulkDeleteInAdmin

from .models import Key, Symptom, SymptomGroup

class SymptomGroupAdmin(PreventBulkDeleteInAdmin, admin.ModelAdmin):
    list_display = ('name', 'parent', 'deprecated')

class SymptomAdmin(PreventBulkDeleteInAdmin, admin.ModelAdmin):
    list_display = ('name', 'group', 'order', 'deprecated')

    def confirm_merge_symptoms(self, request, queryset):
        if queryset.count() != 2:
            self.message_user(
                request,
                _('Допускается объединение лишь двух симптомов'),
                messages.ERROR,
            )
            return
        response = TemplateResponse(
            request,
            'admin/confirm_merge_symptoms.html',
            dict(
                symptom_src=queryset[0],
                symptom_dst=queryset[1],
        ))
        return response

    confirm_merge_symptoms.short_description = _("Объединить симптомы")
    actions = (confirm_merge_symptoms, )

class KeyAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_', 'value',)

    def type_(self, obj):
        return '(%s) %s' % (obj.type.pk, obj.type.title,)

admin.site.register(Symptom, SymptomAdmin)
admin.site.register(SymptomGroup, SymptomGroupAdmin)
admin.site.register(Key, KeyAdmin)
