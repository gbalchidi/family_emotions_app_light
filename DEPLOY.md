# Deployment Instructions for Coolify

## Prerequisites

1. Coolify installed on your server
2. GitHub repository connected to Coolify
3. Telegram Bot Token from @BotFather
4. Anthropic API Key

## Deployment Steps

### 1. Environment Variables in Coolify

Add these environment variables in Coolify dashboard:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
ENVIRONMENT=production
LOG_LEVEL=INFO

# If your server is in a region where Anthropic API is blocked:
USE_PROXY=true
PROXY_URL=socks5://host.docker.internal:1080
# Adjust port 1080 to your shadowsocks/proxy port
```

### 2. Coolify Configuration

1. **Source**: GitHub repository `https://github.com/gbalchidi/family_emotions_app_light`
2. **Branch**: main
3. **Build Pack**: Docker Compose
4. **Compose File**: docker-compose.coolify.yml

### 3. Deploy

1. Push code to GitHub
2. Trigger deployment in Coolify
3. Monitor logs for successful startup

### 4. Verify Bot

1. Open Telegram
2. Search for your bot username
3. Send `/start` command
4. Test phrase analysis

## Monitoring

Check bot logs:
```bash
docker logs emotions-translator-bot
```


## Troubleshooting

### Bot not responding
- Check TELEGRAM_BOT_TOKEN is correct
- Verify bot is running: `docker ps`
- Check logs for errors

### Analysis not working
- Verify ANTHROPIC_API_KEY is valid
- Check API rate limits
- Monitor logs for API errors

