# Automotive Records

Премиальная цифровая энциклопедия мировых автомобильных рекордов — тёмная тема,
золотые акценты, на чистом Django + встроенных шаблонах (без React/Vue/Node).

## Стек

- Python + Django 5.x
- PostgreSQL
- Встроенные Django templates, чистый CSS, vanilla JS
- Никаких frontend-фреймворков

## Структура проекта

```
AutomotiveRecords/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                  # настройки проекта
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── records/                  # основное приложение
│   ├── models.py             # Car, Category, Record, Comparison, Favorite
│   ├── scoring.py            # алгоритм "Идеальный сбалансированный автомобиль"
│   ├── admin.py
│   ├── forms.py
│   ├── views.py              # CBV + FBV
│   ├── urls.py
│   ├── context_processors.py
│   ├── templatetags/records_extras.py
│   └── fixtures/initial_data.json   # 8 категорий + 16 авто + 11 рекордов
├── templates/
│   ├── base.html
│   ├── records/               # все страницы приложения
│   └── registration/          # login / signup
└── static/
    ├── css/style.css
    └── js/main.js
```

## Установка и запуск

### 1. Клонировать и создать виртуальное окружение

```bash
cd AutomotiveRecords
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить переменные окружения

```bash
cp .env.example .env
```

Откройте `.env` и укажите реальные данные для подключения к PostgreSQL
(`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), а также
сгенерируйте новый `SECRET_KEY` для продакшена.

### 4. Создать базу данных PostgreSQL

```sql
CREATE DATABASE automotive_records;
```

### 5. Применить миграции

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Создать суперпользователя

```bash
python manage.py createsuperuser
```

### 7. Загрузить тестовые данные (8 категорий, 16 автомобилей, 11 рекордов)

```bash
python manage.py loaddata initial_data
```

### 8. Собрать статику (для продакшена; в DEBUG=True не обязательно)

```bash
python manage.py collectstatic --noinput
```

### 9. Запустить сервер разработки

```bash
python manage.py runserver
```

Приложение будет доступно на `http://127.0.0.1:8000/`,
админка — на `http://127.0.0.1:8000/admin/`.

## Основные разделы

- `/` — главная с 8 категориями рекордов
- `/cars/` — все автомобили: поиск, фильтры, сортировка, таблица
- `/cars/<slug>/` — детальная карточка автомобиля
- `/category/<slug>/` — история рекордов в категории
- `/compare/` — сравнение 2–4 автомобилей с подсветкой победителя
- `/balanced/` — "Идеальный сбалансированный автомобиль" (рейтинг по алгоритму)
- `/favorites/` — избранное (требует входа)
- `/accounts/login/`, `/accounts/signup/` — аутентификация

## Алгоритм "Идеальный сбалансированный автомобиль"

Реализован в `records/scoring.py`. Считает взвешенный балл (0–100) по шести
нормализованным параметрам:

| Параметр | Вес |
|---|---|
| Максимальная скорость | 20% |
| Мощность | 15% |
| Разгон 0-100 км/ч (инвертирован — меньше лучше) | 15% |
| Надёжность | 20% |
| Экологичность | 15% |
| Технологичность | 15% |

Нормализация ведётся относительно реального разброса значений среди всех
автомобилей в реестре, что не позволяет единственному параметру-выбросу
доминировать в итоговом рейтинге.

## Загрузка фотографий автомобилей

Фотографии загружаются через Django admin (поле `photo` модели `Car`) и
сохраняются в `media/cars/`. В фикстуре `initial_data.json` поле `photo`
не заполнено — добавьте изображения вручную через `/admin/`.
