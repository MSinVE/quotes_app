# quotes_app/management/commands/clean_view_history.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from quotes_app.models import ViewHistory

class Command(BaseCommand):
    help = 'Удаляет записи ViewHistory старше 30 дней'

    def handle(self, *args, **kwargs):
        threshold = timezone.now() - timedelta(days=30)
        deleted_count, _ = ViewHistory.objects.filter(viewed_at__lt=threshold).delete()
        self.stdout.write(self.style.SUCCESS(f'Удалено {deleted_count} старых записей ViewHistory'))