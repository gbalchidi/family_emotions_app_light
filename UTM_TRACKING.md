# UTM Tracking Documentation

## Overview
The bot now supports UTM parameter tracking for marketing analytics. UTM parameters are automatically extracted from Telegram deep links and stored in the analytics database.

## How It Works

### 1. Link Format
Telegram deep links with UTM parameters should be formatted as:
```
https://t.me/YOUR_BOT_USERNAME?start=utm_source-VALUE_utm_medium-VALUE_utm_campaign-VALUE
```

### 2. Examples

#### Google Ads Campaign
```
https://t.me/family_emotions_bot?start=utm_source-google_utm_medium-cpc_utm_campaign-summer2024
```

#### Facebook Campaign
```
https://t.me/family_emotions_bot?start=utm_source-facebook_utm_medium-social_utm_campaign-awareness
```

#### Email Newsletter
```
https://t.me/family_emotions_bot?start=utm_source-newsletter_utm_medium-email_utm_campaign-weekly
```

#### Instagram Bio Link
```
https://t.me/family_emotions_bot?start=utm_source-instagram_utm_medium-social_utm_campaign-bio
```

### 3. Supported Parameters
- `utm_source` - The source of traffic (google, facebook, instagram, etc.)
- `utm_medium` - The marketing medium (cpc, social, email, etc.)
- `utm_campaign` - The campaign name
- `utm_term` - Optional: Keywords for paid search
- `utm_content` - Optional: To differentiate similar content/links

### 4. Parameter Format Rules
- Use hyphens (`-`) instead of spaces
- Use underscores (`_`) to separate different UTM parameters
- No special characters except hyphens and underscores
- Keep values lowercase for consistency

### 5. What Gets Tracked

When a user starts the bot with UTM parameters, the following is stored:
```json
{
  "event": "bot_started",
  "properties": {
    "user_id": "123456789",
    "timestamp": "2024-01-15T10:30:00",
    "source": "google",
    "utm_source": "google",
    "utm_medium": "cpc",
    "utm_campaign": "summer2024",
    "platform": "telegram",
    "language": "ru",
    "session_id": "uuid-here"
  }
}
```

### 6. Database Query Examples

#### Get all users from Google Ads:
```sql
SELECT COUNT(DISTINCT event_data->'properties'->>'user_id') 
FROM analytics_events 
WHERE event_data->>'event' = 'bot_started' 
AND event_data->'properties'->>'utm_source' = 'google';
```

#### Get conversion rate by source:
```sql
WITH starts AS (
  SELECT 
    event_data->'properties'->>'utm_source' as source,
    COUNT(DISTINCT event_data->'properties'->>'user_id') as users
  FROM analytics_events 
  WHERE event_data->>'event' = 'bot_started'
  GROUP BY 1
),
conversions AS (
  SELECT 
    event_data->'properties'->>'utm_source' as source,
    COUNT(DISTINCT event_data->'properties'->>'user_id') as converted
  FROM analytics_events 
  WHERE event_data->>'event' = 'decode_completed'
  GROUP BY 1
)
SELECT 
  s.source,
  s.users,
  c.converted,
  ROUND(100.0 * c.converted / s.users, 2) as conversion_rate
FROM starts s
LEFT JOIN conversions c ON s.source = c.source
ORDER BY s.users DESC;
```

### 7. Testing

To test UTM tracking locally:
1. Start the bot
2. Send `/start utm_source-test_utm_medium-debug_utm_campaign-local`
3. Check the analytics log or database for the tracked parameters

### 8. Implementation Details

The UTM extraction happens in:
- `src/presentation/handlers.py` - `start_command` method extracts parameters
- `src/infrastructure/analytics.py` - `track_bot_started` method stores parameters

## Changes Made (2024-09-17)

1. **handlers.py**: Updated `start_command` to parse UTM parameters from the start command
2. **analytics.py**: Updated `track_bot_started` to accept and store UTM parameters
3. All UTM parameters are now properly stored in the `analytics_events` table