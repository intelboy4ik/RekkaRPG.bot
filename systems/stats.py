import random

from config import MIN_HP_PULL, MAX_HP_PULL, MIN_DEF_PULL, MAX_DEF_PULL, MIN_ATK_PULL, MAX_ATK_PULL, MIN_CRIT_DMG_PULL, \
    MAX_CRIT_DMG_PULL, BASE_ATK, BASE_DEF, BASE_HP, BASE_CRIT_DMG


class StatsSystem:
    def __init__(self, bot, players, playerquery):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery

    def register_handlers(self):
        self.bot.message_handler(commands=['rollstats'])(self.generate_stats)

    def generate_stats(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        if player_data["stats"]["base"]["HP"] != 0:
            self.bot.reply_to(message, "Вы уже сгенерировали свои характеристики!")
            return

        raw_stats = {
            "HP": sum(sorted([random.randint(MIN_HP_PULL, MAX_HP_PULL) for _ in range(4)])[1:]) + BASE_HP,
            "DEF": sum(sorted([random.randint(MIN_DEF_PULL, MAX_DEF_PULL) for _ in range(4)])[1:]) + BASE_DEF,
            "ATK": sum(sorted([random.randint(MIN_ATK_PULL, MAX_ATK_PULL) for _ in range(4)])[1:]) + BASE_ATK,
            "CRIT.DMG": sum(sorted(random.randint(MIN_CRIT_DMG_PULL, MAX_CRIT_DMG_PULL) for _ in range(4))[1:]) + BASE_CRIT_DMG,
            "PEN": 0,
        }

        final_stats = {
            "❤️‍🩹 Здоровье": raw_stats["HP"],
            "🛡️ Защита": raw_stats["DEF"],
            "🗡️ Атака": raw_stats["ATK"],
            "💥 Крит. урон": f"{raw_stats['CRIT.DMG']}%",
        }

        player_data['stats']['base'] = raw_stats

        self.players.update({
            "stats": player_data["stats"]
        }, self.PlayerQuery.uid == message.from_user.id)

        self.recalc_stats(player_data)

        self.bot.send_dice(message.chat.id, message_thread_id=message.message_thread_id)
        self.bot.reply_to(
            message,
            "Полученные характеристики:\n" + "\n".join(
                [f"{key}: {value}" for key, value in final_stats.items()]
            )
        )

    @staticmethod
    def recalc_stats(player_data):
        visible = {}
        base = player_data["stats"]["base"]
        flat = player_data["stats"]["modifiers"]["flat"]
        percent = player_data["stats"]["modifiers"]["percent"]

        for key, base_value in base.items():
            flat_bonus = flat.get(key, 0)
            percent_bonus = percent.get(key, 0)
            visible[key] = int(base_value * (1 + percent_bonus / 100)) + flat_bonus

        return visible
