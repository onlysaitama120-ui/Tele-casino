# 🎰 Casino Bot - Professional Telegram Mini App
# its a demo project to be turned into nft based game for tele.

A fully-featured casino bot with NFT items, case opening, roulette, slots, breeding, and marketplace.

## 🚀 Features

### Games
- **📦 Case Opening** - 4 case tiers (Bronze, Silver, Gold, Diamond)
- **🎡 Roulette** - Red/Black/Green with multipliers
- **🎰 Slots** - Classic slot machine with jackpots
- **🧬 Breeding** - Combine items to create new ones

### Economy
- **💰 Virtual Wallet** - Coins for all transactions
- **🎁 Daily Rewards** - Claim every 24h with streak bonuses
- **👥 Referral System** - Earn coins for inviting friends
- **🛒 Marketplace** - Buy/sell items with other players

### Progression
- **📊 Levels & XP** - Gain XP from playing
- **🏅 Achievements** - Unlock achievements for milestones
- **🏆 Leaderboards** - Compete with other players
- **📦 Inventory** - Collect and manage your items

## 📁 Project Structure

```
telegram-casino/
├── run.py              # Main entry point
├── config.py           # All settings
├── requirements.txt    # Dependencies
├── db/                 # Database models
│   ├── __init__.py     # All models
│   └── engine.py       # DB connection
├── api/                # Game logic + API
│   ├── __init__.py     # Core game engine
│   └── server.py       # FastAPI routes
├── bot/                # Telegram bot
│   └── __init__.py     # All handlers
└── miniapp/            # Web game UI
    ├── index.html      # Main page
    └── static/
        ├── style.css   # Styling
        └── game.js     # Game logic
```

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Bot
Edit `config.py`:
```python
BOT_TOKEN = "your_bot_token"  # From @BotFather
BOT_USERNAME = "your_bot"
WEBAPP_URL = "https://yourdomain.com"
ADMIN_IDS = [your_telegram_id]
```

### 3. Run Bot
```bash
python run.py
```

### 4. Test Locally
- Open `http://localhost:8000` in browser
- Mini app will load for testing

## 🌐 Deployment

### Option 1: VPS (Recommended)
```bash
# On your VPS
git clone <repo>
cd telegram-casino
pip install -r requirements.txt

# Run with screen/tmux
screen -S casino
python run.py
# Ctrl+A, D to detach

# Or use systemd service
```

### Option 2: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "run.py"]
```

### Option 3: Heroku
```bash
heroku create your-app
git push heroku main
```

## 💳 Payment Integration

### Telegram Stars (Recommended)
Built-in Telegram payment system. Users pay with Telegram Stars.

### Crypto (NOWPayments)
1. Register at nowpayments.io
2. Get API key
3. Add to `config.py`

## 🎮 Game Mechanics

### Case Opening
- Roll random items based on probabilities
- Rarity tiers: Common → Uncommon → Rare → Epic → Legendary → Mythic → Divine
- Higher tier cases = better odds for rare items

### Roulette
- Bet on Red (2x), Black (2x), or Green (14x)
- Provably fair system
- Min bet: 50, Max bet: 50,000

### Slots
- Match symbols for multipliers
- 3-of-a-kind pays most
- Jackpot on 🎰🎰🎰 (100x)

### Breeding
- Combine two items of same rarity
- Chance to upgrade to next rarity
- Costs coins + cooldown

## 📊 Admin Commands

```
/admin - Admin panel
/admin_balance @username - Check balance
/admin_give @username 1000 - Give coins
/admin_broadcast message - Send to all users
```

## 🔧 Customization

### Add New Cases
Edit `config.py` → `CASES` dict:
```python
"my_case": {
    "name": "My Case",
    "price": 1000,
    "emoji": "🎁",
    "color": "#FF0000",
    "items": [
        {"name": "Item", "rarity": "rare", "chance": 10, "value": 500, "emoji": "💎"},
    ]
}
```

### Change Economy
Edit values in `config.py`:
```python
INITIAL_COINS = 1000
DAILY_REWARD = 100
REFERRAL_BONUS = 200
```

## 🛡️ Security

- Verify Telegram init_data
- Server-side game logic
- Rate limiting recommended
- Input validation on all endpoints

## 📈 Scaling

- SQLite for small scale (<10K users)
- PostgreSQL for larger scale
- Redis for caching
- Load balancer for multiple instances

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding | Check BOT_TOKEN |
| Mini app not loading | Check WEBAPP_URL |
| Database errors | Delete db/casino.db to reset |
| Payment failing | Verify API keys |

## 📝 License

MIT License - Use freely for your projects.

---

Built with ❤️ for Telegram
