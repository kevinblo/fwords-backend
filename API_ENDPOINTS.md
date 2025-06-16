# FWords Backend API Endpoints

Полная документация API для приложения изучения языков FWords Backend.

## Базовые URL

- **API v1 Base URL**: `/api/v1/`
- **Authentication**: `/api/v1/auth/`

## Аутентификация

Для защищенных endpoints используйте JWT токен в заголовке:

```
Authorization: Bearer {access_token}
```

---

## 1. Authentication Endpoints

### 1.1. User Registration

**POST** `/api/v1/auth/register/`

Регистрация нового пользователя с отправкой email для активации.

**Request Body:**

```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword123",
  "password_confirm": "securepassword123"
}
```

**Response (201):**

```json
{
  "message": "User registered successfully. Please check your email to activate your account.",
  "user_id": 1
}
```

### 1.2. Email Activation

**GET** `/api/v1/auth/activate/{token}/`

Активация email пользователя по токену из письма.

**Response (200):**

```json
{
  "message": "Email activated successfully. You can now login."
}
```

### 1.3. User Login

**POST** `/api/v1/auth/login/`

Авторизация пользователя с получением JWT токенов.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**

```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "is_email_verified": true,
    "created_at": "2024-01-01T12:00:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### 1.4. Token Refresh

**POST** `/api/v1/auth/token/refresh/`

Обновление access токена с помощью refresh токена.

**Request Body:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 1.5. User Logout

**POST** `/api/v1/auth/logout/`

Выход пользователя с блокировкой refresh токена.

**Headers:**

```
Authorization: Bearer {access_token}
```

**Request Body:**

```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**

```json
{
  "message": "Logout successful"
}
```

### 1.6. User Profile

**GET** `/api/v1/auth/profile/`

Получение профиля текущего пользователя.

**Headers:**

```
Authorization: Bearer {access_token}
```

**Response (200):**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "is_email_verified": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

**PATCH** `/api/v1/auth/profile/`

Обновление профиля пользователя.

**Headers:**

```
Authorization: Bearer {access_token}
```

**Request Body:**

```json
{
  "username": "newusername"
}
```

### 1.7. Resend Activation Email

**POST** `/api/v1/auth/resend-activation/`

Повторная отправка письма для активации email.

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response (200):**

```json
{
  "message": "Activation email sent successfully"
}
```

---

## 2. Languages Endpoints

### 2.1. List Languages

**GET** `/api/v1/languages/`

Получение списка всех языков.

**Query Parameters:**

- `enabled_only=true` - только активные языки

**Response (200):**

```json
[
  {
    "id": 1,
    "code": "en",
    "name_english": "English",
    "name_native": "English",
    "enabled": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  {
    "id": 2,
    "code": "ru",
    "name_english": "Russian",
    "name_native": "Русский",
    "enabled": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 2.2. Create Language

**POST** `/api/v1/languages/`

Создание нового языка. *Требует права администратора.*

**Request Body:**

```json
{
  "code": "es",
  "name_english": "Spanish",
  "name_native": "Español",
  "enabled": true
}
```

### 2.3. Get Language by Code

**GET** `/api/v1/languages/{code}/`

Получение языка по коду.

**Response (200):**

```json
{
  "id": 1,
  "code": "en",
  "name_english": "English",
  "name_native": "English",
  "enabled": true,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 2.4. Update Language

**PUT/PATCH** `/api/v1/languages/{code}/`

Обновление языка. *Требует права администратора.*

### 2.5. Delete Language

**DELETE** `/api/v1/languages/{code}/`

Удаление языка. *Требует права администратора.*

### 2.6. Get Enabled Languages

**GET** `/api/v1/languages/enabled/`

Получение только активных языков.

### 2.7. Get Language Codes

**GET** `/api/v1/languages/codes/`

Получение списка кодов языков.

**Query Parameters:**

- `enabled_only=true` - только коды активных языков

**Response (200):**

```json
[
  "en",
  "ru",
  "es",
  "fr"
]
```

---

## 3. Parts of Speech Endpoints

### 3.1. List Parts of Speech

**GET** `/api/v1/pos/`

Получение списка частей речи.

**Query Parameters:**

- `enabled=true` - фильтр по активности
- `search=noun` - поиск по коду или описанию

**Response (200):**

```json
[
  {
    "id": 1,
    "code": "noun",
    "description": "A word used to identify any of a class of people, places, or things",
    "enabled": true,
    "translations": [
      {
        "id": 1,
        "language": {
          "code": "ru",
          "name_english": "Russian"
        },
        "name": "существительное",
        "abbreviation": "сущ."
      }
    ],
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 3.2. Create Part of Speech

**POST** `/api/v1/pos/`

Создание новой части речи. *Требует права администратора.*

**Request Body:**

```json
{
  "code": "adjective",
  "description": "A word that describes a noun or pronoun",
  "enabled": true
}
```

### 3.3. Get Part of Speech

**GET** `/api/v1/pos/{id}/`

Получение части речи по ID.

### 3.4. Update Part of Speech

**PUT/PATCH** `/api/v1/pos/{id}/`

Обновление части речи. *Требует права администратора.*

### 3.5. Delete Part of Speech

**DELETE** `/api/v1/pos/{id}/`

Удаление части речи. *Требует права администратора.*

### 3.6. Get Simple Parts of Speech

**GET** `/api/v1/pos/simple/`

Получение упрощенного списка частей речи (для UI компонентов).

**Response (200):**

```json
[
  {
    "id": 1,
    "code": "noun",
    "name": "существительное"
  }
]
```

### 3.7. Get Part of Speech Translations

**GET** `/api/v1/pos/{id}/tr/`

Получение всех переводов части речи.

### 3.8. Add Translation to Part of Speech

**POST** `/api/v1/pos/{id}/add_translation/`

Добавление перевода к части речи. *Требует права администратора.*

**Request Body:**

```json
{
  "language": 1,
  "name": "прилагательное",
  "abbreviation": "прил."
}
```

### 3.9. Get Enabled Parts of Speech

**GET** `/api/v1/pos/enabled/`

Получение только активных частей речи.

---

## 4. Words Endpoints

### 4.1. List Words

**GET** `/api/v1/words/`

Получение списка слов с фильтрацией и поиском.

**Query Parameters:**

- `language=1` - фильтр по языку
- `part_of_speech=1` - фильтр по части речи
- `gender=masculine` - фильтр по роду
- `difficulty_level=beginner` - фильтр по уровню сложности
- `active=true` - фильтр по активности
- `search=hello` - поиск по слову или транскрипции
- `ordering=word` - сортировка

**Response (200):**

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/words/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "word": "hello",
      "language": {
        "id": 1,
        "code": "en",
        "name_english": "English"
      },
      "transcription": "/həˈloʊ/",
      "part_of_speech": {
        "id": 1,
        "code": "interjection",
        "name": "междометие"
      },
      "gender": null,
      "difficulty_level": "beginner",
      "audio_url": "https://example.com/audio/hello.mp3",
      "active": true,
      "translations": [
        {
          "id": 1,
          "target_word": {
            "id": 2,
            "word": "привет",
            "language": {
              "code": "ru",
              "name_english": "Russian"
            }
          },
          "confidence": 1.0,
          "notes": ""
        }
      ],
      "examples": [
        {
          "id": 1,
          "example_text": "Hello, how are you?",
          "translation": "Привет, как дела?",
          "translation_language": {
            "code": "ru",
            "name_english": "Russian"
          }
        }
      ],
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### 4.2. Create Word

**POST** `/api/v1/words/`

Создание нового слова. *Требует права администратора.*

**Request Body:**

```json
{
  "word": "goodbye",
  "language": 1,
  "transcription": "/ɡʊdˈbaɪ/",
  "part_of_speech": 1,
  "gender": null,
  "difficulty_level": "beginner",
  "audio_url": "https://example.com/audio/goodbye.mp3",
  "active": true
}
```

### 4.3. Get Word

**GET** `/api/v1/words/{id}/`

Получение слова по ID с полной информацией.

### 4.4. Update Word

**PUT/PATCH** `/api/v1/words/{id}/`

Обновление слова. *Требует права администратора.*

### 4.5. Delete Word

**DELETE** `/api/v1/words/{id}/`

Удаление слова. *Требует права администратора.*

### 4.6. Get Simple Words

**GET** `/api/v1/words/simple/`

Получение упрощенного списка слов (для UI компонентов).

### 4.7. Get Word Translations

**GET** `/api/v1/words/{id}/tr/`

Получение всех переводов слова.

### 4.8. Add Translation to Word

**POST** `/api/v1/words/{id}/add_translation/`

Добавление перевода к слову. *Требует права администратора.*

**Request Body:**

```json
{
  "target_word_id": 2,
  "confidence": 1.0,
  "notes": "Основной перевод"
}
```

### 4.9. Get Word Examples

**GET** `/api/v1/words/{id}/examples/`

Получение примеров использования слова.

### 4.10. Add Example to Word

**POST** `/api/v1/words/{id}/add_example/`

Добавление примера использования к слову. *Требует права администратора.*

**Request Body:**

```json
{
  "example_text": "Goodbye, see you later!",
  "translation": "До свидания, увидимся позже!",
  "translation_language": 2,
  "audio_url": "https://example.com/audio/goodbye_example.mp3"
}
```

### 4.11. Get Active Words

**GET** `/api/v1/words/active/`

Получение только активных слов.

### 4.12. Get Words by Difficulty

**GET** `/api/v1/words/by_difficulty/?difficulty_level=beginner`

Получение слов по уровню сложности.

**Query Parameters:**

- `difficulty_level` - уровень сложности (обязательный)

### 4.13. Advanced Word Search

**POST** `/api/v1/words/search/`

Расширенный поиск слов.

**Request Body:**

```json
{
  "query": "hello",
  "language": "en",
  "part_of_speech": "interjection",
  "difficulty_level": "beginner",
  "active_only": true
}
```

### 4.14. Get Word Statistics

**GET** `/api/v1/words/stats/`

Получение статистики по словам.

**Response (200):**

```json
{
  "total_words": 1000,
  "active_words": 950,
  "words_by_language": {
    "en": 500,
    "ru": 400,
    "es": 100
  },
  "words_by_part_of_speech": {
    "noun": 400,
    "verb": 300,
    "adjective": 200,
    "adverb": 100
  },
  "words_by_difficulty_level": {
    "beginner": 300,
    "elementary": 250,
    "intermediate": 200,
    "upper_intermediate": 150,
    "advanced": 75,
    "proficient": 25
  },
  "words_with_audio": 800,
  "words_with_examples": 600
}
```

### 4.15. Get Random Words

**GET** `/api/v1/words/random/?from=en&to=ru&count=20&level=beginner`

Получение случайных слов для изучения.

**Query Parameters:**

- `from` - код исходного языка (обязательный)
- `to` - код языка перевода (обязательный)
- `count` - количество слов (по умолчанию 20, максимум 100)
- `level` - уровень сложности (необязательный)

**Response (200):**

```json
{
  "words": [
    {
      "id": 27864,
      "word": "awkward",
      "language": {
        "id": 1,
        "code": "en",
        "name_english": "English",
        "name_native": "English",
        "enabled": true,
        "created_at": "2025-06-09T00:14:19.066513Z",
        "updated_at": "2025-06-09T00:14:19.066529Z"
      },
      "transcription": "/ˈɑkwɚd/",
      "part_of_speech": {
        "id": 1,
        "code": "noun",
        "name": "noun",
        "abbreviation": "n."
      },
      "gender": null,
      "gender_display": null,
      "difficulty_level": "upper_intermediate",
      "difficulty_level_display": "B2",
      "audio_url": "awkward__us_1.mp3",
      "active": true,
      "examples": [],
      "translation": {
        "id": 27865,
        "word": "неловкий",
        "language": {
          "id": 2,
          "code": "ru",
          "name_english": "Russian",
          "name_native": "Русский",
          "enabled": true,
          "created_at": "2025-06-09T00:14:19.070180Z",
          "updated_at": "2025-06-09T00:14:19.070193Z"
        },
        "transcription": "",
        "part_of_speech": {
          "id": 1,
          "code": "noun",
          "name": "существительное",
          "abbreviation": "сущ."
        },
        "gender": null,
        "gender_display": null,
        "difficulty_level": "upper_intermediate",
        "difficulty_level_display": "B2",
        "audio_url": "",
        "active": true,
        "examples": [],
        "confidence": 1,
        "notes": "Импортировано из CSV (часть речи: noun)",
        "created_at": "2025-06-09T21:50:22.413449Z",
        "updated_at": "2025-06-09T21:50:22.413463Z"
      },
      "created_at": "2025-06-09T21:50:22.409853Z",
      "updated_at": "2025-06-09T21:50:22.409866Z"
    }
  ],
  "total_available": 4956,
  "requested_count": 1,
  "returned_count": 1,
  "source_language": "en",
  "target_language": "ru",
  "difficulty_level": null
}
```

---

## 5. Word Translations Endpoints

### 5.1. List Word Translations

**GET** `/api/v1/words/tr/`

Получение списка переводов слов.

**Query Parameters:**

- `source_word__language=1` - фильтр по исходному языку
- `target_word__language=2` - фильтр по языку перевода
- `confidence=1.0` - фильтр по уверенности
- `search=hello` - поиск по словам или заметкам

### 5.2. Create Word Translation

**POST** `/api/v1/words/tr/`

Создание нового перевода. *Требует права администратора.*

**Request Body:**

```json
{
  "source_word_id": 1,
  "target_word_id": 2,
  "confidence": 1.0,
  "notes": "Основной перевод"
}
```

### 5.3. Get Word Translation

**GET** `/api/v1/words/tr/{id}/`

Получение перевода по ID.

### 5.4. Update Word Translation

**PUT/PATCH** `/api/v1/words/tr/{id}/`

Обновление перевода. *Требует права администратора.*

### 5.5. Delete Word Translation

**DELETE** `/api/v1/words/tr/{id}/`

Удаление перевода. *Требует права администратора.*

---

## 6. Word Examples Endpoints

### 6.1. List Word Examples

**GET** `/api/v1/words/examples/`

Получение списка примеров использования слов.

**Query Parameters:**

- `word=1` - фильтр по слову
- `translation_language=2` - фильтр по языку перевода
- `active=true` - фильтр по активности
- `search=example` - поиск по тексту примера или переводу

### 6.2. Create Word Example

**POST** `/api/v1/words/examples/`

Создание нового примера. *Требует права администратора.*

**Request Body:**

```json
{
  "word": 1,
  "example_text": "Hello, world!",
  "translation": "Привет, мир!",
  "translation_language": 2,
  "audio_url": "https://example.com/audio/hello_world.mp3",
  "active": true
}
```

### 6.3. Get Word Example

**GET** `/api/v1/words/examples/{id}/`

Получение примера по ID.

### 6.4. Update Word Example

**PUT/PATCH** `/api/v1/words/examples/{id}/`

Обновление примера. *Требует права администратора.*

### 6.5. Delete Word Example

**DELETE** `/api/v1/words/examples/{id}/`

Удаление примера. *Требует права администратора.*

---

## 7. Progress Endpoints

API для отслеживания прогресса изучения языков и слов пользователем. Все endpoints требуют аутентификации.

### Language Progress

#### List/Create Language Progress

**GET** `/api/v1/progress/language/`

Получение списка прогресса изучения языков для текущего пользователя.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
[
  {
    "id": 1,
    "language": {
      "id": 1,
      "code": "en",
      "name_english": "English",
      "name_native": "English",
      "enabled": true,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    },
    "level": "B1",
    "learned_words_count": 150,
    "learned_phrases_count": 45,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-15T18:30:00Z"
  }
]
```

**POST** `/api/v1/progress/language/`

Создание нового прогресса изучения языка.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "language_id": 1,
  "level": "A1",
  "learned_words_count": 0,
  "learned_phrases_count": 0
}
```

**Response (201):**
```json
{
  "id": 2,
  "language": {
    "id": 1,
    "code": "en",
    "name_english": "English",
    "name_native": "English",
    "enabled": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "level": "A1",
  "learned_words_count": 0,
  "learned_phrases_count": 0,
  "created_at": "2024-01-16T10:00:00Z",
  "updated_at": "2024-01-16T10:00:00Z"
}
```

#### Language Progress Detail

**GET** `/api/v1/progress/language/{id}/`

Получение детального прогресса изучения конкретного языка.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": 1,
  "language": {
    "id": 1,
    "code": "en",
    "name_english": "English",
    "name_native": "English",
    "enabled": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "level": "B1",
  "learned_words_count": 150,
  "learned_phrases_count": 45,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-15T18:30:00Z"
}
```

**PATCH** `/api/v1/progress/language/{id}/`

Обновление прогресса изучения языка.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "level": "B2",
  "learned_words_count": 200,
  "learned_phrases_count": 60
}
```

**DELETE** `/api/v1/progress/language/{id}/`

Удаление прогресса изучения языка.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (204):** No Content

---

### Words Progress

#### List/Create Words Progress

**GET** `/api/v1/progress/words/`

Получение списка прогресса изучения слов для текущего пользователя.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `status` - фильтр по статусу (`new`, `learning`, `learned`, `mastered`)
- `target_language` - фильтр по коду языка перевода (например: `ru`)
- `word_language` - фильтр по коду языка слова (например: `en`)
- `due_for_review` - слова, готовые для повторения (`true`/`false`)

**Response (200):**
```json
[
  {
    "id": 1,
    "word": {
      "id": 27864,
      "word": "hello",
      "language": {
        "id": 1,
        "code": "en",
        "name": "English"
      },
      "transcription": "/həˈloʊ/",
      "part_of_speech": "interjection",
      "difficulty_level": "beginner"
    },
    "target_language": {
      "id": 2,
      "code": "ru",
      "name_english": "Russian",
      "name_native": "Русский",
      "enabled": true,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    },
    "status": "learning",
    "interval": 3,
    "next_review": "2024-01-18T12:00:00Z",
    "review_count": 5,
    "correct_count": 3,
    "date_learned": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-16T14:45:00Z"
  }
]
```

**POST** `/api/v1/progress/words/`

Создание нового прогресса изучения слова.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "word_id": 27864,
  "target_language_id": 2,
  "status": "new",
  "interval": 1
}
```

**Response (201):**
```json
{
  "id": 2,
  "word": {
    "id": 27864,
    "word": "hello",
    "language": {
      "id": 1,
      "code": "en",
      "name": "English"
    },
    "transcription": "/həˈloʊ/",
    "part_of_speech": "interjection",
    "difficulty_level": "beginner"
  },
  "target_language": {
    "id": 2,
    "code": "ru",
    "name_english": "Russian",
    "name_native": "Русский",
    "enabled": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "status": "new",
  "interval": 1,
  "next_review": null,
  "review_count": 0,
  "correct_count": 0,
  "date_learned": null,
  "created_at": "2024-01-16T15:00:00Z",
  "updated_at": "2024-01-16T15:00:00Z"
}
```

#### Words Progress Detail

**GET** `/api/v1/progress/words/{id}/`

Получение детального прогресса изучения конкретного слова.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": 1,
  "word": {
    "id": 27864,
    "word": "hello",
    "language": {
      "id": 1,
      "code": "en",
      "name": "English"
    },
    "transcription": "/həˈloʊ/",
    "part_of_speech": "interjection",
    "difficulty_level": "beginner"
  },
  "target_language": {
    "id": 2,
    "code": "ru",
    "name_english": "Russian",
    "name_native": "Русский",
    "enabled": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "status": "learning",
  "interval": 3,
  "next_review": "2024-01-18T12:00:00Z",
  "review_count": 5,
  "correct_count": 3,
  "date_learned": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:45:00Z"
}
```

**PATCH** `/api/v1/progress/words/{id}/`

Обновление прогресса изучения слова.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "status": "learned",
  "review_count": 6,
  "correct_count": 5,
  "interval": 7,
  "next_review": "2024-01-25T12:00:00Z"
}
```

**DELETE** `/api/v1/progress/words/{id}/`

Удаление прогресса изучения слова.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (204):** No Content

#### Bulk Update Words Progress

**POST** `/api/v1/progress/words/bulk-update/`

Массовое обновление прогресса изучения слов (для сессий повторения).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "updates": [
    {
      "id": 1,
      "correct": true,
      "status": "learning",
      "interval": 3,
      "next_review": "2024-01-18T12:00:00Z"
    },
    {
      "id": 2,
      "correct": false,
      "status": "new",
      "interval": 1,
      "next_review": "2024-01-16T12:00:00Z"
    }
  ]
}
```

**Response (200):**
```json
{
  "updated_count": 2,
  "total_requested": 2,
  "errors": []
}
```

**Response with errors (200):**
```json
{
  "updated_count": 1,
  "total_requested": 2,
  "errors": [
    {
      "error": "Words progress with id 999 not found"
    }
  ]
}
```

---

## Progress Data Models

### Language Progress Fields

- **id** - Уникальный идентификатор записи
- **language** - Объект языка с полной информацией
- **language_id** - ID языка (только для записи)
- **level** - Уровень владения языком (`A1`, `A2`, `B1`, `B2`, `C1`, `C2`)
- **learned_words_count** - Количество изученных слов
- **learned_phrases_count** - Количество изученных фраз
- **created_at** - Дата создания записи
- **updated_at** - Дата последнего обновления

### Words Progress Fields

- **id** - Уникальный идентификатор записи
- **word** - Объект слова с полной информацией (только для чтения)
- **word_id** - ID слова (только для записи)
- **target_language** - Объект языка перевода (только для чтения)
- **target_language_id** - ID языка перевода (только для записи)
- **status** - Статус изучения:
    - `new` - Новое слово
    - `learning` - Изучается
    - `learned` - Изучено
    - `mastered` - Освоено
- **interval** - Интервал повторения в днях
- **next_review** - Дата и время следующего повторения
- **review_count** - Общее количество повторений
- **correct_count** - Количество правильных ответов
- **date_learned** - Дата изучения (устанавливается автоматически при статусе `learned` или `mastered`)
- **created_at** - Дата создания записи
- **updated_at** - Дата последнего обновления

### Bulk Update Fields

- **id** - ID записи прогресса (обязательное)
- **correct** - Правильный ли был ответ (обязательное)
- **status** - Новый статус (необязательное)
- **interval** - Новый интервал повторения (необязательное)
- **next_review** - Дата следующего повторения (необязательное)

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": [
    "Error message"
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### Validation Errors
```json
{
  "word_id": [
    "Invalid or inactive word"
  ],
  "target_language_id": [
    "Invalid or disabled language"
  ],
  "non_field_errors": [
    "Target language cannot be the same as word language"
  ]
}
```

---

## Usage Examples

### Создание прогресса для нового слова
```bash
curl -X POST "http://localhost:8000/api/v1/progress/words/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "word_id": 123,
    "target_language_id": 2,
    "status": "new"
  }'
```

### Получение слов для повторения
```bash
curl "http://localhost:8000/api/v1/progress/words/?due_for_review=true&status=learning" \
  -H "Authorization: Bearer {access_token}"
```

### Обновление после сессии повторения
```bash
curl -X POST "http://localhost:8000/api/v1/progress/words/bulk-update/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {
        "id": 1,
        "correct": true,
        "interval": 7,
        "next_review": "2024-01-25T12:00:00Z"
      }
    ]
  }'
```

### Фильтрация прогресса слов
```bash
# Получить все новые слова
curl "http://localhost:8000/api/v1/progress/words/?status=new" \
  -H "Authorization: Bearer {access_token}"

# Получить слова для изучения английского на русский
curl "http://localhost:8000/api/v1/progress/words/?word_language=en&target_language=ru" \
  -H "Authorization: Bearer {access_token}"

# Получить слова, готовые для повторения
curl "http://localhost:8000/api/v1/progress/words/?due_for_review=true" \
  -H "Authorization: Bearer {access_token}"
```

### Обновление прогресса языка
```bash
curl -X PATCH "http://localhost:8000/api/v1/progress/language/1/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "B2",
    "learned_words_count": 250
  }'
```
---

## Error Responses

### 400 Bad Request

```json
{
  "field_name": [
    "Error message"
  ]
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error

```json
{
  "detail": "A server error occurred."
}
```

---

## Permissions

- **Публичные endpoints**: Доступны всем пользователям
- **Только чтение**: Доступны всем пользователям для чтения
- **Администратор**: Требуют права администратора для записи/изменения

---

## API Documentation

- **Swagger UI**: `/swagger/`
- **ReDoc**: `/redoc/`
- **OpenAPI Schema**: `/swagger.json`

---

## Pagination

Большинство списочных endpoints поддерживают пагинацию:

**Query Parameters:**

- `page=1` - номер страницы
- `page_size=20` - размер страницы (по умолчанию 20, максимум 100)

**Response Format:**

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/words/?page=2",
  "previous": null,
  "results": [
    ...
  ]
}
```

---

## Rate Limiting

API может иметь ограничения по количеству запросов. При превышении лимита возвращается статус 429.

---

## Versioning

Текущая версия API: **v1**

Все endpoints версионируются через URL: `/api/v1/`



