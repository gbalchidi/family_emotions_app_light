# Emotions Translator Bot

Telegram bot that helps parents understand the hidden emotional meaning behind their children's phrases.

## Features

- 🔍 Phrase analysis - Decode what your child really means
- 📊 Emotional context - Understand underlying feelings
- 💬 Response suggestions - Get constructive reply options
- 📚 Common examples - Learn from typical scenarios
- 🔒 Privacy-first - No data storage, anonymous processing

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Anthropic API Key

### Installation

1. Clone the repository:
```bash
cd /Users/glebbalcidi/Deployments/emotions-translator-bot
```

2. Install dependencies:
```bash
pip install poetry
poetry install
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your tokens
```

4. Run the bot:
```bash
poetry run python -m src.main
```

### Docker Deployment

```bash
docker-compose up -d
```

## Architecture

The bot follows Domain-Driven Design (DDD) principles:

```
src/
├── domain/           # Core business logic
├── application/      # Use cases and services
├── infrastructure/   # External integrations
└── presentation/     # Telegram interface
```

## Usage

1. Start bot with `/start`
2. Choose "🔍 Decode phrase" 
3. Send child's phrase
4. Get emotional analysis and response suggestions

## Testing

```bash
poetry run pytest
```

## License

MIT