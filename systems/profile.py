from config import is_admin


class ProfileSystem:
    def __init__(self, bot, players, playerquery, stats_system=None):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(commands=["createprofile"])(self.create_profile_command)
        self.bot.message_handler(commands=['myprofile'])(self.my_profile_command)
        self.bot.message_handler(commands=['deleteprofile'])(self.delete_profile_command)
        self.bot.message_handler(commands=["viewprofileid"])(self.view_profile_id)

    def create_profile_command(self, message):
        if not self.players.get(self.PlayerQuery.uid == message.from_user.id):
            self.players.insert({
                "uid": message.from_user.id,
                "username": f"@{message.from_user.username}",
                "role": "не задана",
                "internot": {
                    "lv": 1,
                    "coins": 0,
                    "posts": 0,
                    "duel_wins": 0,
                    "last_daily": None
                },
                "stats": {
                    "points": 0,
                    "base":
                        {
                            "HP": 0,
                            "DEF": 0,
                            "ATK": 0,
                            "PEN": 0,
                            "CRIT.DMG": 0,
                        },
                    "modifiers":
                        {
                            "flat": {},
                            "percent": {}
                        }
                },
                "amplifiers": {
                    "owned": [],
                    "equipped": None
                },
                "decoder": {
                    "videotapes": 45,
                    "searched": 0,
                    "guarantee": {
                        "a-tier": 10,
                        "s-tier": 90
                    },
                }
            })
            self.bot.reply_to(
                message,
                "Профиль успешно создан!"
                "\n\n"
                "Используйте команду /rollstats чтобы сгенерировать ваши характеристики или /myprofile чтобы просмотреть его.")
        else:
            self.bot.reply_to(message, "У вас уже есть профиль!")

    def my_profile_command(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return
        stats = self.stats_system.recalc_stats(player_data)
        if stats["HP"] != 0:
            self.bot.reply_to(
                message,
                f"Игрок | {player_data['username']}"
                f"\n\n"
                f"Роль • {player_data['role']}\n"
                f"Ур. Интернота • {player_data['internot']['lv']}\n"
                f"Амплификатор • {player_data['amplifiers']['equipped'] if player_data['amplifiers']['equipped'] else 'пусто'}\n"
                f"Баланс • {player_data['internot']['coins']} монеток"
                f"\n\n"
                f"❤️‍🩹 Здоровье: {stats['HP']}\n"
                f"🛡️ Защита: {stats['DEF']}\n"
                f"⚔️ Атака: {stats['ATK']}\n"
                f"💥 Крит. урон: {stats['CRIT.DMG']}%\n"
                f"🗡️ Пробивание: {stats['PEN']}"
                "f\n\n"
                f"🧩 Очки характеристик: {player_data['stats']['points']}"
            )
            return
        self.bot.reply_to(
            message,
            f"Игрок | {player_data['username']}"
            f"\n\n"
            f"Характеристики ещё не заданы. Воспользуйтесь командой /rollstats чтобы их сгенерировать."
        )

    def delete_profile_command(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        try:
            parts = message.text.split(" ")
            uid = int(parts[1])
            if self.players.remove(self.PlayerQuery.uid == uid):
                self.bot.reply_to(message, f"Профиль с ID {uid} успешно удален.")
            else:
                self.bot.reply_to(message, f"Профиль с ID {uid} не найден.")
        except (IndexError, ValueError):
            self.bot.reply_to(message, "Пожалуйста, введите корректный числовой ID.")

    def view_profile_id(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        try:
            parts = message.text.split(" ")
            username = parts[1]
            player = self.players.get(self.PlayerQuery.username == username)
            if not player:
                self.bot.reply_to(message, "Игрок не найден.")
                return
            self.bot.reply_to(
                message, f"ID | {player['uid']}\nИгрок | {player['username']}"
            )
        except (IndexError, ValueError):
            self.bot.reply_to(message, "Пожалуйста, используйте команду в формате: /viewid @username")

