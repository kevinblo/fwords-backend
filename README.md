# FWords Backend

Django REST API backend для приложения изучения языков с полнофункциональной системой управления словами, переводами, частями речи и пользователями.

## Возможности

### Аутентификация и пользователи
- ✅ Регистрация пользователей
- ✅ Активация email
- ✅ JWT авторизация (access/refresh токены)
- ✅ Управление профилем пользователя
- ✅ Система разрешений

### Управление языками
- ✅ Поддержка множественных языков
- ✅ Локализация названий языков
- ✅ Активация/деактивация языков

### Части речи
- ✅ Система частей речи с уникальными кодами
- ✅ Переводы частей речи на разные языки
- ✅ Сокращения для частей речи

### Словарь и переводы
- ✅ Управление словами с транскрипцией
- ✅ Двунаправленные переводы между языками
- ✅ Система уровней сложности (A1-C2)
- ✅ Поддержка рода слов
- ✅ Примеры использования слов
- ✅ Аудио произношение (URL)
- ✅ Система уверенности в переводах
- ✅ Случайные слова для изучения

### API и документация
- ✅ RESTful API с полной документацией
- ✅ Swagger UI и ReDoc
- ✅ Фильтрация и поиск
- ✅ Пагинация результатов
- ✅ Админ панель Django

## Технологии

- Django 5.2+
- Django REST Framework 3.14+
- Django REST Framework SimpleJWT 5.2+
- PostgreSQL
- drf-yasg (Swagger/OpenAPI)
- django-cors-headers
- django-filter
- uWSGI
- python-decouple

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd fwords-backend
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=fwords_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@fwords.com
```

### 5. Настройка базы данных

Создайте PostgreSQL базу данных:
```sql
CREATE DATABASE fwords_db;
```

### 6. Применение миграций
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 8. Загрузка начальных данных (опционально)
```bash
# Загрузка языков
python manage.py loaddata languages/fixtures/languages.json

# Загрузка частей речи
python manage.py loaddata parts_of_speech/fixtures/parts_of_speech.json
```

### 9. Запуск сервера
```bash
python manage.py runserver
```

Сервер будет доступен по адресу: http://127.0.0.1:8000/

## Docker

Проект поддерживает развертывание через Docker:

```bash
# Сборка образа
docker build -t fwords-backend .

# Запуск контейнера
docker run -p 8000:8000 fwords-backend
```

Для продакшена используйте docker-compose с PostgreSQL и nginx.

## API Endpoints

Подробная документация по API endpoints доступна в файлах:
- [API_ENDPOINTS.md](API_ENDPOINTS.md) - Полная документация API
- [API_EXAMPLES.md](API_EXAMPLES.md) - Примеры использования API
- [WORDS_API_EXAMPLES.md](WORDS_API_EXAMPLES.md) - Примеры работы со словами

### Аутентификация (`/api/auth/`):
- `POST /api/auth/register/` - Регистрация пользователя
- `GET /api/auth/activate/{token}/` - Активация email
- `POST /api/auth/login/` - Авторизация
- `POST /api/auth/logout/` - Выход
- `GET /api/auth/profile/` - Профиль пользователя
- `POST /api/auth/token/refresh/` - Обновление токена

### Языки (`/api/languages/`):
- `GET /api/languages/` - Список всех языков
- `POST /api/languages/` - Создание нового языка
- `GET /api/languages/{id}/` - Детали языка
- `PUT /api/languages/{id}/` - Обновление языка
- `DELETE /api/languages/{id}/` - Удаление языка

### Части речи (`/api/parts-of-speech/`):
- `GET /api/parts-of-speech/` - Список частей речи
- `POST /api/parts-of-speech/` - Создание части речи
- `GET /api/parts-of-speech/{id}/` - Детали части речи
- `PUT /api/parts-of-speech/{id}/` - Обновление части речи
- `DELETE /api/parts-of-speech/{id}/` - Удаление части речи

### Слова (`/api/words/`):
- `GET /api/words/` - Список слов с фильтрацией
- `POST /api/words/` - Создание нового слова
- `GET /api/words/{id}/` - Детали слова с переводами
- `PUT /api/words/{id}/` - Обновление слова
- `DELETE /api/words/{id}/` - Удаление слова
- `GET /api/words/random/` - Случайные слова для изучения
- `POST /api/words/{id}/translations/` - Добавление перевода
- `GET /api/words/{id}/examples/` - Примеры использования слова

## API Документация

- Swagger UI: http://127.0.0.1:8000/swagger/
- ReDoc: http://127.0.0.1:8000/redoc/
- Админ панель: http://127.0.0.1:8000/admin/

## Структура проекта

```
fwords-backend/
├── config/                 # Настройки Django
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── permissions.py
│   ├── wsgi.py
│   └── asgi.py
├── users/                  # Приложение пользователей
│   ├── models.py           # Модели пользователей и токенов
│   ├── serializers.py      # Сериализаторы для API
│   ├── views.py            # Представления для аутентификации
│   ├── urls.py             # URL маршруты
│   ├── admin.py            # Админ панель
│   └── migrations/         # Миграции базы данных
├── languages/              # Приложение языков
│   ├── models.py           # Модель Language
│   ├── serializers.py      # Сериализаторы языков
│   ├── views.py            # API представления
│   ├── urls.py             # URL маршруты
│   ├── permissions.py      # Разрешения
│   ├── fixtures/           # Начальные данные
│   └── management/         # Команды управления
├── parts_of_speech/        # Приложение частей речи
│   ├── models.py           # PartOfSpeech, PartOfSpeechTranslation
│   ├── serializers.py      # Сериализаторы частей речи
│   ├── views.py            # API представления
│   ├── urls.py             # URL маршруты
│   └── management/         # Команды управления
├── words/                  # Приложение словаря
│   ├── models.py           # Word, WordTranslation, WordExample
│   ├── serializers.py      # Сериализаторы слов
│   ├── views.py            # API представления
│   ├── urls.py             # URL маршруты
│   └── management/         # Команды управления
├── scripts/                # Утилиты и скрипты
│   ├── wordconv.py         # Конвертация словарей
│   ├── wlinks.py           # Обработка ссылок
│   └── README.md           # Документация скриптов
├── manage.py
├── requirements.txt
├── Dockerfile              # Docker конфигурация
├── uwsgi.ini              # uWSGI конфигурация
├── README.md
├── API_ENDPOINTS.md        # Документация API
├── API_EXAMPLES.md         # Примеры использования
├── WORDS_API_EXAMPLES.md   # Примеры работы со словами
└── DEPLOYMENT.md           # Инструкции по развертыванию
```

## Тестирование

Запуск тестов:
```bash
python manage.py test
```

Запуск тестов с покрытием:
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Модели данных

### Пользователи (users)

#### User (Пользователь)
- `email` - Email (уникальный)
- `username` - Имя пользователя
- `first_name` - Имя
- `last_name` - Фамилия
- `is_email_verified` - Подтвержден ли email
- `created_at` - Дата создания
- `updated_at` - Дата обновления

#### EmailActivationToken (Токен активации)
- `user` - Связь с пользователем
- `token` - UUID токен
- `created_at` - Дата создания
- `is_used` - Использован ли токен

### Языки (languages)

#### Language (Язык)
- `code` - Код языка (например: 'en', 'ru', 'es')
- `name_english` - Название на английском
- `name_native` - Название на родном языке
- `enabled` - Активен ли язык
- `created_at` - Дата создания
- `updated_at` - Дата обновления

### Части речи (parts_of_speech)

#### PartOfSpeech (Часть речи)
- `code` - Уникальный код (например: 'noun', 'verb', 'adjective')
- `description` - Описание на английском
- `enabled` - Активна ли часть речи
- `created_at` - Дата создания
- `updated_at` - Дата обновления

#### PartOfSpeechTranslation (Перевод части речи)
- `part_of_speech` - Связь с частью речи
- `language` - Язык перевода
- `name` - Название на указанном языке
- `abbreviation` - Сокращение (например: 'сущ.', 'гл.')
- `created_at` - Дата создания
- `updated_at` - Дата обновления

### Словарь (words)

#### Word (Слово)
- `word` - Само слово
- `language` - Язык слова
- `transcription` - Транскрипция
- `part_of_speech` - Часть речи
- `gender` - Род слова (masculine, feminine, neuter, common)
- `difficulty_level` - Уровень сложности (A1-C2)
- `audio_url` - URL аудиофайла
- `active` - Активно ли слово
- `created_at` - Дата создания
- `updated_at` - Дата обновления

#### WordTranslation (Перевод слова)
- `source_word` - Исходное слово
- `target_word` - Целевое слово (перевод)
- `confidence` - Уверенность в переводе (0.0-1.0)
- `notes` - Дополнительные заметки
- `created_at` - Дата создания
- `updated_at` - Дата обновления

#### WordExample (Пример использования)
- `word` - Слово для примера
- `example_text` - Текст примера
- `translation` - Перевод примера
- `translation_language` - Язык перевода
- `audio_url` - URL аудиофайла примера
- `active` - Активен ли пример
- `created_at` - Дата создания
- `updated_at` - Дата обновления

## Безопасность

- JWT токены для авторизации
- Валидация паролей Django
- CORS настройки
- Защита от XSS и CSRF
- Активация email обязательна

## Развертывание

Для продакшена:
1. Установите `DEBUG=False`
2. Настройте ALLOWED_HOSTS
3. Используйте PostgreSQL
4. Настройте HTTPS
5. Используйте переменные окружения для секретных данных
6. Настройте статические файлы (collectstatic)

## Лицензия

MIT License