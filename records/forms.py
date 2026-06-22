from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Car, Category


class CarFilterForm(forms.Form):
    """Форма поиска и фильтрации на странице со всеми рекордами/автомобилями."""

    SORT_CHOICES = [
        ('-year', 'Год (новые → старые)'),
        ('year', 'Год (старые → новые)'),
        ('manufacturer', 'Производитель (А-Я)'),
        ('-top_speed_kmh', 'Скорость (макс. → мин.)'),
        ('-power_hp', 'Мощность (макс. → мин.)'),
        ('-price_usd', 'Цена (макс. → мин.)'),
        ('price_usd', 'Цена (мин. → макс.)'),
        ('-balance', 'Балл сбалансированности'),
    ]

    q = forms.CharField(
        label='Поиск', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Название, производитель, год...'})
    )
    category = forms.ModelChoiceField(
        label='Категория', queryset=Category.objects.all(), required=False, empty_label='Все категории'
    )
    manufacturer = forms.CharField(label='Производитель', required=False)
    year_from = forms.IntegerField(label='Год от', required=False)
    year_to = forms.IntegerField(label='Год до', required=False)
    fuel_type = forms.ChoiceField(
        label='Топливо', required=False,
        choices=[('', 'Любое')] + list(Car.FUEL_CHOICES)
    )
    sort = forms.ChoiceField(label='Сортировка', choices=SORT_CHOICES, required=False)


class ComparisonSelectForm(forms.Form):
    """Форма выбора автомобилей для сравнения (минимум 2)."""

    cars = forms.ModelMultipleChoiceField(
        label='Автомобили для сравнения',
        queryset=Car.objects.all().order_by('manufacturer', 'name'),
        widget=forms.SelectMultiple(attrs={'size': 10}),
    )

    def clean_cars(self):
        cars = self.cleaned_data['cars']
        if len(cars) < 2:
            raise forms.ValidationError('Выберите минимум 2 автомобиля для сравнения.')
        if len(cars) > 4:
            raise forms.ValidationError('Можно сравнить не более 4 автомобилей одновременно.')
        return cars


class SignUpForm(UserCreationForm):
    """Регистрация пользователя — расширяет стандартную форму Django."""

    email = forms.EmailField(label='Email', required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email
