# Инструкция по деплою базы данных для аналитики

## Шаги для развертывания на Coolify:

### 1. Подготовка окружения

В вашем `.env` файле добавьте параметры базы данных:
```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=analytics
DB_USER=analytics_user
DB_PASSWORD=ваш_секретный_пароль_здесь
```

### 2. Локальный запуск для тестирования

```bash
# Запустить базу данных и бота
docker-compose up -d

# Проверить логи
docker-compose logs -f

# Посмотреть события в базе данных
docker exec -it emotions-analytics-db psql -U analytics_user -d analytics -c "SELECT * FROM analytics_events ORDER BY created_at DESC LIMIT 10;"
```

### 3. Деплой на Coolify

#### Вариант А: Docker Compose (рекомендуется)

1. В Coolify создайте новый проект типа "Docker Compose"
2. Вставьте содержимое `docker-compose.yml`
3. В настройках окружения добавьте переменную:
   - `DB_PASSWORD=ваш_секретный_пароль`
4. Нажмите "Deploy"

#### Вариант Б: Отдельные сервисы

1. **Создайте PostgreSQL базу данных в Coolify:**
   - Add Resource → Database → PostgreSQL
   - Установите параметры:
     - Database: `analytics`
     - User: `analytics_user`
     - Password: задайте пароль
   - Deploy

2. **Обновите настройки бота:**
   - В настройках вашего бота в Coolify
   - Добавьте environment переменные:
     ```
     DB_HOST=имя_сервиса_postgres_из_coolify
     DB_PORT=5432
     DB_NAME=analytics
     DB_USER=analytics_user
     DB_PASSWORD=ваш_пароль
     ```

3. **Пересоберите и задеплойте бота**

### 4. Проверка работы

После деплоя подключитесь к серверу по SSH:

```bash
# Найти контейнер с базой данных
docker ps | grep postgres

# Подключиться к базе
docker exec -it [container_id] psql -U analytics_user -d analytics

# В psql консоли проверить события:
SELECT COUNT(*) FROM analytics_events;
SELECT event_data->>'event', COUNT(*) FROM analytics_events GROUP BY event_data->>'event';
SELECT * FROM analytics_events ORDER BY created_at DESC LIMIT 5;
```

### 5. Мониторинг

Полезные SQL запросы для аналитики:

```sql
-- Количество событий по типам
SELECT 
    event_data->>'event' as event_type,
    COUNT(*) as count
FROM analytics_events
GROUP BY event_type
ORDER BY count DESC;

-- События по пользователям
SELECT 
    event_data->'properties'->>'user_id' as user_id,
    COUNT(*) as events_count
FROM analytics_events
GROUP BY user_id
ORDER BY events_count DESC;

-- События за последний час
SELECT * FROM analytics_events
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;

-- Среднее время ответа API
SELECT 
    AVG((event_data->'properties'->>'response_time_ms')::int) as avg_response_time
FROM analytics_events
WHERE event_data->>'event' = 'decode_completed';
```

## Структура базы данных

Таблица `analytics_events`:
- `id` - автоинкрементный первичный ключ
- `event_data` - JSONB с полными данными события
- `created_at` - временная метка создания записи

Индексы для быстрых запросов:
- По типу события
- По user_id
- По timestamp события
- По created_at

## Безопасность

⚠️ **Важно:**
- Используйте сильный пароль для базы данных
- Не открывайте порт 5432 наружу без необходимости
- Регулярно делайте бэкапы базы данных
- Следите за размером базы (каждое событие ~500 байт)