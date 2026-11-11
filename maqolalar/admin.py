from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import Konspekt, Izoh, Layk

@admin.register(Konspekt)
class KonspektAdmin(admin.ModelAdmin):
    list_display = ('sarlavha', 'sana', 'chop_etilgan')
    list_filter = ('chop_etilgan',)
    search_fields = ('sarlavha', 'matn')
    list_editable = ('chop_etilgan',)

    class Media:
        js = ('maqolalar/js/konspekt_preview.js',)

    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(attrs={
                'rows': 25,
                'style': 'width:100%; font-family:monospace;'
            })
        }
    }

    fieldsets = (
        ('Konspekt maʼlumotlari', {
            'fields': ('sarlavha', 'matn', 'chop_etilgan'),
        }),
    )

admin.site.register(Izoh)
admin.site.register(Layk)
