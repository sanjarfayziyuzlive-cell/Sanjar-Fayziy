from django.db import models
import markdown
import bleach

class Konspekt(models.Model):
    sarlavha = models.CharField(max_length=250)
    matn = models.TextField()
    sana = models.DateTimeField(auto_now_add=True)
    chop_etilgan = models.BooleanField(default=True)

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
        Konspekt, on_delete=models.CASCADE, related_name='layklar'
    )
    sessiya = models.CharField(max_length=100)

    class Meta:
        unique_together = ('konspekt', 'sessiya')


class Izoh(models.Model):
    konspekt = models.ForeignKey(
        Konspekt, on_delete=models.CASCADE, related_name='izohlar'
    )
    ism = models.CharField(max_length=100)
    matn = models.TextField(max_length=2000)
    sana = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sana']

    def __str__(self):
        return self.ism
