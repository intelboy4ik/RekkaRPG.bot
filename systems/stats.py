import random


class StatsSystem:
    def __init__(self, bot, users, userquery):
        self.bot = bot
        self.users = users
        self.UserQuery = userquery

    def register_handlers(self):
        self.bot.message_handler(commands=['rollstats'])(self.generate_stats)

    def generate_stats(self, message):
        user_data = self.users.get(self.UserQuery.user_id == message.from_user.id)
        if not user_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        if user_data["stats"]["base"]["HP"] != 0:
            self.bot.reply_to(message, "Вы уже сгенерировали свои характеристики!")
            return

        raw_stats = {
            "HP": sum(sorted([random.randint(600, 2400) for _ in range(4)])[1:]) + 800,
            "DEF": sum(sorted([random.randint(15, 35) for _ in range(4)])[1:]) + 30,
            "ATK": sum(sorted([random.randint(85, 185) for _ in range(4)])[1:]) + 200,
            "CRIT.DMG": sum(sorted(random.randint(15, 60) for _ in range(4))[1:]) + 110,
            "PEN": 0,
        }

        final_stats = {
            "❤️‍🩹 Здоровье": raw_stats["HP"],
            "🛡️ Защита": raw_stats["DEF"],
            "🗡️ Атака": raw_stats["ATK"],
            "💥 Крит. урон": f"{raw_stats['CRIT.DMG']}%",
        }

        user_data['stats']['base'] = raw_stats

        self.users.update({
            "stats": user_data["stats"]
        }, self.UserQuery.user_id == message.from_user.id)

        self.recalc_stats(user_data)

        self.bot.send_dice(message.chat.id, message_thread_id=message.message_thread_id)
        self.bot.reply_to(
            message,
            "Полученные характеристики:\n" + "\n".join(
                [f"{key}: {value}" for key, value in final_stats.items()]
            )
        )

    def recalc_stats(self, user_data):
        visible = {}
        base = user_data["stats"]["base"]
        flat = user_data["stats"]["modifiers"]["flat"]
        percent = user_data["stats"]["modifiers"]["percent"]

        for key, base_value in base.items():
            flat_bonus = flat.get(key, 0)
            percent_bonus = percent.get(key, 0)
            visible[key] = int(base_value * (1 + percent_bonus / 100)) + flat_bonus

        return visible
