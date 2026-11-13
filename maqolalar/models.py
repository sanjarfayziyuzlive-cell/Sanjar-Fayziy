from django.db import models
import markdown
import bleach


class Konspekt(models.Model):
    sarlavha = models.CharField(max_length=250)
    muallif = models.CharField(
        max_length=200,
        default='Muallif ko‘rsatilmagan'
    )
    matn = models.TextField()
    sana = models.DateTimeField(auto_now_add=True)
    chop_etilgan = models.BooleanField(default=True)
    korishlar = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-sana']

    def __str__(self):
        return self.sarlavha

    @property
    def html_matn(self):
        html = markdown.markdown(
            self.matn,
            extensions=['fenced_code', 'tables']
        )
        return bleach.clean(
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
                'img': ['src', 'alt', 'title'],
            },
            protocols=['http', 'https'],
            strip=True
        )


class Layk(models.Model):
    konspekt = models.ForeignKey(
        Konspekt,
        on_delete=models.CASCADE,
        related_name='layklar'
    )
    sessiya = models.CharField(max_length=100)

    class Meta:
        unique_together = ('konspekt', 'sessiya')


class Izoh(models.Model):
    konspekt = models.ForeignKey(
        Konspekt,
        on_delete=models.CASCADE,
        related_name='izohlar'
    )
    ism = models.CharField(max_length=100)
    matn = models.TextField(max_length=2000)
    sana = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sana']

    def __str__(self):
        return self.ism


class Korish(models.Model):
    konspekt = models.ForeignKey(
        Konspekt,
        on_delete=models.CASCADE,
        related_name='korishlar_tarixi'
    )
    sessiya = models.CharField(max_length=100)

    class Meta:
        unique_together = ('konspekt', 'sessiya')


class Bildirishnoma(models.Model):
    TURLAR = [
        ('layk', 'Layk'),
        ('izoh', 'Izoh'),
    ]

    konspekt = models.ForeignKey(
        Konspekt,
        on_delete=models.CASCADE,
        related_name='bildirishnomalar'
    )
    turi = models.CharField(max_length=10, choices=TURLAR)
    xabar = models.CharField(max_length=300)
    oqilgan = models.BooleanField(default=False)
    sana = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sana']

    def __str__(self):
        return self.xabar


# ==============================
# BOOK KUBOK TURNIR TIZIMI
# ==============================

class Turnir(models.Model):
    nom = models.CharField(max_length=150, default='Book Kubok')
    faol = models.BooleanField(default=True)
    royxat_yopilgan = models.BooleanField(default=False)
    qura_tashlangan = models.BooleanField(default=False)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class Ishtirokchi(models.Model):
    turnir = models.ForeignKey(
        Turnir, on_delete=models.CASCADE, related_name='ishtirokchilar'
    )
    ism = models.CharField(max_length=100)
    familiya = models.CharField(max_length=100)
    telefon = models.CharField(max_length=20)
    sana = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['turnir', 'telefon'],
                name='book_kubok_unique_telefon'
            )
        ]

    def __str__(self):
        return f'{self.ism} {self.familiya}'


class AdabiyotSavoli(models.Model):
    savol = models.TextField()
    variant_a = models.CharField(max_length=500)
    variant_b = models.CharField(max_length=500)
    variant_c = models.CharField(max_length=500)
    variant_d = models.CharField(max_length=500)

    TOGRI_VARIANTLAR = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    togri_javob = models.CharField(
        max_length=1,
        choices=TOGRI_VARIANTLAR
    )
    faol = models.BooleanField(default=True)
    sana = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.savol[:80]


class Duel(models.Model):
    BOSQICHLAR = [
        ('1/8', '1/8 final'),
        ('1/4', 'Chorak final'),
        ('1/2', 'Yarim final'),
        ('final', 'Final'),
    ]

    turnir = models.ForeignKey(
        Turnir, on_delete=models.CASCADE, related_name='duellar'
    )
    bosqich = models.CharField(max_length=10, choices=BOSQICHLAR)
    raqam = models.PositiveSmallIntegerField()

    ishtirokchi_1 = models.ForeignKey(
        Ishtirokchi,
        on_delete=models.PROTECT,
        related_name='duel_1'
    )
    ishtirokchi_2 = models.ForeignKey(
        Ishtirokchi,
        on_delete=models.PROTECT,
        related_name='duel_2'
    )

    boshlash_muddati = models.DateTimeField(null=True, blank=True)
    golib = models.ForeignKey(
        Ishtirokchi,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='golib_duellar'
    )
    yakunlangan = models.BooleanField(default=False)
    ovoz_berish_boshlangan = models.DateTimeField(null=True, blank=True)
    ovoz_berish_tugaydi = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['bosqich', 'raqam']

    def __str__(self):
        return f'{self.bosqich} — Duel {self.raqam}'


class DuelSavoli(models.Model):
    duel = models.ForeignKey(
        Duel, on_delete=models.CASCADE, related_name='savollar'
    )
    savol = models.ForeignKey(
        AdabiyotSavoli, on_delete=models.PROTECT
    )
    tartib = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['tartib']
        constraints = [
            models.UniqueConstraint(
                fields=['duel', 'tartib'],
                name='book_kubok_unique_duel_tartib'
            ),
            models.UniqueConstraint(
                fields=['duel', 'savol'],
                name='book_kubok_unique_duel_savol'
            ),
        ]

    def __str__(self):
        return f'{self.duel} — {self.tartib}-savol'


class DuelNatija(models.Model):
    duel = models.ForeignKey(
        Duel, on_delete=models.CASCADE, related_name='natijalar'
    )
    ishtirokchi = models.ForeignKey(
        Ishtirokchi, on_delete=models.PROTECT
    )
    test_boshlangan = models.DateTimeField(null=True, blank=True)
    test_tugagan = models.DateTimeField(null=True, blank=True)
    ball = models.PositiveSmallIntegerField(default=0)
    sarflangan_ms = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['duel', 'ishtirokchi'],
                name='book_kubok_unique_duel_natija'
            )
        ]

    def __str__(self):
        return f'{self.ishtirokchi} — {self.ball} ball'


class DuelJavobi(models.Model):
    VARIANTLAR = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    duel_savoli = models.ForeignKey(
        DuelSavoli, on_delete=models.CASCADE, related_name='javoblar'
    )
    ishtirokchi = models.ForeignKey(
        Ishtirokchi, on_delete=models.PROTECT
    )
    tanlangan_javob = models.CharField(
        max_length=1, choices=VARIANTLAR, blank=True
    )
    savol_boshlangan = models.DateTimeField(null=True, blank=True)
    javob_berilgan = models.DateTimeField(null=True, blank=True)
    togri = models.BooleanField(default=False)
    sarflangan_ms = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['duel_savoli', 'ishtirokchi'],
                name='book_kubok_unique_savol_javob'
            )
        ]

    def __str__(self):
        return f'{self.ishtirokchi} — {self.duel_savoli}'


class DuelOvoz(models.Model):
    duel = models.ForeignKey(
        Duel, on_delete=models.CASCADE, related_name='ovozlar'
    )
    ishtirokchi = models.ForeignKey(
        Ishtirokchi, on_delete=models.PROTECT, related_name='duel_ovozlari'
    )
    sessiya_id = models.CharField(max_length=64)
    berilgan_vaqt = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['duel', 'sessiya_id'],
                name='book_kubok_unique_duel_ovoz_sessiya'
            )
        ]

    def __str__(self):
        return f'{self.duel} — {self.ishtirokchi}'
