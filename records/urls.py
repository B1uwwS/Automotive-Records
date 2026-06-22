from django.urls import path

from . import views

app_name = 'records'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),

    # Категории
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),

    # Автомобили / рекорды
    path('cars/', views.CarListView.as_view(), name='car_list'),
    path('cars/<slug:slug>/', views.CarDetailView.as_view(), name='car_detail'),

    # Поиск
    path('search/', views.SearchView.as_view(), name='search'),

    # Сравнение
    path('compare/', views.CompareView.as_view(), name='compare'),
    path('compare/toggle/<slug:slug>/', views.compare_toggle, name='compare_toggle'),
    path('compare/clear/', views.compare_clear, name='compare_clear'),

    # Избранное
    path('favorites/', views.FavoriteListView.as_view(), name='favorite_list'),
    path('favorites/toggle/<slug:slug>/', views.favorite_toggle, name='favorite_toggle'),

    # Идеальный сбалансированный автомобиль
    path('balanced/', views.BalancedCarView.as_view(), name='balanced'),

    # Аутентификация
    path('accounts/signup/', views.SignUpView.as_view(), name='signup'),
    path('accounts/login/', views.AppLoginView.as_view(), name='login'),
    path('accounts/logout/', views.AppLogoutView.as_view(), name='logout'),
]
