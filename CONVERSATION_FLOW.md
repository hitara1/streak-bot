# Habit Streak Bot — Conversation Flow

## /start
User sends /start
→ Bot sends welcome message with avatar (Stage 1)
→ Shows quick commands list

## /addhabit (Conversation Handler)
1. Bot asks: "What's the name of this habit?"
   → User types name

2. Bot asks: "Add a short description (or /skip)"
   → User types description or /skip

3. Bot shows category buttons:
   [💪 Health] [📚 Learning] [🦋 Social]
   [🎨 Creative] [🎯 Discipline] [💼 Career] [🎲 Other]
   → User taps category

4. Bot shows difficulty buttons:
   [🟢 Easy (+5 XP)] [🟡 Medium (+10 XP)] [🔴 Hard (+20 XP)]
   → User taps difficulty

5. Bot shows frequency buttons:
   [📅 Daily] [📆 Weekdays] [🌅 Weekends] [🔢 Custom (X/week)]
   → User taps frequency
   → If Custom: Bot asks for number (1-7)

6. Bot asks: "What time is the deadline? (HH:MM)"
   → User types time (e.g., 23:59)

7. Bot creates habit and confirms with summary

## /checkin
User sends /checkin
→ Bot shows inline keyboard with habits:
   [⬜ Morning Run] [✅ Meditation (12🔥)]
   [⬜ Read 10 Pages]
   [📝 Add note to check-in]

→ User taps unchecked habit
→ Bot processes check-in:
   - Updates streak
   - Awards XP
   - Checks for level up
   - Checks for achievements
   - Checks for streak milestones

→ Bot sends response:
   ✅ Morning Run — Checked in!
   🔥 Current streak: 5 days
   ⭐ XP earned: +10
   📊 Total XP: 45 / 100

→ If level up: Sends new avatar
→ If achievement: Sends achievement card
→ If milestone (7/14/30/50/100 days): Sends streak badge image

## /habits
User sends /habits
→ Bot lists all active habits with status:
   ✅ Morning Run (5🔥)
      ├ Medium | Daily
      ├ Best: 12🔥 | Total: 45
      └ Deadline: 08:00

   ⬜ Read 10 Pages
      ├ Easy | Daily
      ├ Best: 3🔥 | Total: 12
      └ Deadline: 23:59

→ Shows buttons: [➕ Add New Habit] [📊 View Stats]

## /stats
User sends /stats
→ Bot generates heatmap image (last 30 days)
→ Bot sends heatmap with stats text:
   📊 Your Stats — Apprentice (Level 5)

   🔥 Streaks:
   ├ Best Ever: 12 days
   ├ Active Streaks: 3
   └ Average: 4.5 days

   📈 Activity:
   ├ Total Check-ins: 67
   ├ XP: 45 / 100
   └ Active Habits: 4

   🏆 Achievements: 5

## /profile
User sends /profile
→ Bot sends avatar image with profile text:
   👤 John — Apprentice (Level 5)

   📊 Stats:
   ├ XP: 45 / 100
   ├ Total Check-ins: 67
   ├ Active Habits: 4
   ├ Best Streak: 12 days
   ├ Streak Freezes: 2
   └ Today's Completion: 75%

   🏆 Achievements: 5

## /leaderboard
User sends /leaderboard
→ Bot shows top 10 users:
   🏆 Global Leaderboard

   🥇 Sarah — Lv.15 Warrior (450 XP)
   🥈 Mike — Lv.12 Knight (320 XP)
   🥉 John — Lv.5 Apprentice (45 XP)
   4. Alex — Lv.4 Novice (38 XP)
   ...

## /settings
User sends /settings
→ Bot shows settings menu:
   [⏰ Reminder Time] [🌙 Summary Time]
   [🌍 Timezone] [❄️ Streak Freezes: 2]

## Background Jobs (Every Minute)
1. Check morning reminders (user.reminder_time)
   → Send: "Today's quests: Morning Run, Meditation... Use /checkin!"

2. Check evening summaries (user.summary_time)
   → Send completion report with missed habits

3. Check streak risk (deadline approaching)
   → Send warning: "Your streak for Morning Run ends in 2 hours!"

## Achievement Flow
When user checks in and triggers achievement:
→ Award achievement to database
→ Add XP reward
→ Send message:
   🏆 ACHIEVEMENT UNLOCKED!

   🎖️ 7-Day Warrior
   _Maintain a 7-day streak on any habit_
   +50 XP

   _A week of fire! Your consistency is becoming dangerous._

## Level Up Flow
When user gains enough XP:
→ Update level and title
→ Update avatar stage
→ Send new avatar image:
   "🎊 LEVEL UP! You're now Level 5 — Apprentice!"
   "🎊 Your avatar has evolved!"
