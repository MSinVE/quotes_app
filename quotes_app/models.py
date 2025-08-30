from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Quote(models.Model):
    text = models.TextField(unique=True)  # Цитата, уникальная
    source = models.CharField(max_length=255)  # Источник (фильм, книга)
    weight = models.PositiveIntegerField(default=1)  # Вес для случайного выбора
    likes = models.ManyToManyField(User, related_name='liked_quotes', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_quotes', blank=True)
    views = models.IntegerField(default=0)

    def clean(self):
        # Проверка на лимит: не больше 3 цитат на источник
        if Quote.objects.filter(source=self.source).count() >= 3 and not self.pk:
            raise ValidationError(f"У источника '{self.source}' уже 3 цитаты. Нельзя добавить больше.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.text[:50]}... ({self.source})"
    
class ViewHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'quote'), ('session_key', 'quote')]

