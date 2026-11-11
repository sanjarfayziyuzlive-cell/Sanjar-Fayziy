from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Konspekt, Izoh, Layk

def home(request):
    konspektlar = Konspekt.objects.filter(chop_etilgan=True)
    return render(request, 'maqolalar/home.html', {
        'konspektlar': konspektlar,
    })

def detail(request, pk):
    konspekt = get_object_or_404(Konspekt, pk=pk, chop_etilgan=True)
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
    return redirect('detail', pk=pk)

@require_POST
def comment(request, pk):
    konspekt = get_object_or_404(Konspekt, pk=pk, chop_etilgan=True)
    ism = request.POST.get('ism', '').strip()
    matn = request.POST.get('matn', '').strip()
    if ism and matn:
        Izoh.objects.create(konspekt=konspekt, ism=ism, matn=matn)
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
        matn = request.POST.get('matn', '').strip()

        if sarlavha and matn:
            Konspekt.objects.create(
                sarlavha=sarlavha,
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
