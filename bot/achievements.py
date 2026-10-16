"""Achievement engine for Habit Streak Bot"""
from datetime import datetime, time
from sqlalchemy import func
from bot.models import Achievement, UserAchievement, CheckIn, Habit

def check_achievements(user, session):
    """Check and award new achievements for a user"""
    new_achievements = []

    all_achievements = session.query(Achievement).all()
    earned_ids = {ua.achievement_id for ua in user.achievements}

    for achievement in all_achievements:
        if achievement.id in earned_ids:
            continue

        earned = False

        if achievement.condition_type == "total_checkins":
            total = session.query(CheckIn).filter_by(user_id=user.id).count()
            if total >= achievement.condition_value:
                earned = True

        elif achievement.condition_type == "streak":
            habits = session.query(Habit).filter_by(user_id=user.id).all()
            for habit in habits:
                if habit.current_streak >= achievement.condition_value:
                    earned = True
                    break

        elif achievement.condition_type == "level":
            if user.level >= achievement.condition_value:
                earned = True

        elif achievement.condition_type == "habit_count":
            habit_count = session.query(Habit).filter_by(user_id=user.id, is_active=True).count()
            if habit_count >= achievement.condition_value:
                earned = True

        elif achievement.condition_type == "early_checkin":
            early = session.query(CheckIn).filter(
                CheckIn.user_id == user.id,
                func.extract('hour', CheckIn.checked_at) < 7
            ).first()
            if early:
                earned = True

        elif achievement.condition_type == "late_checkin":
            late = session.query(CheckIn).filter(
                CheckIn.user_id == user.id,
                func.extract('hour', CheckIn.checked_at) >= 22
            ).first()
            if late:
                earned = True

        elif achievement.condition_type == "category_checkins":
            category_map = {
                "Health Nut": "health",
                "Scholar": "learning",
                "Social Butterfly": "social"
            }
            category_name = category_map.get(achievement.name)
            if category_name:
                count = session.query(CheckIn).join(Habit).filter(
                    CheckIn.user_id == user.id,
                    Habit.category == category_name
                ).count()
                if count >= achievement.condition_value:
                    earned = True

        if earned:
            ua = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            session.add(ua)
            user.add_xp(achievement.xp_reward)
            new_achievements.append(achievement)

    session.commit()
    return new_achievements


def get_achievement_message(achievement):
    """Generate a fun message for earning an achievement"""
    messages = {
        "First Step": "Every legend starts with a single step. Yours just happened!",
        "7-Day Warrior": "A week of fire! Your consistency is becoming dangerous.",
        "30-Day Champion": "A whole month! You are now officially someone who does things.",
        "Centurion": "100 check-ins. That is not luck, that is a lifestyle.",
        "Comeback Kid": "Fell down, got up. The most important streak is the one you restarted.",
        "Jack of All Trades": "Five habits?! You are basically a Renaissance person now.",
        "Early Bird": "Up before the sun. The worms are terrified of you.",
        "Night Owl": "Burning the midnight oil. Or just really good at procrastinating productively.",
        "Health Nut": "Your body is basically a temple at this point.",
        "Scholar": "Your brain is getting swole. Intellectual gains only.",
        "Social Butterfly": "Making connections, one check-in at a time.",
        "Level 5": "Novice no more. You are an Apprentice now - time to learn some real spells.",
        "Level 20": "Knight status achieved. The cape is in the mail.",
        "Level 50": "LEGEND. Your avatar is glowing. People are writing songs about you.",
    }

    return messages.get(achievement.name, "Achievement unlocked: " + achievement.name + "!")


def format_achievement_card(achievement):
    """Format an achievement for display"""
    return (
        achievement.icon + " *" + achievement.name + "*\n"
        "_" + achievement.description + "_\n"
        "+" + str(achievement.xp_reward) + " XP"
    )
