from django.utils import timezone


def current_datetime(request):
    """Добавляет текущую дату и время в контекст всех шаблонов"""
    now = timezone.now()
    return {
        'current_date': now.date(),
        'current_time': now,
    }
