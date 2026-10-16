# 🔥 Habit Streak Bot

A gamified Telegram bot that turns your daily routines into an RPG-style streak tracker. Build habits, earn XP, level up your avatar, and unlock achievements.

## Features

- **🎯 Habit Tracking** — Create habits with custom difficulty, frequency, and deadlines
- **🔥 Streak System** — Build and maintain streaks with grace periods and rest days
- **⭐ XP & Leveling** — Earn XP for check-ins, level up, and evolve your pixel avatar
- **🏆 Achievements** — Unlock 14+ achievements with fun descriptions
- **📊 Visual Analytics** — Heatmaps, streak badges, and progress stats
- **⏰ Smart Reminders** — Morning reminders and evening summaries
- **🥇 Leaderboards** — Compete globally or with friends
- **❄️ Streak Freezes** — Save your streak when life gets in the way

## Quick Start

### 1. Get a Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy your bot token

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your BOT_TOKEN
```

### 4. Run the Bot

```bash
python run.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and overview |
| `/addhabit` | Create a new habit (interactive) |
| `/habits` | View all your habits |
| `/checkin` | Check in for today's habits |
| `/stats` | Stats, heatmap, and avatar |
| `/profile` | Full profile with avatar |
| `/leaderboard` | Global rankings |
| `/settings` | Customize reminders and timezone |
| `/help` | Detailed help message |

## Habit Configuration

### Difficulty Tiers
- 🟢 **Easy** — +5 XP per check-in
- 🟡 **Medium** — +10 XP per check-in
- 🔴 **Hard** — +20 XP per check-in

### Frequency Options
- **Daily** — Every day
- **Weekdays** — Monday-Friday
- **Weekends** — Saturday-Sunday
- **Custom** — X times per week (1-7)

### Streak Rules
- Check in before your deadline (default: 23:59)
- 2-hour grace period after deadline
- Miss a day = streak breaks (unless you use a freeze)
- Rest days based on your frequency setting

## XP & Level System

- XP to next level: `100 × level^1.5`
- Level milestones unlock titles and avatar stages:
  - Level 1: Novice
  - Level 5: Apprentice
  - Level 10: Warrior
  - Level 20: Knight
  - Level 30: Champion
  - Level 50: Legend
  - Level 75: Mythic
  - Level 100: Immortal

## Avatar Stages

Your pixel avatar evolves as you level up:
- Stage 1: Basic character
- Stage 2: Belt and pants
- Stage 3: Sword
- Stage 4: Cape
- Stage 5: Crown and aura
- Stage 6: Wings

## Achievements

| Achievement | Condition | XP Reward |
|-------------|-----------|-----------|
| First Step | 1st check-in | +10 |
| 7-Day Warrior | 7-day streak | +50 |
| 30-Day Champion | 30-day streak | +200 |
| Centurion | 100 total check-ins | +100 |
| Comeback Kid | Restart after break | - |
| Jack of All Trades | 5 active habits | +75 |
| Early Bird | Check in before 7am | +25 |
| Night Owl | Check in after 10pm | +25 |
| Health Nut | 50 health check-ins | +100 |
| Scholar | 50 learning check-ins | +100 |
| Social Butterfly | 50 social check-ins | +100 |
| Level 5 | Reach level 5 | +50 |
| Level 20 | Reach level 20 | +200 |
| Level 50 | Reach level 50 | +500 |

## Project Structure

```
habit_streak_bot/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Bot handlers & commands
│   ├── models.py        # Database models
│   ├── avatar.py        # Avatar & heatmap generator
│   └── achievements.py  # Achievement engine
├── assets/              # Static assets (if needed)
├── run.py              # Entry point
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Database

Uses SQLAlchemy with SQLite by default. Supports PostgreSQL for production.

```bash
# Default (unset): local SQLite file habit_streak.db
# Absolute SQLite path (note the 4 slashes)
DATABASE_URL=sqlite:////data/habit_streak.db

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/habitstreak
```

## Deployment

### VPS / Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run with systemd or screen/tmux
python run.py
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

### Render

Deploy as a Web Service (Docker). The bot opens a small health endpoint on `$PORT`
so Render sees it as live. Render's free tier has no persistent disk, so attach a
Render Postgres database and set `DATABASE_URL` to its Internal Database URL,
otherwise data resets on every restart.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token (required) | - |
| `DATABASE_URL` | Database connection string | `sqlite:///habit_streak.db` |
| `ADMIN_USER_ID` | Admin Telegram ID for management | - |

## Customization

### Bot Personality

Edit the response messages in `bot/main.py` to change the bot's tone. The default is a supportive but slightly sarcastic gym coach.

### Achievement Messages

Edit `bot/achievements.py` to customize achievement unlock messages.

### Avatar Colors

Modify `bot/avatar.py` to change pixel art color palettes.

## License

MIT License — feel free to use, modify, and share!

---

Built with ❤️ and 🔥 for people who want to build better habits.
