from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import random
from django.views.decorators.http import require_POST
from .models import Konspekt, Izoh, Layk, Korish, Bildirishnoma

def home(request):
    konspektlar = Konspekt.objects.filter(chop_etilgan=True)

    yangi_bildirishnoma_soni = 0
    if request.user.is_authenticated and request.user.is_staff:
        yangi_bildirishnoma_soni = Bildirishnoma.objects.filter(
            oqilgan=False
        ).count()

    return render(request, 'maqolalar/home.html', {
        'konspektlar': konspektlar,
        'yangi_bildirishnoma_soni': yangi_bildirishnoma_soni,
    })

def detail(request, pk):
    konspekt = get_object_or_404(Konspekt, pk=pk, chop_etilgan=True)

    if not request.session.session_key:
        request.session.create()

    _, yangi = Korish.objects.get_or_create(
        konspekt=konspekt,
        sessiya=request.session.session_key
    )

    if yangi:
        Konspekt.objects.filter(pk=pk).update(
            korishlar=F('korishlar') + 1
        )
    konspekt.refresh_from_db()

    return render(request, 'maqolalar/detail.html', {
        'konspekt': konspekt,
        'izohlar': konspekt.izohlar.all(),
    })

@require_POST
def like(request, pk):
    konspekt = get_object_or_404(Konspekt, pk=pk, chop_etilgan=True)
    if not request.session.session_key:
        request.session.create()
    sessiya = request.session.session_key
    layk, created = Layk.objects.get_or_create(
        konspekt=konspekt, sessiya=sessiya
    )
    if not created:
        layk.delete()
    else:
        Bildirishnoma.objects.create(
            konspekt=konspekt,
            turi='layk',
            xabar=f'«{konspekt.sarlavha}» maqolangizga yangi layk bosildi.'
        )
    return redirect('detail', pk=pk)

@require_POST
def comment(request, pk):
    konspekt = get_object_or_404(Konspekt, pk=pk, chop_etilgan=True)
    ism = request.POST.get('ism', '').strip()
    matn = request.POST.get('matn', '').strip()
    if ism and matn:
        Izoh.objects.create(konspekt=konspekt, ism=ism, matn=matn)
        Bildirishnoma.objects.create(
            konspekt=konspekt,
            turi='izoh',
            xabar=f'{ism} «{konspekt.sarlavha}» maqolangizga izoh yozdi.'
        )
    return redirect('detail', pk=pk)

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import markdown
import bleach

@staff_member_required
@require_POST
def preview(request):
    matn = request.POST.get('matn', '')
    html = markdown.markdown(
        matn,
        extensions=['fenced_code', 'tables']
    )
    html = bleach.clean(
        html,
        tags=[
            'p', 'br', 'strong', 'b', 'em', 'i',
            'h1', 'h2', 'h3', 'h4',
            'blockquote', 'ul', 'ol', 'li',
            'a', 'img', 'pre', 'code', 'hr',
            'table', 'thead', 'tbody', 'tr', 'th', 'td'
        ],
        attributes={
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title']
        },
        protocols=['http', 'https'],
        strip=True
    )
    return JsonResponse({'html': html})


@staff_member_required
def yozish(request):
    xato = ''

    if request.method == 'POST':
        sarlavha = request.POST.get('sarlavha', '').strip()
        muallif = request.POST.get('muallif', '').strip()
        matn = request.POST.get('matn', '').strip()

        if sarlavha and muallif and matn:
            Konspekt.objects.create(
                sarlavha=sarlavha,
                muallif=muallif,
                matn=matn,
                chop_etilgan=True
            )
            return redirect('home')
        else:
            xato = 'Sarlavha va matnni to‘ldiring.'

    return render(request, 'maqolalar/yozish.html', {
        'xato': xato,
    })


@staff_member_required
def tahrirlash(request, pk):
    konspekt = get_object_or_404(Konspekt, pk=pk)

    if request.method == 'POST':
        sarlavha = request.POST.get('sarlavha', '').strip()
        matn = request.POST.get('matn', '').strip()

        if sarlavha and matn:
            konspekt.sarlavha = sarlavha
            konspekt.matn = matn
            konspekt.save()
            return redirect('detail', pk=pk)

    return render(request, 'maqolalar/tahrirlash.html', {
        'konspekt': konspekt,
    })


@staff_member_required
@require_POST
def ochirish(request, pk):
    konspekt = get_object_or_404(Konspekt, pk=pk)
    konspekt.delete()
    return redirect('home')


from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm


def egasi_kirish(request):
    xato = ''

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            foydalanuvchi = form.get_user()

            if foydalanuvchi.is_staff:
                login(request, foydalanuvchi)
                return redirect('home')
            else:
                xato = 'Bu hisob sayt egasi uchun ruxsatga ega emas.'
        else:
            xato = 'Login yoki parol noto‘g‘ri.'
    else:
        form = AuthenticationForm()

    return render(request, 'maqolalar/egasi_kirish.html', {
        'xato': xato,
    })


@require_POST
def egasi_chiqish(request):
    logout(request)
    return redirect('home')


@staff_member_required
def bildirishnomalar(request):
    xabarlar = Bildirishnoma.objects.select_related('konspekt')
    return render(request, 'maqolalar/bildirishnomalar.html', {
        'xabarlar': xabarlar,
        'yangi_soni': xabarlar.filter(oqilgan=False).count(),
    })


@staff_member_required
@require_POST
def bildirishnoma_oqish(request, pk):
    xabar = get_object_or_404(Bildirishnoma, pk=pk)
    xabar.oqilgan = True
    xabar.save(update_fields=['oqilgan'])
    return redirect('bildirishnomalar')


# BOOK KUBOK SAHIFASI
from .models import Turnir, Ishtirokchi
from django.db import transaction


def book_kubok(request):
    xato = ''

    turnir = Turnir.objects.filter(
        faol=True
    ).order_by('-yaratilgan').first()

    if not turnir:
        return render(request, 'maqolalar/book_kubok.html', {
            'turnir': None,
            'ishtirokchilar': [],
            'duellar': [],
            'xato': 'Hozircha faol turnir mavjud emas.',
        })

    if request.method == 'POST':
        ism = request.POST.get('ism', '').strip()
        familiya = request.POST.get('familiya', '').strip()
        telefon = request.POST.get('telefon', '').strip()

        if not ism or not familiya or not telefon:
            xato = 'Barcha maydonlarni to‘ldiring.'
        else:
            telefon = ''.join(
                c for c in telefon if c.isdigit() or c == '+'
            )

            with transaction.atomic():
                turnir = Turnir.objects.select_for_update().get(
                    pk=turnir.pk
                )

                soni = turnir.ishtirokchilar.count()

                if turnir.royxat_yopilgan or turnir.qura_tashlangan:
                    xato = 'Ro‘yxatdan o‘tish yopilgan.'
                elif soni >= 16:
                    turnir.royxat_yopilgan = True
                    turnir.save(update_fields=['royxat_yopilgan'])
                    xato = '16 ta joy to‘lgan.'
                elif Ishtirokchi.objects.filter(
                    turnir=turnir, telefon=telefon
                ).exists():
                    xato = 'Bu telefon raqami bilan avval ro‘yxatdan o‘tilgan.'
                else:
                    Ishtirokchi.objects.create(
                        turnir=turnir,
                        ism=ism,
                        familiya=familiya,
                        telefon=telefon,
                    )

                    if soni + 1 >= 16:
                        turnir.royxat_yopilgan = True
                        turnir.save(update_fields=['royxat_yopilgan'])

                    return redirect('book_kubok')

    ishtirokchilar = turnir.ishtirokchilar.all()
    duellar = turnir.duellar.select_related(
        'ishtirokchi_1',
        'ishtirokchi_2',
        'golib'
    ).prefetch_related('savollar')

    return render(request, 'maqolalar/book_kubok.html', {
        'turnir': turnir,
        'ishtirokchilar': ishtirokchilar,
        'duellar': duellar,
        'xato': xato,
    })


# BOOK KUBOK SAYT ICHIDAGI BOSHQARUV PANELI
from django.contrib.admin.views.decorators import staff_member_required
from .models import Turnir, Ishtirokchi, AdabiyotSavoli, Duel, DuelSavoli, DuelNatija, DuelJavobi, DuelOvoz


@staff_member_required
def book_kubok_boshqaruv(request):
    xato = ''

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()

        if not nom:
            xato = 'Turnir nomini kiriting.'
        elif len(nom) > 150:
            xato = 'Turnir nomi 150 belgidan oshmasin.'
        else:
            Turnir.objects.filter(faol=True).update(faol=False)
            Turnir.objects.create(nom=nom, faol=True)
            return redirect('book_kubok_boshqaruv')

    xabar = request.session.pop('book_kubok_xabar', '')
    faol_savollar_soni = AdabiyotSavoli.objects.filter(faol=True).count()
    joriy_turnir = Turnir.objects.filter(faol=True).order_by('-id').first()

    ishlatilgan_savollar_soni = 0
    yangi_savollar_soni = faol_savollar_soni

    if joriy_turnir:
        ishlatilgan_ids = DuelSavoli.objects.filter(
            duel__turnir=joriy_turnir
        ).values_list('savol_id', flat=True).distinct()

        ishlatilgan_savollar_soni = len(set(ishlatilgan_ids))
        yangi_savollar_soni = AdabiyotSavoli.objects.filter(
            faol=True
        ).exclude(id__in=ishlatilgan_ids).count()

    return render(request, 'maqolalar/book_kubok_boshqaruv.html', {
        'xabar': xabar,
        'turnirlar_soni': Turnir.objects.count(),
        'ishtirokchilar_soni': Ishtirokchi.objects.count(),
        'savollar_soni': AdabiyotSavoli.objects.count(),
        'faol_savollar_soni': faol_savollar_soni,
        'ishlatilgan_savollar_soni': ishlatilgan_savollar_soni,
        'yangi_savollar_soni': yangi_savollar_soni,
        'savollar_yetarlimi': yangi_savollar_soni >= 5,
        'yetishmayotgan_savollar_soni': max(0, 5 - yangi_savollar_soni),
        'duellar_soni': Duel.objects.count(),
        'turnirlar': Turnir.objects.order_by('-yaratilgan'),
        'xato': xato,
    })


# BOOK KUBOK — SAVOL QO‘SHISH
@staff_member_required
def book_kubok_savol_qoshish(request):
    xato = ''

    if request.method == 'POST':
        savol = request.POST.get('savol', '').strip()
        a = request.POST.get('variant_a', '').strip()
        b = request.POST.get('variant_b', '').strip()
        c = request.POST.get('variant_c', '').strip()
        d = request.POST.get('variant_d', '').strip()
        togri = request.POST.get('togri_javob', '')

        if not all([savol, a, b, c, d]):
            xato = 'Barcha maydonlarni to‘ldiring.'
        elif togri not in ['A', 'B', 'C', 'D']:
            xato = 'To‘g‘ri javobni tanlang.'
        else:
            AdabiyotSavoli.objects.create(
                savol=savol,
                variant_a=a,
                variant_b=b,
                variant_c=c,
                variant_d=d,
                togri_javob=togri,
                faol=True,
            )
            return redirect('book_kubok_savollar')

    return render(request, 'maqolalar/book_kubok_savol.html', {
        'xato': xato,
    })


# BOOK KUBOK — SAYT ICHIDAN QUR'A TASHLASH
@staff_member_required
@require_POST
def book_kubok_qura_tashlash(request):
    xabar = ''

    try:
        with transaction.atomic():
            turnir = Turnir.objects.select_for_update().filter(
                faol=True
            ).order_by('-yaratilgan').first()

            if not turnir:
                xabar = "Faol turnir topilmadi."
            elif turnir.qura_tashlangan or turnir.duellar.exists():
                xabar = "Bu turnir uchun qur'a avval tashlangan."
            else:
                ishtirokchilar = list(
                    Ishtirokchi.objects.filter(turnir=turnir)
                )
                savollar = list(
                    AdabiyotSavoli.objects.filter(faol=True)
                )

                if len(ishtirokchilar) != 16:
                    xabar = "Qur'a uchun aynan 16 nafar ishtirokchi kerak."
                elif len(savollar) < 5:
                    xabar = "Kamida 5 ta faol adabiyot savoli kerak."
                else:
                    random.shuffle(ishtirokchilar)
                    tanlangan_savollar = random.sample(savollar, 5)
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

                        for tartib, savol in enumerate(
                            tanlangan_savollar, start=1
                        ):
                            DuelSavoli.objects.create(
                                duel=duel,
                                savol=savol,
                                tartib=tartib,
                            )

                    turnir.royxat_yopilgan = True
                    turnir.qura_tashlangan = True
                    turnir.save(update_fields=[
                        'royxat_yopilgan', 'qura_tashlangan'
                    ])
                    xabar = "Qur'a muvaffaqiyatli tashlandi. 8 ta duel yaratildi."

    except Exception:
        xabar = "Qur'a vaqtida xatolik yuz berdi. Ma'lumotlar saqlanmadi."

    request.session['book_kubok_xabar'] = xabar
    return redirect('book_kubok_boshqaruv')


# BOOK KUBOK — ISHTIROKCHINING DUELGA KIRISHI
def book_kubok_duel_kirish(request):
    xato = ''

    turnir = Turnir.objects.filter(
        faol=True,
        qura_tashlangan=True
    ).order_by('-yaratilgan').first()

    if request.method == 'POST':
        ism = request.POST.get('ism', '').strip()
        familiya = request.POST.get('familiya', '').strip()
        telefon = ''.join(
            c for c in request.POST.get('telefon', '')
            if c.isdigit() or c == '+'
        )

        if not turnir:
            xato = 'Hozircha faol turnir mavjud emas.'
        elif not ism or not familiya or not telefon:
            xato = 'Barcha maydonlarni to‘ldiring.'
        else:
            ishtirokchi = Ishtirokchi.objects.filter(
                turnir=turnir,
                ism__iexact=ism,
                familiya__iexact=familiya,
                telefon=telefon,
            ).first()

            if not ishtirokchi:
                xato = 'Kiritilgan ma’lumotlar ro‘yxat bilan mos kelmadi.'
            else:
                duel = Duel.objects.filter(
                    turnir=turnir,
                    yakunlangan=False,
                    ishtirokchi_1=ishtirokchi,
                ).first()

                if not duel:
                    duel = Duel.objects.filter(
                        turnir=turnir,
                        yakunlangan=False,
                        ishtirokchi_2=ishtirokchi,
                    ).first()

                if not duel:
                    xato = 'Siz uchun hozir faol duel topilmadi.'
                else:
                    request.session['book_kubok_ishtirokchi_id'] = ishtirokchi.pk
                    request.session['book_kubok_turnir_id'] = turnir.pk
                    return redirect(
                        'book_kubok_duel_test',
                        duel_id=duel.pk
                    )

    return render(request, 'maqolalar/book_kubok_duel_kirish.html', {
        'xato': xato,
        'turnir': turnir,
    })


# BOOK KUBOK — 5 SAVOLLIK DUEL TESTI
def book_kubok_duel_test(request, duel_id):
    from django.db import transaction
    from django.db.models import Sum

    ishtirokchi_id = request.session.get(
        'book_kubok_ishtirokchi_id'
    )
    turnir_id = request.session.get('book_kubok_turnir_id')

    if not ishtirokchi_id or not turnir_id:
        return redirect('book_kubok_duel_kirish')

    duel = get_object_or_404(
        Duel.objects.select_related(
            'ishtirokchi_1', 'ishtirokchi_2'
        ).prefetch_related('savollar__savol'),
        pk=duel_id,
        turnir_id=turnir_id,
    )

    ishtirokchi = get_object_or_404(
        Ishtirokchi,
        pk=ishtirokchi_id,
        turnir_id=turnir_id,
    )

    if ishtirokchi.pk not in (
        duel.ishtirokchi_1_id,
        duel.ishtirokchi_2_id
    ):
        return redirect('book_kubok_duel_kirish')

    raqib = (
        duel.ishtirokchi_2
        if duel.ishtirokchi_1_id == ishtirokchi.pk
        else duel.ishtirokchi_1
    )

    now = timezone.now()

    # Duel tugagan bo‘lsa, natijalarni ko‘rsatish
    if duel.yakunlangan:
        natijalar = duel.natijalar.select_related(
            'ishtirokchi'
        ).all()
        return render(
            request,
            'maqolalar/book_kubok_duel_test.html',
            {
                'duel': duel,
                'natijalar': natijalar,
                'yakunlangan': True,
                'ishtirokchi': ishtirokchi,
            }
        )

    # Ishtirokchining natijasini yaratish
    natija, yangi = DuelNatija.objects.get_or_create(
        duel=duel,
        ishtirokchi=ishtirokchi,
    )

    # 24 soat ichida boshlamagan ishtirokchi 0 ball bilan yakunlanadi.
    # Raqib testni tugatmaguncha duel yopilmaydi.
    if (
        not natija.test_boshlangan
        and duel.boshlash_muddati
        and now > duel.boshlash_muddati
    ):
        with transaction.atomic():
            natija.test_tugagan = now
            natija.ball = 0
            natija.sarflangan_ms = 0
            natija.save(update_fields=[
                'test_tugagan', 'ball', 'sarflangan_ms'
            ])

            boshqa_natija = DuelNatija.objects.filter(
                duel=duel,
                ishtirokchi=raqib,
                test_tugagan__isnull=False,
            ).first()

            if boshqa_natija:
                if boshqa_natija.ball > 0:
                    duel.golib = raqib
                elif boshqa_natija.ball == 0 and boshqa_natija.sarflangan_ms > 0:
                    duel.golib = raqib

                duel.yakunlangan = True
                duel.save(update_fields=['golib', 'yakunlangan'])

        return render(
            request,
            'maqolalar/book_kubok_duel_test.html',
            {
                'duel': duel,
                'yakunlangan': duel.yakunlangan,
                'kutish': not duel.yakunlangan,
                'muddat_otgan': True,
                'ishtirokchi': ishtirokchi,
            }
        )

    if natija.test_tugagan:
        return render(
            request,
            'maqolalar/book_kubok_duel_test.html',
            {
                'duel': duel,
                'kutish': True,
                'ishtirokchi': ishtirokchi,
            }
        )

    if not natija.test_boshlangan:
        natija.test_boshlangan = now
        natija.save(update_fields=['test_boshlangan'])

    savollar = list(duel.savollar.all())

    if len(savollar) != 5:
        return render(
            request,
            'maqolalar/book_kubok_duel_test.html',
            {
                'xato': 'Bu duel uchun 5 ta savol tayyorlanmagan.',
                'duel': duel,
            }
        )

    # Hali javob berilmagan birinchi savol
    javoblar = DuelJavobi.objects.filter(
        duel_savoli__duel=duel,
        ishtirokchi=ishtirokchi,
    )

    tugallanmagan = javoblar.filter(
        javob_berilgan__isnull=True
    ).first()

    if tugallanmagan:
        vaqt_otgan = (
            now - tugallanmagan.savol_boshlangan
        ).total_seconds() >= 20

        if vaqt_otgan:
            tugallanmagan.tanlangan_javob = ''
            tugallanmagan.togri = False
            tugallanmagan.javob_berilgan = now
            tugallanmagan.sarflangan_ms = 20000
            tugallanmagan.save()

            return redirect(
                'book_kubok_duel_test',
                duel_id=duel.pk
            )

    else:
        javob_berilgan_ids = set(
            javoblar.values_list('duel_savoli_id', flat=True)
        )

        keyingi = next(
            (
                savol for savol in savollar
                if savol.pk not in javob_berilgan_ids
            ),
            None
        )

        if keyingi:
            tugallanmagan = DuelJavobi.objects.create(
                duel_savoli=keyingi,
                ishtirokchi=ishtirokchi,
                savol_boshlangan=now,
            )

    # Barcha savollarga javob berilgan
    if not tugallanmagan:
        with transaction.atomic():
            natija.refresh_from_db()
            if not natija.test_tugagan:
                natija.ball = javoblar.filter(togri=True).count()
                natija.sarflangan_ms = (
                    javoblar.aggregate(jami=Sum('sarflangan_ms'))['jami']
                    or 0
                )
                natija.test_tugagan = now
                natija.save()

            boshqa_natija = DuelNatija.objects.filter(
                duel=duel,
                ishtirokchi=raqib,
                test_tugagan__isnull=False,
            ).first()

            if boshqa_natija:
                natija.refresh_from_db()

                if natija.ball > boshqa_natija.ball:
                    duel.golib = ishtirokchi
                elif natija.ball < boshqa_natija.ball:
                    duel.golib = raqib
                elif natija.sarflangan_ms < boshqa_natija.sarflangan_ms:
                    duel.golib = ishtirokchi
                elif natija.sarflangan_ms > boshqa_natija.sarflangan_ms:
                    duel.golib = raqib
                elif natija.test_boshlangan < boshqa_natija.test_boshlangan:
                    duel.golib = ishtirokchi
                elif natija.test_boshlangan > boshqa_natija.test_boshlangan:
                    duel.golib = raqib

                if duel.golib:
                    duel.yakunlangan = True
                    duel.save(update_fields=['golib', 'yakunlangan'])
                else:
                    duel.ovoz_berish_boshlangan = timezone.now()
                    duel.ovoz_berish_tugaydi = duel.ovoz_berish_boshlangan + timedelta(hours=6)
                    duel.save(update_fields=[
                        'ovoz_berish_boshlangan',
                        'ovoz_berish_tugaydi'
                    ])

        return render(
            request,
            'maqolalar/book_kubok_duel_test.html',
            {
                'duel': duel,
                'kutish': not duel.yakunlangan,
                'yakunlangan': duel.yakunlangan,
                'natijalar': duel.natijalar.select_related(
                    'ishtirokchi'
                ).all() if duel.yakunlangan else [],
                'ishtirokchi': ishtirokchi,
            }
        )

    # Javobni qabul qilish
    if request.method == 'POST':
        with transaction.atomic():
            javob = DuelJavobi.objects.select_for_update().get(
                pk=tugallanmagan.pk,
                ishtirokchi=ishtirokchi,
            )

            if javob.javob_berilgan is None:
                vaqt = (
                    timezone.now() - javob.savol_boshlangan
                ).total_seconds()

                tanlov = request.POST.get('javob', '').upper()

                if vaqt < 20 and tanlov in ['A', 'B', 'C', 'D']:
                    javob.tanlangan_javob = tanlov
                    javob.togri = (
                        tanlov == javob.duel_savoli.savol.togri_javob
                    )
                    javob.sarflangan_ms = max(
                        0, int(vaqt * 1000)
                    )
                else:
                    javob.tanlangan_javob = ''
                    javob.togri = False
                    javob.sarflangan_ms = 20000

                javob.javob_berilgan = timezone.now()
                javob.save()

        return redirect(
            'book_kubok_duel_test',
            duel_id=duel.pk
        )

    qolgan = max(
        0,
        20 - int(
            (timezone.now() - tugallanmagan.savol_boshlangan).total_seconds()
        )
    )

    return render(
        request,
        'maqolalar/book_kubok_duel_test.html',
        {
            'duel': duel,
            'savol': tugallanmagan.duel_savoli.savol,
            'savol_tartibi': tugallanmagan.duel_savoli.tartib,
            'qolgan_vaqt': qolgan,
            'ishtirokchi': ishtirokchi,
        }
    )


# BOOK KUBOK — MEHMONLAR UCHUN OVOZ BERISH
def book_kubok_ovoz_berish(request, duel_id):
    duel = get_object_or_404(
        Duel.objects.select_related(
            'ishtirokchi_1', 'ishtirokchi_2'
        ),
        pk=duel_id,
    )

    now = timezone.now()
    xato = ''
    xabar = ''

    if not duel.ovoz_berish_boshlangan:
        xato = 'Bu duelda ovoz berish hali boshlanmagan.'
    elif now >= duel.ovoz_berish_tugaydi:
        xato = 'Ovoz berish muddati tugagan.'
    elif request.method == 'POST':
        tanlov = request.POST.get('ishtirokchi')
        ruxsat_etilgan = [
            str(duel.ishtirokchi_1_id),
            str(duel.ishtirokchi_2_id),
        ]

        if tanlov not in ruxsat_etilgan:
            xato = 'Noto‘g‘ri tanlov.'
        else:
            if not request.session.session_key:
                request.session.create()

            ovoz, yaratildi = DuelOvoz.objects.get_or_create(
                duel=duel,
                sessiya_id=request.session.session_key,
                defaults={'ishtirokchi_id': int(tanlov)},
            )

            if yaratildi:
                xabar = 'Ovozingiz qabul qilindi!'
            else:
                xato = 'Siz bu duel uchun avval ovoz bergansiz.'

    ovozlar = {
        str(duel.ishtirokchi_1_id): DuelOvoz.objects.filter(
            duel=duel,
            ishtirokchi=duel.ishtirokchi_1,
        ).count(),
        str(duel.ishtirokchi_2_id): DuelOvoz.objects.filter(
            duel=duel,
            ishtirokchi=duel.ishtirokchi_2,
        ).count(),
    }

    return render(
        request,
        'maqolalar/book_kubok_ovoz_berish.html',
        {
            'duel': duel,
            'ovozlar': ovozlar,
            'ovoz_1': ovozlar[str(duel.ishtirokchi_1_id)],
            'ovoz_2': ovozlar[str(duel.ishtirokchi_2_id)],
            'xato': xato,
            'xabar': xabar,
            'ovoz_berish_tugaydi': duel.ovoz_berish_tugaydi,
            'muddat_tugagan': bool(
                duel.ovoz_berish_tugaydi
                and now >= duel.ovoz_berish_tugaydi
            ),
            'admin_teng_ovoz': bool(
                request.user.is_authenticated
                and request.user.is_staff
                and duel.ovoz_berish_tugaydi
                and now >= duel.ovoz_berish_tugaydi
                and ovozlar[str(duel.ishtirokchi_1_id)]
                    == ovozlar[str(duel.ishtirokchi_2_id)]
                and not duel.golib_id
            ),
        }
    )


# BOOK KUBOK — OVOZ BERISH NATIJASINI YAKUNLASH
@require_POST
def book_kubok_ovoz_yakunlash(request, duel_id):
    duel = get_object_or_404(Duel, pk=duel_id)

    if not duel.ovoz_berish_boshlangan:
        return redirect('book_kubok')

    if timezone.now() < duel.ovoz_berish_tugaydi:
        return redirect(
            'book_kubok_ovoz_berish',
            duel_id=duel.pk
        )

    ovoz_1 = DuelOvoz.objects.filter(
        duel=duel,
        ishtirokchi=duel.ishtirokchi_1,
    ).count()

    ovoz_2 = DuelOvoz.objects.filter(
        duel=duel,
        ishtirokchi=duel.ishtirokchi_2,
    ).count()

    if ovoz_1 > ovoz_2:
        duel.golib = duel.ishtirokchi_1
    elif ovoz_2 > ovoz_1:
        duel.golib = duel.ishtirokchi_2
    else:
        duel.golib = None

    duel.yakunlangan = bool(duel.golib_id)
    duel.save(update_fields=['golib', 'yakunlangan'])

    request.session['book_kubok_ovoz_natija'] = (
        'Ovoz berish yakunlandi. '
        f'{ovoz_1}:{ovoz_2}'
    )

    return redirect(
        'book_kubok_ovoz_berish',
        duel_id=duel.pk
    )


# BOOK KUBOK — TENG OVOZDA ADMIN G‘OLIBNI TANLAYDI
@require_POST
def book_kubok_admin_golib_tanlash(request, duel_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('egasi_kirish')

    duel = get_object_or_404(Duel, pk=duel_id)

    if not duel.ovoz_berish_tugaydi:
        return redirect('book_kubok')

    if timezone.now() < duel.ovoz_berish_tugaydi:
        return redirect('book_kubok_ovoz_berish', duel_id=duel.pk)

    ovoz_1 = DuelOvoz.objects.filter(
        duel=duel, ishtirokchi=duel.ishtirokchi_1
    ).count()
    ovoz_2 = DuelOvoz.objects.filter(
        duel=duel, ishtirokchi=duel.ishtirokchi_2
    ).count()

    if ovoz_1 != ovoz_2 or duel.golib_id:
        return redirect('book_kubok_ovoz_berish', duel_id=duel.pk)

    tanlov = request.POST.get('golib')
    if tanlov not in (
        str(duel.ishtirokchi_1_id),
        str(duel.ishtirokchi_2_id),
    ):
        return redirect('book_kubok_ovoz_berish', duel_id=duel.pk)

    duel.golib_id = int(tanlov)
    duel.yakunlangan = True
    duel.save(update_fields=['golib', 'yakunlangan'])

    return redirect('book_kubok_ovoz_berish', duel_id=duel.pk)


# BOOK KUBOK — KEYINGI BOSQICHNI AVTOMATIK YARATISH
from django.db.models.signals import post_save
from django.dispatch import receiver


def book_kubok_keyingi_bosqich(turnir_id):
    bosqichlar = {
        '1/8': '1/4',
        '1/4': '1/2',
        '1/2': 'final',
    }

    with transaction.atomic():
        turnir = Turnir.objects.select_for_update().get(
            pk=turnir_id
        )

        oxirgi_duel = Duel.objects.filter(
            turnir=turnir
        ).order_by('-id').first()

        if not oxirgi_duel:
            return

        yangi_bosqich = bosqichlar.get(oxirgi_duel.bosqich)

        if not yangi_bosqich:
            return

        duellar = list(
            Duel.objects.select_for_update().filter(
                turnir=turnir,
                bosqich=oxirgi_duel.bosqich,
            ).order_by('raqam')
        )

        if not duellar or any(
            not duel.yakunlangan or not duel.golib_id
            for duel in duellar
        ):
            return

        if Duel.objects.filter(
            turnir=turnir,
            bosqich=yangi_bosqich,
        ).exists():
            return

        goliblar = [duel.golib for duel in duellar]

        if len(goliblar) < 2 or len(goliblar) % 2:
            return

        # Shu turnirning oldingi bosqichlarida ishlatilgan savollar
        # keyingi bosqichlarda qayta tanlanmaydi.
        ishlatilgan_ids = DuelSavoli.objects.filter(
            duel__turnir=turnir
        ).values_list('savol_id', flat=True)

        savollar = list(
            AdabiyotSavoli.objects.filter(
                faol=True
            ).exclude(
                id__in=ishlatilgan_ids
            ).order_by('?')[:5]
        )

        # Kamida 5 ta yangi faol savol bo‘lmasa,
        # keyingi bosqich yaratilmaydi.
        if len(savollar) < 5:
            return

        muddat = timezone.now() + timedelta(hours=24)

        for i in range(0, len(goliblar), 2):
            raqam = i // 2 + 1

            yangi_duel = Duel.objects.create(
                turnir=turnir,
                bosqich=yangi_bosqich,
                raqam=raqam,
                ishtirokchi_1=goliblar[i],
                ishtirokchi_2=goliblar[i + 1],
                boshlash_muddati=muddat,
            )

            for tartib, savol in enumerate(savollar, start=1):
                DuelSavoli.objects.create(
                    duel=yangi_duel,
                    savol=savol,
                    tartib=tartib,
                )


@receiver(post_save, sender=Duel)
def book_kubok_duel_yakunlanganda(sender, instance, **kwargs):
    if instance.yakunlangan and instance.golib_id:
        book_kubok_keyingi_bosqich(instance.turnir_id)


# BOOK KUBOK — SAVOLLAR BAZASI
def book_kubok_savollar(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('egasi_kirish')

    savollar = AdabiyotSavoli.objects.all().order_by('-id')

    return render(
        request,
        'maqolalar/book_kubok_savollar.html',
        {'savollar': savollar}
    )


# BOOK KUBOK — SAVOLNI TAHRIRLASH
def book_kubok_savol_tahrirlash(request, savol_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('egasi_kirish')

    savol = get_object_or_404(AdabiyotSavoli, pk=savol_id)

    if request.method == 'POST':
        savol.savol = request.POST.get('savol', '').strip()
        savol.variant_a = request.POST.get('variant_a', '').strip()
        savol.variant_b = request.POST.get('variant_b', '').strip()
        savol.variant_c = request.POST.get('variant_c', '').strip()
        savol.variant_d = request.POST.get('variant_d', '').strip()
        javob = request.POST.get('togri_javob', '').upper()

        if (
            all([
                savol.savol,
                savol.variant_a,
                savol.variant_b,
                savol.variant_c,
                savol.variant_d,
            ])
            and javob in ['A', 'B', 'C', 'D']
        ):
            savol.togri_javob = javob
            savol.save()
            return redirect('book_kubok_savollar')

    return render(
        request,
        'maqolalar/book_kubok_savol_tahrirlash.html',
        {'savol': savol}
    )


# BOOK KUBOK — SAVOLNI O‘CHIRISH YOKI FAOLSIZLANTIRISH
@require_POST
def book_kubok_savol_ochirish(request, savol_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('egasi_kirish')

    savol = get_object_or_404(AdabiyotSavoli, pk=savol_id)

    if DuelSavoli.objects.filter(savol=savol).exists():
        savol.faol = False
        savol.save(update_fields=['faol'])
    else:
        savol.delete()

    return redirect('book_kubok_savollar')


# BOOK KUBOK — SAVOLNI FAOLLASHTIRISH
@require_POST
def book_kubok_savol_faollashtirish(request, savol_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('egasi_kirish')

    savol = get_object_or_404(AdabiyotSavoli, pk=savol_id)
    savol.faol = not savol.faol
    savol.save(update_fields=['faol'])

    return redirect('book_kubok_savollar')
