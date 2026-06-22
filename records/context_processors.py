from .models import Category


def categories_processor(request):
    """Делает список категорий доступным во всех шаблонах (для меню/футера)."""
    return {
        'nav_categories': Category.objects.order_by('order', 'name'),
    }
