from config import is_admin


class ProfileSystem:
    def __init__(self, bot, users, userquery, stats_system=None):
        self.bot = bot
        self.users = users
        self.UserQuery = userquery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(commands=["createprofile"])(self.create_profile_command)
        self.bot.message_handler(commands=['myprofile'])(self.my_profile_command)
        self.bot.message_handler(commands=['deleteprofile'])(self.delete_profile_command)
        self.bot.message_handler(commands=["viewprofileid"])(self.view_profile_id)

    def create_profile_command(self, message):
        if not self.users.get(self.UserQuery.user_id == message.from_user.id):
            self.users.insert({
                "user_id": message.from_user.id,
                "username": f"@{message.from_user.username}",
                "role": "не задана",
                "internot": {
                    "lv": 1,
                    "coins": 0,
                    "posts": 0,
                    "duel_wins": 0,
                },
                "stats": {
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
        if not self.users.get(self.UserQuery.user_id == message.from_user.id):
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return
        user_data = self.users.get(self.UserQuery.user_id == message.from_user.id)
        stats = self.stats_system.recalc_stats(user_data)
        if stats["HP"] != 0:
            self.bot.reply_to(
                message,
                f"Игрок | {user_data['username']}"
                f"\n\n"
                f"Роль • {user_data['role']}\n"
                f"Ур. Интернота • {user_data['internot']['lv']}\n"
                f"Амплификатор • {user_data['amplifiers']['equipped'] if user_data['amplifiers']['equipped'] else 'пусто'}\n"
                f"Баланс • {user_data['internot']['coins']} монеток"
                f"\n\n"
                f"❤️‍🩹 Здоровье: {stats['HP']}\n"
                f"🛡️ Защита: {stats['DEF']}\n"
                f"⚔️ Атака: {stats['ATK']}\n"
                f"💥 Крит. урон: {stats['CRIT.DMG']}%"
            )
            return
        self.bot.reply_to(
            message,
            f"Игрок | {user_data['username']}"
            f"\n\n"
            f"Характеристики ещё не заданы. Воспользуйтесь командой /rollstats чтобы их сгенерировать."
        )

    def delete_profile_command(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        try:
            parts = message.text.split(" ")
            user_id = int(parts[1])
            if self.users.remove(self.UserQuery.user_id == user_id):
                self.bot.reply_to(message, f"Профиль с ID {user_id} успешно удален.")
            else:
                self.bot.reply_to(message, f"Профиль с ID {user_id} не найден.")
        except (IndexError, ValueError):
            self.bot.reply_to(message, "Пожалуйста, введите корректный числовой ID.")

    def view_profile_id(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        try:
            parts = message.text.split(" ")
            username = parts[1]
            user = self.users.get(self.UserQuery.username == username)
            if not user:
                self.bot.reply_to(message, "Игрок не найден.")
                return
            self.bot.reply_to(
                message, f"ID | {user['user_id']}\nИгрок | {user['username']}"
            )
        except (IndexError, ValueError):
            self.bot.reply_to(message, "Пожалуйста, используйте команду в формате: /viewid @username")

