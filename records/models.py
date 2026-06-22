from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """
    Одна из 8 категорий мировых автомобильных рекордов.
    Например: «Самая быстрая машина», «Самая дорогая машина» и т.д.
    """

    name = models.CharField('Название', max_length=120, unique=True)
    slug = models.SlugField('Слаг', max_length=140, unique=True, blank=True)
    description = models.TextField('Описание', blank=True)
    icon = models.CharField(
        'Иконка (emoji или css-класс)', max_length=50, blank=True,
        help_text='Можно указать emoji (например 🏎️) — используется на карточках главной страницы.'
    )
    unit_label = models.CharField(
        'Подпись единицы измерения рекорда', max_length=50, blank=True,
        help_text='Например: км/ч, $, кг, баллы. Используется в карточках и таблицах.'
    )
    order = models.PositiveIntegerField('Порядок отображения', default=0)

    class Meta:
        verbose_name = 'Категория рекорда'
        verbose_name_plural = 'Категории рекордов'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=False) or slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('records:category_detail', kwargs={'slug': self.slug})

    @property
    def current_record(self):
        """Текущий действующий (последний по дате) рекорд в категории."""
        return self.records.select_related('car').order_by('-date_set').first()


class Car(models.Model):
    """Автомобиль — объект, который может удерживать один или несколько рекордов."""

    FUEL_PETROL = 'petrol'
    FUEL_DIESEL = 'diesel'
    FUEL_ELECTRIC = 'electric'
    FUEL_HYBRID = 'hybrid'
    FUEL_HYDROGEN = 'hydrogen'
    FUEL_OTHER = 'other'
    FUEL_CHOICES = [
        (FUEL_PETROL, 'Бензин'),
        (FUEL_DIESEL, 'Дизель'),
        (FUEL_ELECTRIC, 'Электричество'),
        (FUEL_HYBRID, 'Гибрид'),
        (FUEL_HYDROGEN, 'Водород'),
        (FUEL_OTHER, 'Другое'),
    ]

    name = models.CharField('Название модели', max_length=150)
    manufacturer = models.CharField('Производитель', max_length=100)
    year = models.PositiveIntegerField('Год выпуска')
    slug = models.SlugField('Слаг', max_length=200, unique=True, blank=True)

    photo = models.ImageField('Фото', upload_to='cars/', blank=True, null=True)
    description = models.TextField('Описание', blank=True)

    record_category = models.ForeignKey(
        Category, verbose_name='Основная рекордная категория',
        related_name='primary_cars', on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text='Категория, в которой эта модель в первую очередь известна.'
    )

    # Технические характеристики — используются таблицей, фильтрами и алгоритмом
    # "Идеального сбалансированного автомобиля".
    top_speed_kmh = models.DecimalField('Макс. скорость (км/ч)', max_digits=7, decimal_places=1, null=True, blank=True)
    power_hp = models.PositiveIntegerField('Мощность (л.с.)', null=True, blank=True)
    price_usd = models.DecimalField('Цена ($)', max_digits=14, decimal_places=2, null=True, blank=True)
    weight_kg = models.PositiveIntegerField('Масса (кг)', null=True, blank=True)
    length_mm = models.PositiveIntegerField('Длина (мм)', null=True, blank=True)
    acceleration_0_100 = models.DecimalField(
        'Разгон 0-100 км/ч (сек)', max_digits=4, decimal_places=2, null=True, blank=True
    )
    reliability_score = models.DecimalField(
        'Индекс надёжности (0-100)', max_digits=5, decimal_places=1, null=True, blank=True,
        help_text='Экспертная или агрегированная оценка надёжности.'
    )
    eco_score = models.DecimalField(
        'Индекс экологичности (0-100)', max_digits=5, decimal_places=1, null=True, blank=True,
        help_text='Чем выше — тем чище технология/меньше выбросов.'
    )
    tech_score = models.DecimalField(
        'Индекс технологичности (0-100)', max_digits=5, decimal_places=1, null=True, blank=True,
        help_text='Оценка инновационности: автопилот, материалы, электроника.'
    )
    fuel_type = models.CharField('Тип топлива', max_length=20, choices=FUEL_CHOICES, default=FUEL_PETROL)

    is_featured = models.BooleanField('Показывать на главной', default=False)
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-year', 'manufacturer']
        indexes = [
            models.Index(fields=['manufacturer']),
            models.Index(fields=['year']),
        ]

    def __str__(self):
        return f'{self.manufacturer} {self.name} ({self.year})'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f'{self.manufacturer}-{self.name}-{self.year}')
            self.slug = base or f'car-{self.year}'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('records:car_detail', kwargs={'slug': self.slug})

    @property
    def balance_score(self):
        """
        Взвешенный балл "сбалансированности" автомобиля по шести нормализованным
        параметрам. Используется фичей "Идеальный сбалансированный автомобиль".
        Возвращает float от 0 до 100 (или None, если данных недостаточно).
        """
        from .scoring import compute_balance_score
        return compute_balance_score(self)


class Record(models.Model):
    """Конкретный мировой рекорд, удерживаемый автомобилем в рамках категории."""

    car = models.ForeignKey(Car, verbose_name='Автомобиль', related_name='records', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='records', on_delete=models.CASCADE)

    value = models.DecimalField('Значение рекорда', max_digits=14, decimal_places=2)
    unit = models.CharField('Единица измерения', max_length=30, help_text='км/ч, $, л.с., кг и т.д.')

    date_set = models.DateField('Дата установления рекорда')
    source = models.CharField(
        'Источник', max_length=300,
        help_text='Название организации или ссылка, подтверждающая рекорд (например, Guinness World Records).'
    )
    notes = models.TextField('Примечания', blank=True)
    is_current = models.BooleanField(
        'Действующий рекорд', default=True,
        help_text='Снимите галочку, если рекорд побит и больше не актуален.'
    )

    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'Рекорд'
        verbose_name_plural = 'Рекорды'
        ordering = ['-date_set']

    def __str__(self):
        return f'{self.category.name}: {self.car} — {self.value} {self.unit}'


class Comparison(models.Model):
    """Сохранённое сравнение двух или более автомобилей."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Пользователь', related_name='comparisons',
        on_delete=models.CASCADE, null=True, blank=True,
        help_text='Может быть пустым для анонимных сравнений.'
    )
    cars = models.ManyToManyField(Car, verbose_name='Автомобили', related_name='comparisons')
    session_key = models.CharField('Ключ сессии', max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Сравнение'
        verbose_name_plural = 'Сравнения'
        ordering = ['-created_at']

    def __str__(self):
        names = ', '.join(str(c) for c in self.cars.all()[:3])
        return f'Сравнение #{self.pk}: {names}'


class Favorite(models.Model):
    """Автомобиль, добавленный пользователем в избранное."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Пользователь',
        related_name='favorites', on_delete=models.CASCADE
    )
    car = models.ForeignKey(Car, verbose_name='Автомобиль', related_name='favorited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'car')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} ♥ {self.car}'
