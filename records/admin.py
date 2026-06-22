from django.contrib import admin
from django.utils.html import format_html

from .models import Car, Category, Comparison, Favorite, Record


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'unit_label', 'order', 'cars_count')
    list_editable = ('order',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    @admin.display(description='Кол-во авто')
    def cars_count(self, obj):
        return obj.primary_cars.count()


class RecordInline(admin.TabularInline):
    model = Record
    extra = 1
    fields = ('category', 'value', 'unit', 'date_set', 'source', 'is_current')


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail', 'name', 'manufacturer', 'year', 'record_category',
        'top_speed_kmh', 'power_hp', 'price_display', 'is_featured', 'balance_score_display',
    )
    list_display_links = ('name',)
    list_editable = ('is_featured',)
    list_filter = ('record_category', 'fuel_type', 'is_featured', 'year')
    search_fields = ('name', 'manufacturer', 'description')
    prepopulated_fields = {'slug': ('manufacturer', 'name', 'year')}
    date_hierarchy = 'created_at'
    inlines = [RecordInline]
    readonly_fields = ('created_at', 'updated_at', 'balance_score_display')
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'manufacturer', 'year', 'slug', 'photo', 'description', 'record_category', 'is_featured')
        }),
        ('Технические характеристики', {
            'fields': (
                'top_speed_kmh', 'power_hp', 'acceleration_0_100', 'price_usd',
                'weight_kg', 'length_mm', 'fuel_type',
            )
        }),
        ('Индексы для алгоритма сбалансированности', {
            'fields': ('reliability_score', 'eco_score', 'tech_score', 'balance_score_display'),
            'description': 'Эти три индекса (0-100) и характеристики выше используются в фиче '
                            '«Идеальный сбалансированный автомобиль».',
        }),
        ('Системное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Фото')
    def thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;object-fit:cover;" />', obj.photo.url)
        return '—'

    @admin.display(description='Цена')
    def price_display(self, obj):
        if obj.price_usd is None:
            return '—'
        return f'${obj.price_usd:,.0f}'

    @admin.display(description='Балл сбалансированности')
    def balance_score_display(self, obj):
        score = obj.balance_score
        return f'{score} / 100' if score is not None else 'недостаточно данных'


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('category', 'car', 'value', 'unit', 'date_set', 'is_current', 'source')
    list_filter = ('category', 'is_current', 'date_set')
    search_fields = ('car__name', 'car__manufacturer', 'source')
    autocomplete_fields = ('car',)
    date_hierarchy = 'date_set'
    list_editable = ('is_current',)


@admin.register(Comparison)
class ComparisonAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'cars_list', 'created_at')
    list_filter = ('created_at',)
    filter_horizontal = ('cars',)

    @admin.display(description='Автомобили')
    def cars_list(self, obj):
        return ', '.join(str(c) for c in obj.cars.all())


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'car__name', 'car__manufacturer')


# Для работы autocomplete_fields в RecordAdmin
admin.site.empty_value_display = '—'
admin.site.site_header = 'Automotive Records — Администрирование'
admin.site.site_title = 'Automotive Records Admin'
admin.site.index_title = 'Панель управления контентом'
