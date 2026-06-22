from django import template

register = template.Library()


@register.filter
def usd(value):
    """Форматирует число как $1,234,567."""
    if value in (None, ''):
        return '—'
    try:
        return f'${float(value):,.0f}'
    except (TypeError, ValueError):
        return value


@register.filter
def percent_of(value, max_value):
    """Возвращает value как процент от max_value (для ширины progress-bar в CSS)."""
    try:
        value = float(value)
        max_value = float(max_value)
        if max_value <= 0:
            return 0
        return min(100, max(0, round((value / max_value) * 100)))
    except (TypeError, ValueError):
        return 0


@register.filter
def dash_if_none(value):
    return value if value not in (None, '') else '—'


@register.filter
def get_item(container, key):
    """Достаёт значение по ключу из словаря или QueryDict в шаблоне."""
    if container is None:
        return ''
    try:
        return container.get(key, '')
    except AttributeError:
        return ''


@register.filter
def in_list(value, the_list):
    """Безопасная проверка `value in the_list`, не падает если the_list пуст/None."""
    if not the_list:
        return False
    return value in the_list
