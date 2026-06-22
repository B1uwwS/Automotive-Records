from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import CarFilterForm, SignUpForm
from .models import Car, Category, Favorite, Record
from .scoring import compute_balance_scores_for_queryset

COMPARE_SESSION_KEY = 'compare_car_ids'
MAX_COMPARE = 4


# ---------------------------------------------------------------------------
# Главная страница
# ---------------------------------------------------------------------------
class HomeView(TemplateView):
    template_name = 'records/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.order_by('order', 'name')
        context['featured_cars'] = (
            Car.objects.filter(is_featured=True)
            .select_related('record_category')
            .order_by('-year')[:6]
        )
        context['latest_records'] = (
            Record.objects.filter(is_current=True)
            .select_related('car', 'category')
            .order_by('-date_set')[:5]
        )
        context['total_cars'] = Car.objects.count()
        context['total_records'] = Record.objects.filter(is_current=True).count()
        return context


# ---------------------------------------------------------------------------
# Категория: детальная страница с действующим рекордом и историей
# ---------------------------------------------------------------------------
class CategoryDetailView(DetailView):
    model = Category
    template_name = 'records/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = (
            self.object.records.select_related('car')
            .order_by('-is_current', '-date_set')
        )
        context['records'] = records
        context['current_record'] = records.filter(is_current=True).first()
        return context


# ---------------------------------------------------------------------------
# Список всех рекордов / автомобилей с фильтрами, поиском и сортировкой
# ---------------------------------------------------------------------------
class CarListView(ListView):
    model = Car
    template_name = 'records/car_list.html'
    context_object_name = 'cars'
    paginate_by = 12

    def get_queryset(self):
        queryset = Car.objects.select_related('record_category').prefetch_related('records__category')
        form = CarFilterForm(self.request.GET or None)
        self.filter_form = form

        if form.is_valid():
            data = form.cleaned_data
            if data.get('q'):
                q = data['q']
                queryset = queryset.filter(
                    Q(name__icontains=q)
                    | Q(manufacturer__icontains=q)
                    | Q(description__icontains=q)
                    | Q(year__icontains=q)
                )
            if data.get('category'):
                queryset = queryset.filter(record_category=data['category'])
            if data.get('manufacturer'):
                queryset = queryset.filter(manufacturer__icontains=data['manufacturer'])
            if data.get('year_from'):
                queryset = queryset.filter(year__gte=data['year_from'])
            if data.get('year_to'):
                queryset = queryset.filter(year__lte=data['year_to'])
            if data.get('fuel_type'):
                queryset = queryset.filter(fuel_type=data['fuel_type'])

            sort = data.get('sort')
            if sort and sort != '-balance':
                queryset = queryset.order_by(sort)
            elif not sort:
                queryset = queryset.order_by('-year')
            # '-balance' обрабатывается отдельно ниже, так как это вычисляемое поле

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = getattr(self, 'filter_form', CarFilterForm())
        context['compare_ids'] = self.request.session.get(COMPARE_SESSION_KEY, [])

        query_dict = self.request.GET.copy()
        query_dict.pop('page', None)
        querystring = query_dict.urlencode()
        context['querystring_no_page'] = f'{querystring}&' if querystring else ''

        sort = self.request.GET.get('sort')
        if sort == '-balance':
            # Балл считается относительно уже отображаемой страницы (после пагинации).
            # Полноценный рейтинг по всему реестру — см. отдельную страницу /balanced/.
            scored = compute_balance_scores_for_queryset(context['cars'])
            context['cars'] = [car for car, _score in scored]
            context['balance_scores'] = {car.pk: score for car, score in scored}

        return context


# ---------------------------------------------------------------------------
# Детальная страница автомобиля
# ---------------------------------------------------------------------------
class CarDetailView(DetailView):
    model = Car
    template_name = 'records/car_detail.html'
    context_object_name = 'car'

    def get_queryset(self):
        return Car.objects.select_related('record_category').prefetch_related('records__category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['records'] = self.object.records.select_related('category').order_by('-date_set')
        context['balance_score'] = self.object.balance_score

        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, car=self.object
            ).exists()

        # Похожие автомобили в той же категории
        if self.object.record_category_id:
            context['related_cars'] = (
                Car.objects.filter(record_category_id=self.object.record_category_id)
                .exclude(pk=self.object.pk)[:4]
            )

        context['compare_ids'] = self.request.session.get(COMPARE_SESSION_KEY, [])
        return context


# ---------------------------------------------------------------------------
# Сравнение автомобилей
# ---------------------------------------------------------------------------
def compare_toggle(request, slug):
    """Добавляет/удаляет автомобиль в список сравнения (хранится в сессии)."""
    car = get_object_or_404(Car, slug=slug)
    compare_ids = request.session.get(COMPARE_SESSION_KEY, [])

    if car.pk in compare_ids:
        compare_ids.remove(car.pk)
        messages.info(request, f'«{car}» убран из сравнения.')
    else:
        if len(compare_ids) >= MAX_COMPARE:
            messages.warning(request, f'Можно сравнить не более {MAX_COMPARE} автомобилей одновременно.')
        else:
            compare_ids.append(car.pk)
            messages.success(request, f'«{car}» добавлен к сравнению.')

    request.session[COMPARE_SESSION_KEY] = compare_ids
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'records:car_list'
    return redirect(next_url)


class CompareView(TemplateView):
    template_name = 'records/compare.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compare_ids = self.request.session.get(COMPARE_SESSION_KEY, [])
        cars = list(Car.objects.filter(pk__in=compare_ids).select_related('record_category'))
        # Сохраняем порядок добавления пользователем
        cars.sort(key=lambda c: compare_ids.index(c.pk))
        context['cars'] = cars
        context['all_cars'] = Car.objects.order_by('manufacturer', 'name')

        if len(cars) >= 2:
            context['winners'] = self._compute_winners(cars)

        return context

    @staticmethod
    def _compute_winners(cars):
        """Определяет «победителя» по каждому числовому параметру для подсветки."""
        fields = [
            ('top_speed_kmh', 'max', 'Максимальная скорость'),
            ('power_hp', 'max', 'Мощность'),
            ('acceleration_0_100', 'min', 'Разгон 0-100 км/ч'),
            ('price_usd', 'max', 'Цена'),
            ('weight_kg', 'min', 'Масса'),
            ('reliability_score', 'max', 'Надёжность'),
            ('eco_score', 'max', 'Экологичность'),
            ('tech_score', 'max', 'Технологичность'),
        ]
        winners = {}
        for field_name, mode, _label in fields:
            values = [(car.pk, getattr(car, field_name)) for car in cars if getattr(car, field_name) is not None]
            if not values:
                continue
            if mode == 'max':
                winner_pk = max(values, key=lambda pair: pair[1])[0]
            else:
                winner_pk = min(values, key=lambda pair: pair[1])[0]
            winners[field_name] = winner_pk
        return winners


def compare_clear(request):
    request.session[COMPARE_SESSION_KEY] = []
    messages.info(request, 'Список сравнения очищен.')
    return redirect('records:compare')


# ---------------------------------------------------------------------------
# Избранное
# ---------------------------------------------------------------------------
class FavoriteListView(LoginRequiredMixin, ListView):
    template_name = 'records/favorites.html'
    context_object_name = 'favorites'
    paginate_by = 12

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related('car', 'car__record_category')
            .order_by('-created_at')
        )


@login_required
def favorite_toggle(request, slug):
    car = get_object_or_404(Car, slug=slug)
    favorite, created = Favorite.objects.get_or_create(user=request.user, car=car)
    if not created:
        favorite.delete()
        messages.info(request, f'«{car}» удалён из избранного.')
    else:
        messages.success(request, f'«{car}» добавлен в избранное.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'records:car_list'
    return redirect(next_url)


# ---------------------------------------------------------------------------
# Идеальный сбалансированный автомобиль
# ---------------------------------------------------------------------------
class BalancedCarView(TemplateView):
    template_name = 'records/balanced.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Car.objects.select_related('record_category')
        scored = compute_balance_scores_for_queryset(queryset)
        context['ranking'] = scored[:20]
        context['winner'] = scored[0] if scored else None
        return context


# ---------------------------------------------------------------------------
# Поиск (отдельная точка входа, переиспользует CarListView логику через GET)
# ---------------------------------------------------------------------------
class SearchView(CarListView):
    template_name = 'records/search_results.html'


# ---------------------------------------------------------------------------
# Аутентификация
# ---------------------------------------------------------------------------
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('records:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Регистрация прошла успешно. Добро пожаловать!')
        return response


class AppLoginView(LoginView):
    template_name = 'registration/login.html'


class AppLogoutView(LogoutView):
    next_page = reverse_lazy('records:home')
