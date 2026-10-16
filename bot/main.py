"""Main Telegram bot handler for Habit Streak Bot"""
import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, time
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from sqlalchemy import func

from bot.models import (
    init_db, User, Habit, CheckIn, Achievement, UserAchievement,
    ReminderLog, DifficultyTier, HabitCategory, seed_achievements
)
from bot.avatar import generate_avatar, generate_heatmap, generate_streak_badge
from bot.achievements import check_achievements, get_achievement_message, format_achievement_card

load_dotenv()

logging.basicConfig(level=logging.INFO)
# httpx logs full request URLs, which include the bot token
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

NAME, DESCRIPTION, CATEGORY, DIFFICULTY, FREQUENCY, DEADLINE = range(6)
NOTE = 0

Session = init_db()


def get_session():
    return Session()


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    do_HEAD = do_GET

    def log_message(self, *args):
        pass


def start_health_server():
    """Open $PORT so hosts like Render see the service as live."""
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health server listening on port %s", port)


def get_or_create_user(session, telegram_user):
    user = session.query(User).filter_by(telegram_id=telegram_user.id).first()
    if not user:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name
        )
        session.add(user)
        session.commit()
    return user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        welcome_text = (
            "*Welcome to Habit Streak Bot, " + (user.first_name or "Warrior") + "!*\n\n"
            "I turn your daily routines into a game. Build streaks, earn XP, "
            "level up your avatar, and unlock achievements.\n\n"
            "*Quick commands:*\n"
            "/habits - View your habits\n"
            "/checkin - Check in for today\n"
            "/addhabit - Create a new habit\n"
            "/stats - Your stats and avatar\n"
            "/leaderboard - See who is winning\n\n"
            "Your avatar is waiting. Do not let it down."
        )
        avatar_bytes = generate_avatar(user.avatar_stage)
        await update.message.reply_photo(photo=avatar_bytes, caption=welcome_text, parse_mode="Markdown")
    finally:
        session.close()


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        habits = session.query(Habit).filter_by(user_id=user.id, is_active=True).all()
        total_checkins = session.query(CheckIn).filter_by(user_id=user.id).count()
        today = datetime.utcnow().date()
        today_checkins = session.query(CheckIn).filter(
            CheckIn.user_id == user.id,
            func.date(CheckIn.checked_at) == today
        ).count()
        habits_due_today = sum(1 for h in habits if h.should_check_in_today())
        completion_rate = (today_checkins / max(habits_due_today, 1)) * 100
        best_streak = 0
        for h in habits:
            if h.best_streak > best_streak:
                best_streak = h.best_streak
        profile_text = (
            "*" + (user.first_name or "Warrior") + "* - *" + user.title + "* (Level " + str(user.level) + ")\n\n"
            "*Stats:*\n"
            "- XP: " + str(user.total_xp) + " / " + str(user.xp_to_next_level()) + "\n"
            "- Total Check-ins: " + str(total_checkins) + "\n"
            "- Active Habits: " + str(len(habits)) + "\n"
            "- Best Streak: " + str(best_streak) + " days\n"
            "- Streak Freezes: " + str(user.streak_freezes) + "\n"
            "- Today Completion: " + str(int(completion_rate)) + "%\n\n"
            "*Achievements: " + str(len(user.achievements)) + "*"
        )
        avatar_bytes = generate_avatar(user.avatar_stage)
        await update.message.reply_photo(photo=avatar_bytes, caption=profile_text, parse_mode="Markdown")
    finally:
        session.close()


async def add_habit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Let us create a new habit!*\n\n"
        "What is the name of this habit?\n\n"
        "Examples: Morning Run, Read 10 Pages, Meditate",
        parse_mode="Markdown"
    )
    return NAME

async def add_habit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["habit_name"] = update.message.text
    await update.message.reply_text(
        "Got it! Now add a short description (or send /skip):",
        parse_mode="Markdown"
    )
    return DESCRIPTION

async def add_habit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["habit_description"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Health", callback_data="health")],
        [InlineKeyboardButton("Learning", callback_data="learning")],
        [InlineKeyboardButton("Social", callback_data="social")],
        [InlineKeyboardButton("Creative", callback_data="creative")],
        [InlineKeyboardButton("Discipline", callback_data="discipline")],
        [InlineKeyboardButton("Career", callback_data="career")],
        [InlineKeyboardButton("Other", callback_data="other")],
    ]
    await update.message.reply_text("Pick a category:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORY

async def add_habit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["habit_category"] = query.data
    keyboard = [
        [InlineKeyboardButton("Easy (+5 XP)", callback_data="easy")],
        [InlineKeyboardButton("Medium (+10 XP)", callback_data="medium")],
        [InlineKeyboardButton("Hard (+20 XP)", callback_data="hard")],
    ]
    await query.edit_message_text("How difficult is this habit?", reply_markup=InlineKeyboardMarkup(keyboard))
    return DIFFICULTY

async def add_habit_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["habit_difficulty"] = query.data
    keyboard = [
        [InlineKeyboardButton("Daily", callback_data="daily")],
        [InlineKeyboardButton("Weekdays", callback_data="weekdays")],
        [InlineKeyboardButton("Weekends", callback_data="weekend")],
        [InlineKeyboardButton("Custom (X/week)", callback_data="custom")],
    ]
    await query.edit_message_text("How often do you want to do this?", reply_markup=InlineKeyboardMarkup(keyboard))
    return FREQUENCY

async def add_habit_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["habit_frequency"] = query.data
    if query.data == "custom":
        await query.edit_message_text("How many times per week? (1-7)")
        return FREQUENCY
    await query.edit_message_text("What time is the deadline? (HH:MM, 24h format) Example: 23:59 or 08:00")
    return DEADLINE

async def add_habit_custom_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        times = int(update.message.text)
        if 1 <= times <= 7:
            context.user_data["habit_times_per_week"] = times
            await update.message.reply_text("What time is the deadline? (HH:MM, 24h format) Example: 23:59 or 08:00")
            return DEADLINE
        else:
            await update.message.reply_text("Please enter a number between 1 and 7.")
            return FREQUENCY
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return FREQUENCY

async def add_habit_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deadline = update.message.text
    try:
        datetime.strptime(deadline, "%H:%M")
    except ValueError:
        await update.message.reply_text("Invalid format. Please use HH:MM (e.g., 23:59)")
        return DEADLINE
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        habit = Habit(
            user_id=user.id,
            name=context.user_data["habit_name"],
            description=context.user_data.get("habit_description", ""),
            category=HabitCategory(context.user_data["habit_category"]),
            difficulty=DifficultyTier(context.user_data["habit_difficulty"]),
            frequency=context.user_data["habit_frequency"],
            times_per_week=context.user_data.get("habit_times_per_week", 7),
            deadline_time=deadline
        )
        session.add(habit)
        session.commit()
        xp = habit.xp_reward()
        await update.message.reply_text(
            "*Habit created!*\n\n"
            "*" + habit.name + "*\n"
            "- Category: " + habit.category.value.title() + "\n"
            "- Difficulty: " + habit.difficulty.value.title() + "\n"
            "- Frequency: " + habit.frequency.title() + "\n"
            "- Deadline: " + deadline + "\n"
            "- XP per check-in: +" + str(xp) + "\n\n"
            "Use /checkin to start your streak!",
            parse_mode="Markdown"
        )
    finally:
        session.close()
    return ConversationHandler.END

async def cancel_add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Habit creation cancelled.")
    return ConversationHandler.END


async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        habits = session.query(Habit).filter_by(user_id=user.id, is_active=True).all()
        if not habits:
            await update.message.reply_text("You do not have any habits yet! Create one with /addhabit", parse_mode="Markdown")
            return
        today = datetime.utcnow().date()
        keyboard = []
        for habit in habits:
            if not habit.should_check_in_today():
                continue
            already_checked = session.query(CheckIn).filter(
                CheckIn.habit_id == habit.id,
                func.date(CheckIn.checked_at) == today
            ).first()
            if already_checked:
                label = habit.name + " (" + str(habit.current_streak) + " streak)"
                callback = "already_" + str(habit.id)
            else:
                label = habit.name
                callback = "checkin_" + str(habit.id)
            keyboard.append([InlineKeyboardButton(label, callback_data=callback)])
        if not keyboard:
            await update.message.reply_text("All habits are done for today! Take a breather.", parse_mode="Markdown")
            return
        keyboard.append([InlineKeyboardButton("Add note to check-in", callback_data="add_note")])
        await update.message.reply_text(
            "*What did you accomplish?*\n\nTap to check in:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    finally:
        session.close()

async def handle_checkin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("already_"):
        await query.edit_message_text("You already checked in for that habit today!")
        return
    if data.startswith("checkin_"):
        habit_id = int(data.split("_")[1])
        session = get_session()
        try:
            user = get_or_create_user(session, update.effective_user)
            habit = session.query(Habit).filter_by(id=habit_id, user_id=user.id).first()
            if not habit:
                await query.edit_message_text("Habit not found!")
                return
            now = datetime.utcnow()
            last_checkin = session.query(CheckIn).filter_by(habit_id=habit.id).order_by(CheckIn.checked_at.desc()).first()
            if last_checkin:
                last_date = last_checkin.checked_at.date()
                today = now.date()
                yesterday = today - timedelta(days=1)
                if last_date == today:
                    await query.edit_message_text("You already checked in for *" + habit.name + "* today!", parse_mode="Markdown")
                    return
                elif last_date == yesterday:
                    habit.current_streak += 1
                else:
                    old_streak = habit.current_streak
                    habit.current_streak = 1
            else:
                habit.current_streak = 1
            if habit.current_streak > habit.best_streak:
                habit.best_streak = habit.current_streak
            habit.total_checkins += 1
            xp_earned = habit.xp_reward()
            checkin = CheckIn(
                user_id=user.id,
                habit_id=habit.id,
                xp_earned=xp_earned,
                streak_at_checkin=habit.current_streak
            )
            session.add(checkin)
            leveled_up = user.add_xp(xp_earned)
            new_achievements = check_achievements(user, session)
            session.commit()
            response = (
                "*" + habit.name + "* - Checked in!\n\n"
                "Current streak: *" + str(habit.current_streak) + " days*\n"
                "XP earned: +" + str(xp_earned) + "\n"
                "Total XP: " + str(user.total_xp) + " / " + str(user.xp_to_next_level())
            )
            if leveled_up:
                response += "\n\n*LEVEL UP!* You are now Level " + str(user.level) + " - " + user.title + "!"
                avatar_bytes = generate_avatar(user.avatar_stage)
                await query.edit_message_text(response, parse_mode="Markdown")
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=avatar_bytes,
                    caption="Your avatar has evolved! Welcome to Level " + str(user.level) + "!"
                )
            else:
                await query.edit_message_text(response, parse_mode="Markdown")
            for achievement in new_achievements:
                msg = get_achievement_message(achievement)
                card = format_achievement_card(achievement)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="*ACHIEVEMENT UNLOCKED!*\n\n" + card + "\n\n_" + msg + "_",
                    parse_mode="Markdown"
                )
            if habit.current_streak in [7, 14, 30, 50, 100]:
                badge = generate_streak_badge(habit.current_streak)
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=badge,
                    caption="*" + str(habit.current_streak) + "-DAY STREAK!*\n\nKeep the fire burning for *" + habit.name + "*!"
                )
        finally:
            session.close()


async def habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        habits_list = session.query(Habit).filter_by(user_id=user.id, is_active=True).all()
        if not habits_list:
            await update.message.reply_text("No habits yet! Create your first with /addhabit", parse_mode="Markdown")
            return
        today = datetime.utcnow().date()
        text = "*Your Habits*\n\n"
        for habit in habits_list:
            done_today = session.query(CheckIn).filter(
                CheckIn.habit_id == habit.id,
                func.date(CheckIn.checked_at) == today
            ).first()
            status = "DONE" if done_today else "TODO"
            streak_text = " (" + str(habit.current_streak) + " streak)" if habit.current_streak > 0 else ""
            text += status + " *" + habit.name + "*" + streak_text + "\n"
            text += "  - " + habit.difficulty.value.title() + " | " + habit.frequency.title() + "\n"
            text += "  - Best: " + str(habit.best_streak) + " | Total: " + str(habit.total_checkins) + "\n"
            text += "  - Deadline: " + habit.deadline_time + "\n\n"
        keyboard = [
            [InlineKeyboardButton("Add New Habit", callback_data="add_habit")],
            [InlineKeyboardButton("View Stats", callback_data="view_stats")],
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    finally:
        session.close()


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        habits = session.query(Habit).filter_by(user_id=user.id, is_active=True).all()
        checkins = session.query(CheckIn).filter_by(user_id=user.id).order_by(CheckIn.checked_at.desc()).limit(100).all()
        heatmap = generate_heatmap(checkins, habits, days=30)
        total_checkins = session.query(CheckIn).filter_by(user_id=user.id).count()
        best_streak = 0
        for h in habits:
            if h.best_streak > best_streak:
                best_streak = h.best_streak
        current_streaks = [h.current_streak for h in habits if h.current_streak > 0]
        avg_streak = sum(current_streaks) / len(current_streaks) if current_streaks else 0
        stats_text = (
            "*Your Stats* - " + user.title + " (Level " + str(user.level) + ")\n\n"
            "*Streaks:*\n"
            "- Best Ever: " + str(best_streak) + " days\n"
            "- Active Streaks: " + str(len(current_streaks)) + "\n"
            "- Average: " + str(round(avg_streak, 1)) + " days\n\n"
            "*Activity:*\n"
            "- Total Check-ins: " + str(total_checkins) + "\n"
            "- XP: " + str(user.total_xp) + " / " + str(user.xp_to_next_level()) + "\n"
            "- Active Habits: " + str(len(habits)) + "\n\n"
            "*Achievements: " + str(len(user.achievements)) + "*"
        )
        await update.message.reply_photo(photo=heatmap, caption=stats_text, parse_mode="Markdown")
    finally:
        session.close()


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        top_users = session.query(User).order_by(User.level.desc(), User.total_xp.desc()).limit(10).all()
        text = "*Global Leaderboard*\n\n"
        for i, u in enumerate(top_users, 1):
            name = u.first_name or u.username or ("User " + str(u.telegram_id))
            text += str(i) + ". *" + name + "* - Lv." + str(u.level) + " " + u.title + " (" + str(u.total_xp) + " XP)\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Reminder Time", callback_data="set_reminder")],
        [InlineKeyboardButton("Summary Time", callback_data="set_summary")],
        [InlineKeyboardButton("Timezone", callback_data="set_timezone")],
    ]
    await update.message.reply_text(
        "*Settings*\n\nCustomize your Habit Streak experience:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*Habit Streak Bot - Help*\n\n"
        "*Commands:*\n"
        "/start - Welcome and overview\n"
        "/habits - View all your habits\n"
        "/checkin - Check in for today\n"
        "/addhabit - Create a new habit\n"
        "/stats - Stats, heatmap and avatar\n"
        "/profile - Your full profile\n"
        "/leaderboard - Global rankings\n"
        "/settings - Customize bot\n"
        "/help - This message\n\n"
        "*How it works:*\n"
        "1. Create habits with /addhabit\n"
        "2. Check in daily with /checkin\n"
        "3. Build streaks, earn XP, level up\n"
        "4. Unlock achievements and evolve your avatar\n\n"
        "*Streak Rules:*\n"
        "- Check in before your deadline\n"
        "- 2-hour grace period after deadline\n"
        "- Miss a day = streak breaks (unless you use a freeze)\n"
        "- Rest days depend on your habit frequency\n\n"
        "*XP System:*\n"
        "- Easy habits: +5 XP\n"
        "- Medium habits: +10 XP\n"
        "- Hard habits: +20 XP\n"
        "- Level up every 100 * level^1.5 XP\n\n"
        "Need more help? Just ask!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")
        users = session.query(User).all()
        for user in users:
            if user.reminder_time == current_time:
                habits = session.query(Habit).filter_by(user_id=user.id, is_active=True).all()
                due_habits = [h for h in habits if h.should_check_in_today()]
                if due_habits:
                    habit_names = ", ".join([h.name for h in due_habits[:3]])
                    if len(due_habits) > 3:
                        habit_names += " and " + str(len(due_habits) - 3) + " more"
                    await context.bot.send_message(
                        chat_id=user.telegram_id,
                        text=(
                            "Good morning, " + (user.first_name or "Warrior") + "!\n\n"
                            "Today's quests: " + habit_names + "\n\n"
                            "Use /checkin to start your streak!"
                        ),
                        parse_mode="Markdown"
                    )
            if user.summary_time == current_time:
                habits = session.query(Habit).filter_by(user_id=user.id, is_active=True).all()
                today = now.date()
                completed = 0
                missed = []
                for habit in habits:
                    if not habit.should_check_in_today():
                        continue
                    checked = session.query(CheckIn).filter(
                        CheckIn.habit_id == habit.id,
                        func.date(CheckIn.checked_at) == today
                    ).first()
                    if checked:
                        completed += 1
                    else:
                        missed.append(habit.name)
                if missed:
                    text = "Evening Report\n\n"
                    text += "Completed: " + str(completed) + "\n"
                    text += "Still open: " + ", ".join(missed) + "\n\n"
                    for habit_name in missed[:2]:
                        text += habit_name + " is waiting...\n"
                    text += "\nDo not let the streak die! /checkin"
                else:
                    text = "Evening Report\n\n"
                    text += "All habits complete! " + str(completed) + "/" + str(completed) + "\n\n"
                    text += "Perfect day! Your avatar is proud."
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    parse_mode="Markdown"
                )
    finally:
        session.close()


def main():
    session = get_session()
    try:
        seed_achievements(session)
    finally:
        session.close()

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not set! Please set it as an environment variable.")
        return

    application = Application.builder().token(token).build()

    add_habit_conv = ConversationHandler(
        entry_points=[CommandHandler("addhabit", add_habit_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_description)],
            CATEGORY: [CallbackQueryHandler(add_habit_category, pattern="^(health|learning|social|creative|discipline|career|other)$")],
            DIFFICULTY: [CallbackQueryHandler(add_habit_difficulty, pattern="^(easy|medium|hard)$")],
            FREQUENCY: [
                CallbackQueryHandler(add_habit_frequency, pattern="^(daily|weekdays|weekend|custom)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_custom_frequency)
            ],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_deadline)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_habit)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("habits", habits))
    application.add_handler(CommandHandler("checkin", checkin))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(add_habit_conv)
    application.add_handler(CallbackQueryHandler(handle_checkin_callback, pattern="^(checkin_|already_|add_)"))

    job_queue = application.job_queue
    job_queue.run_repeating(send_reminders, interval=60, first=10)

    start_health_server()
    logger.info("Starting Habit Streak Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
