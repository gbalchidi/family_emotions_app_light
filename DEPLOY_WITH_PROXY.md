# Деплой с TCP прокси для PostgreSQL

## Как это работает

В контейнере бота теперь запускаются 3 процесса:
1. **shadowsocks** - SOCKS5 прокси для Anthropic API (порт 1080)
2. **socat** - TCP прокси для PostgreSQL (порт 5432)  
3. **bot** - сам бот

Socat проксирует соединения:
- `localhost:5432` (внутри контейнера) → `POSTGRES_REAL_HOST:5432` (PostgreSQL в сети Coolify)

## Настройка в Coolify

### 1. Переменные окружения для бота

В настройках вашего бота в Coolify добавьте:

```env
# Telegram и Anthropic
TELEGRAM_BOT_TOKEN=ваш_токен
ANTHROPIC_API_KEY=ваш_ключ
USE_PROXY=true
PROXY_URL=socks5://127.0.0.1:1080

# База данных (через локальный прокси)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=analytics
DB_USER=analytics_user
DB_PASSWORD=&S9\sQ0>Y

# Реальный адрес PostgreSQL для socat
POSTGRES_REAL_HOST=10.0.1.7
```

**Важно:** 
- `DB_HOST=localhost` - бот подключается к локальному socat
- `POSTGRES_REAL_HOST=10.0.1.7` - socat проксирует к реальному PostgreSQL

### 2. Редеплой

После добавления переменных нажмите **Redeploy**.

## Проверка работы

### 1. Проверьте логи бота:

```bash
docker logs --tail 100 bot-vcs48g4s40sskk08o4s4o0o4-XXXXX
```

Должны увидеть:
- Запуск shadowsocks: `listening at 127.0.0.1:1080`
- Запуск postgres-proxy (socat)
- Подключение к базе: `Connected to database at localhost:5432/analytics`

### 2. Проверьте записи в базе:

```bash
# Найдите контейнер PostgreSQL
docker ps | grep postgres

# Проверьте количество событий
docker exec -it CONTAINER_ID psql -U analytics_user -d analytics -c "SELECT COUNT(*) FROM analytics_events;"
```

## Диагностика проблем

### Если база не подключается:

1. **Проверьте, что socat запустился:**
```bash
docker exec -it CONTAINER_ID ps aux | grep socat
```

2. **Проверьте доступность PostgreSQL из контейнера:**
```bash
docker exec -it CONTAINER_ID nc -zv 10.0.1.7 5432
```

3. **Проверьте переменную POSTGRES_REAL_HOST:**
```bash
docker exec -it CONTAINER_ID env | grep POSTGRES_REAL_HOST
```

### Если IP PostgreSQL изменился:

PostgreSQL в Coolify может получить новый IP при перезапуске. Проверьте актуальный:

```bash
docker inspect aggw440gs08404s0kos4ocw8 | grep IPAddress
```

И обновите `POSTGRES_REAL_HOST` в Coolify.

## Альтернативный вариант с именем хоста

Вместо IP можно попробовать использовать имя:

```env
POSTGRES_REAL_HOST=aggw440gs08404s0kos4ocw8.coolify
```

или

```env
POSTGRES_REAL_HOST=postgres-aggw440gs08404s0kos4ocw8
```

## Преимущества этого подхода

✅ База и бот в разных сетях, но могут общаться  
✅ Прокси для Anthropic API продолжает работать  
✅ При редеплое всё восстанавливается автоматически  
✅ Данные в PostgreSQL сохраняются  
✅ Не нужно открывать порты наружу