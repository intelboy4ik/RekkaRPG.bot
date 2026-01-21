import main

class ProfileHandler:
    def __init__(self, bot, users, user):
        self.bot = bot
        self.users = users
        self.User = user

    def register_commands(self):
        self.bot.message_handler(commands=["createprofile"])(self.create_profile_command)
        self.bot.message_handler(commands=['myprofile'])(self.my_profile_command)
        self.bot.message_handler(commands=['deleteprofile'])(self.delete_profile_command)
        self.bot.message_handler(commands=["viewprofileid"])(self.view_profile_id)

    def create_profile_command(self, message):
        if not self.users.get(self.User.user_id == message.from_user.id):
            self.users.insert({
                "user_id": message.from_user.id,
                "username": f"@{message.from_user.username}",
                "role": "не задана",
                "internot_lv": 1,
                "stats": {
                    "HP": 0,
                    "ATK": 0,
                    "CRIT.DMG": 0
                }
            })
            self.bot.reply_to(message, "Профиль успешно создан!\n\nИспользуйте команду /rollstats чтобы сгенерировать ваши характеристики или /myprofile чтобы просмотреть его.")
        else:
            self.bot.reply_to(message, "У вас уже есть профиль!")

    def my_profile_command(self, message):
        if not self.users.get(self.User.user_id == message.from_user.id):
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return
        user = self.users.get(self.User.user_id == message.from_user.id)
        chars = user["chars"]
        if user["chars"]["HP"] != 0:
            self.bot.reply_to(
                message,
                f"Игрок | {user['username']}\n\nРоль • {user['role']}\nУр. Интернота • {user['internot']['lv']}\n\n❤️‍🩹 Здоровье: {chars['HP']}\n🛡️ Защита: {chars["DEF"]}\n🗡️ Атака: {chars['ATK']}\n💥 Крит. урон: {chars['CRIT.DMG']}%"
            )
            return
        self.bot.reply_to(
            message, f"Игрок | {user['username']}\n\nХарактеристики ещё не заданы. Воспользуйтесь командой /rollchars чтобы их сгенерировать."
        )

    def delete_profile_command(self, message):
        if not main.is_admin(message.from_user.id):
            self.bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        try:
            parts = message.text.split(" ")
            user_id = int(parts[1])
            if self.users.remove(self.User.user_id == user_id):
                self.bot.reply_to(message, f"Профиль с ID {user_id} успешно удален.")
            else:
                self.bot.reply_to(message, f"Профиль с ID {user_id} не найден.")
        except (IndexError, ValueError):
            self.bot.reply_to(message, "Пожалуйста, введите корректный числовой ID.")

    def view_profile_id(self, message):
        if not main.is_admin(message.from_user.id):
            self.bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        try:
            parts = message.text.split(" ")
            username = parts[1]
            user = self.users.get(self.User.username == username)
            if not user:
                self.bot.reply_to(message, "Игрок не найден.")
                return
            self.bot.reply_to(
                message, f"ID | {user['user_id']}\nИгрок | {user['username']}."
            )
        except (IndexError, ValueError):
            self.bot.reply_to(message, "Пожалуйста, используйте команду в формате: /viewid @username")