from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def minutes_since(value):
    if value is None:
        return None
    now = timezone.now()
    difference = now - value
    return int(difference.total_seconds() / 60)

@register.filter
def is_less_than_five(value):
    if value is None:
        return None
    return value < 5