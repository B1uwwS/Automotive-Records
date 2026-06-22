"""
Алгоритм "Идеальный сбалансированный автомобиль".

Считает взвешенный балл (0-100) по шести нормализованным параметрам:
скорость, мощность, разгон, надёжность, экологичность, технологичность.
Цена и масса используются как штрафующие/смягчающие факторы не напрямую
в этой версии — упор сделан на сравнимые "положительные" характеристики,
чтобы избежать перекоса в сторону единственного супер-дорогого гиперкара.

Нормализация: для каждого параметра у всех автомобилей с непустым значением
вычисляется (value - min) / (max - min) -> [0, 1]. Для "разгона 0-100"
формула инвертируется, так как меньшее значение лучше.
"""

from decimal import Decimal

# Веса параметров. Сумма весов = 1.0
WEIGHTS = {
    'top_speed_kmh': Decimal('0.20'),
    'power_hp': Decimal('0.15'),
    'acceleration_0_100': Decimal('0.15'),  # инвертируется (меньше = лучше)
    'reliability_score': Decimal('0.20'),
    'eco_score': Decimal('0.15'),
    'tech_score': Decimal('0.15'),
}

INVERTED_FIELDS = {'acceleration_0_100'}


def _to_decimal(value):
    if value is None:
        return None
    return Decimal(str(value))


def _normalize(value, min_value, max_value, inverted=False):
    if value is None or min_value is None or max_value is None:
        return None
    if max_value == min_value:
        return Decimal('1.0')
    normalized = (value - min_value) / (max_value - min_value)
    if inverted:
        normalized = Decimal('1.0') - normalized
    return normalized


def get_field_bounds(queryset, field_name):
    """Возвращает (min, max) для поля по переданному queryset автомобилей."""
    values = [
        getattr(car, field_name) for car in queryset
        if getattr(car, field_name) is not None
    ]
    if not values:
        return None, None
    return min(values), max(values)


def compute_balance_score(car, bounds=None):
    """
    Считает балл сбалансированности для одного автомобиля.

    :param car: экземпляр Car
    :param bounds: опциональный словарь {field_name: (min, max)} для расчёта
                   относительно всего парка автомобилей. Если не передан,
                   используется упрощённая абсолютная шкала (см. ABSOLUTE_BOUNDS).
    """
    bounds = bounds or ABSOLUTE_BOUNDS

    total_weight = Decimal('0')
    weighted_sum = Decimal('0')

    for field_name, weight in WEIGHTS.items():
        raw_value = getattr(car, field_name)
        value = _to_decimal(raw_value)
        if value is None:
            continue

        min_value, max_value = bounds.get(field_name, (None, None))
        min_value = _to_decimal(min_value)
        max_value = _to_decimal(max_value)

        normalized = _normalize(value, min_value, max_value, inverted=field_name in INVERTED_FIELDS)
        if normalized is None:
            continue

        weighted_sum += normalized * weight
        total_weight += weight

    if total_weight == 0:
        return None

    # Перенормировка на случай отсутствующих параметров, чтобы балл
    # оставался сравним в шкале 0-100 даже при частично заполненных карточках.
    score = (weighted_sum / total_weight) * Decimal('100')
    return round(float(score), 1)


def compute_balance_scores_for_queryset(queryset):
    """
    Считает балл сбалансированности относительно реального разброса значений
    в переданном наборе автомобилей (динамические границы), а не абсолютной шкалы.
    Возвращает список (car, score) отсортированный по убыванию score.
    """
    cars = list(queryset)
    bounds = {
        field_name: get_field_bounds(cars, field_name)
        for field_name in WEIGHTS
    }

    scored = []
    for car in cars:
        score = compute_balance_score(car, bounds=bounds)
        if score is not None:
            scored.append((car, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


# Абсолютные ориентировочные границы шкалы — используются как запасной вариант
# для balance_score у одиночного автомобиля (например, на странице деталей),
# когда нет смысла пересчитывать относительно всего парка.
ABSOLUTE_BOUNDS = {
    'top_speed_kmh': (Decimal('80'), Decimal('500')),
    'power_hp': (Decimal('70'), Decimal('1600')),
    'acceleration_0_100': (Decimal('1.5'), Decimal('12')),
    'reliability_score': (Decimal('0'), Decimal('100')),
    'eco_score': (Decimal('0'), Decimal('100')),
    'tech_score': (Decimal('0'), Decimal('100')),
}
