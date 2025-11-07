from django import template
from django.utils import timezone
from datetime import datetime, timedelta, time
import pytz
import logging

logger = logging.getLogger(__name__)

register = template.Library()

@register.filter
def timeuntil(value):
    """
    Вычисляет оставшееся время до истечения 30 дней с момента value (даты).
    Учитывает часовой пояс через timezone.now().
    """
    if not value:
        return "Не указано"
    
    # Преобразуем date в datetime с началом дня в текущем часовом поясе
    issue_datetime = timezone.make_aware(datetime.combine(value, time.min), timezone.get_current_timezone())
    deadline = issue_datetime + timedelta(days=30)
    now = timezone.now()
    
    # Вычисляем оставшееся время
    remaining = deadline - now
    
    if remaining.total_seconds() <= 0:
        return "Срок истёк"
    
    # Форматируем оставшееся время
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} дн., {hours} ч."
    elif hours > 0:
        return f"{hours} ч., {minutes} мин."
    else:
        return f"{minutes} мин., {seconds} сек."

@register.filter
def format_date(value):
    """
    Форматирует дату или datetime в формат DD/MM/YYYY.
    """
    if not value:
        return "Не указано"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    return value.strftime("%d/%m/%Y")

@register.filter
def to_utc(value):
    """
    Конвертирует datetime в UTC, если оно ещё не в UTC.
    """
    if not value:
        return "Не указано"
    if not timezone.is_aware(value):
        # Если время не осведомлено о часовом поясе, предполагаем, что это UTC
        value = timezone.make_aware(value, pytz.UTC)
    utc_time = value.astimezone(pytz.UTC)
    logger.debug(f"to_utc: Converted {value} to {utc_time}")
    return utc_time

@register.filter
def local_time(value):
    """
    Преобразует datetime в текущий часовой пояс клиента.
    Предполагается, что входное время в UTC (как хранится в базе).
    """
    if not value:
        return "Не указано"
    if not timezone.is_aware(value):
        # Если время не осведомлено о часовом поясе, предполагаем, что это UTC
        value = timezone.make_aware(value, pytz.UTC)
    local_tz = timezone.get_current_timezone()
    local_time = value.astimezone(local_tz)
    logger.debug(f"local_time: Converted {value} to {local_time} in {local_tz}")
    return local_time

@register.simple_tag
def get_utc_now():
    """
    Возвращает текущее время в UTC.
    """
    utc_now = timezone.now()  # Время в UTC
    logger.debug(f"get_utc_now: Returning {utc_now}")
    return utc_now

@register.filter
def format_utc_time(value):
    """
    Форматирует время в UTC, игнорируя текущий активный часовой пояс.
    """
    if not value:
        return "Не указано"
    if not timezone.is_aware(value):
        value = timezone.make_aware(value, pytz.UTC)
    utc_time = value.astimezone(pytz.UTC)
    return utc_time.strftime("%H:%M")