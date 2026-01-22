import os
from dotenv import load_dotenv

load_dotenv()

# ADMINS IDS
ADMINS_IDS = list(map(int, os.getenv("ADMINS_IDS").split(",")))


def is_admin(user_id):
    return user_id in ADMINS_IDS


class BaseCommands:
    def __init__(self, bot, users, user):
        self.bot = bot
        self.users = users
        self.user = user
        self.forward_waiting = {}

    def register_handlers(self):
        self.bot.message_handler(commands=['start', "help"])(self.send_welcome)
        self.bot.message_handler(commands=['getinvite'])(self.get_invite)
        self.bot.message_handler(func=lambda message: self.forward_waiting.get(message.from_user.id, False))(self.forward_message)
        self.bot.message_handler(commands=['setrole'])(self.set_role)

    def send_welcome(self, message):
        self.bot.reply_to(
            message,
            "Привет! Я бот помощник проекта Zone03.\nДля вступления пожалуйста напиши: /getinvite"
        )

    def get_invite(self, message):
        self.forward_waiting[message.from_user.id] = True
        self.bot.reply_to(
            message,
            "Пожалуйста, отправьте сообщение по следующей форме:"
            "\n- Желаемая роль;"
            "\n- Насколько хорошо вы знакомы с ZZZ (0-10)?"
            "\n- Ваш возраст;"
            "\n- Ваш юз;"
        )

    def forward_message(self, message):
        try:
            for ID in ADMINS_IDS:
                self.bot.send_message(ID, f"Пришла новая заявка! \n{message.text}")
            self.bot.reply_to(message, "Ваша заявка на вступление принята.")
        except Exception as e:
            print(e)
            self.bot.reply_to(message, "Произошла непредвиденная ошибка, попробуйте снова.")
        finally:
            self.forward_waiting.pop(message.from_user.id, None)

    def set_role(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        try:
            parts = message.text.split(" ")
            username = parts[1]
            role = " ".join(parts[2:])
            if self.users.update({"role": role}, self.user.username == username):
                self.bot.reply_to(message, f"Роль игрока {username} успешно установлена на '{role}'.")
            else:
                self.bot.reply_to(message, f"Профиль игрока {username} не найден.")
        except (IndexError, ValueError):
            self.bot.reply_to(message, "Пожалуйста, используйте команду в формате: /setrole @username роль")

