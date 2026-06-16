
class PreventBulkDeleteInAdmin(object):
    """
    Для вызова model.delete() в административном интерфейсе
    """

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
