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


# BOOK KUBOK ADMIN BOSHQARUVI

from .models import (
    Turnir,
    Ishtirokchi,
    AdabiyotSavoli,
    Duel,
    DuelSavoli,
    DuelNatija,
    DuelJavobi,
)

@admin.register(Turnir)
class TurnirAdmin(admin.ModelAdmin):
    list_display = ('nom', 'faol', 'royxat_yopilgan', 'qura_tashlangan', 'yaratilgan')


@admin.register(Ishtirokchi)
class IshtirokchiAdmin(admin.ModelAdmin):
    list_display = ('ism', 'familiya', 'telefon', 'turnir')
    search_fields = ('ism', 'familiya', 'telefon')


@admin.register(AdabiyotSavoli)
class AdabiyotSavoliAdmin(admin.ModelAdmin):
    list_display = ('savol', 'togri_javob', 'faol')
    list_filter = ('faol', 'togri_javob')
    search_fields = ('savol',)


@admin.register(Duel)
class DuelAdmin(admin.ModelAdmin):
    list_display = ('turnir', 'bosqich', 'raqam', 'ishtirokchi_1', 'ishtirokchi_2', 'golib', 'yakunlangan')
    list_filter = ('bosqich', 'yakunlangan')


admin.site.register(DuelSavoli)
admin.site.register(DuelNatija)
admin.site.register(DuelJavobi)


# BOOK KUBOK — OCHIQ QUR'A

import random
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.contrib import messages


@admin.action(description="Book Kubok: Qur'a tashlash")
def qura_tashlash(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.error(request, "Faqat bitta turnirni tanlang.")
        return

    with transaction.atomic():
        turnir = Turnir.objects.select_for_update().get(
            pk=queryset.first().pk
        )

        ishtirokchilar = list(
            turnir.ishtirokchilar.all()
        )

        savollar = list(
            AdabiyotSavoli.objects.filter(faol=True)
        )

        if not turnir.faol:
            messages.error(request, "Bu turnir faol emas.")
            return

        if turnir.qura_tashlangan or turnir.duellar.exists():
            messages.error(request, "Bu turnir uchun qur'a avval tashlangan.")
            return

        if len(ishtirokchilar) != 16:
            messages.error(
                request,
                f"Qur'a uchun 16 kishi kerak. Hozir {len(ishtirokchilar)} kishi bor."
            )
            return

        if len(savollar) < 5:
            messages.error(
                request,
                "Savollar bazasida kamida 5 ta faol savol bo‘lishi kerak."
            )
            return

        random.shuffle(ishtirokchilar)
        muddat = timezone.now() + timedelta(hours=24)

        for i in range(8):
            duel = Duel.objects.create(
                turnir=turnir,
                bosqich='1/8',
                raqam=i + 1,
                ishtirokchi_1=ishtirokchilar[i * 2],
                ishtirokchi_2=ishtirokchilar[i * 2 + 1],
                boshlash_muddati=muddat,
            )

            tanlangan_savollar = random.sample(savollar, 5)

            for tartib, savol in enumerate(tanlangan_savollar, start=1):
                DuelSavoli.objects.create(
                    duel=duel,
                    savol=savol,
                    tartib=tartib,
                )

        turnir.royxat_yopilgan = True
        turnir.qura_tashlangan = True
        turnir.save(
            update_fields=['royxat_yopilgan', 'qura_tashlangan']
        )

    messages.success(
        request,
        "Qur'a muvaffaqiyatli tashlandi! 8 ta duel yaratildi."
    )


TurnirAdmin.actions = [qura_tashlash]
