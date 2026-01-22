import random

import os
from dotenv import load_dotenv

load_dotenv()

import telebot

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage

import signal
import sys

from systems.profile import ProfileSystem
from systems.internot import InternotSystem
from systems.combat import CombatSystem

from commands.base import BaseCommands

# Initialize database
db = TinyDB("database.json", storage=JSONStorage)
users = db.table("users")
User = Query()

# Initialize bot
token = os.getenv("TOKEN")
bot = telebot.TeleBot(token=token)


# Initialize classes
profile_system = ProfileSystem(bot, users, User)
internot_system = InternotSystem(bot, users, User)
fight_system = CombatSystem(bot, users, User, internot_system)
base_commands = BaseCommands(bot, users, User)

# Profile system
profile_system.register_handlers()

#Fight system
fight_system.register_handlers()

#Internot system
internot_system.register_handlers()

# Base commands
base_commands.register_handlers()

# Roll commands
@bot.message_handler(commands=['rollchars'])
def generate_chars(message):
    user = users.get(User.user_id == message.from_user.id)
    if not user:
        bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
        return

    if user["chars"]["HP"] != 0:
        bot.reply_to(message, "Вы уже сгенерировали свои характеристики!")
        return

    raw_chars = {
        "HP": sum(sorted([random.randint(300, 1500) for _ in range(4)])[1:])+800,
        "DEF": sum(sorted([random.randint(10, 15) for _ in range(4)])[1:])+30,
        "ATK": sum(sorted([random.randint(75, 175) for _ in range(4)])[1:])+200,
        "CRIT.DMG": sum(sorted(random.randint(15, 60) for _ in range(4))[1:])+110,
    }

    final_chars = {
        "❤️‍🩹 Здоровье": raw_chars["HP"],
        "🛡️ Защита": raw_chars["DEF"],
        "🗡️ Атака": raw_chars["ATK"],
        "💥 Крит. урон": f"{raw_chars['CRIT.DMG']}%",
    }

    users.update({"chars": {
        "HP": raw_chars["HP"],
        "DEF": raw_chars["DEF"],
        "ATK": raw_chars["ATK"],
        "CRIT.DMG": raw_chars['CRIT.DMG']
        }
    }, User.user_id == message.from_user.id)

    bot.send_dice(message.chat.id, message_thread_id=message.message_thread_id)
    bot.reply_to(message, "Полученные характеристики:\n" + "\n".join([f"{key}: {value}" for key, value in final_chars.items()]))

@bot.message_handler(commands=['rolldice'])
def rolldice(message):
    bot.reply_to(message, "🎲 Выпавшее число: " + str(random.randint(1, 25)))

# DEBUG COMMANDS
@bot.message_handler(commands=['debuggetid'])
def debug_get_id(message):
    print(bot.get_chat(message.chat.id))
    print(bot.get_chat(message.chat.id).type)
    print(message.message_thread_id)

@bot.message_handler(commands=['debugcleardb'])
def debug_clear_db(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Эта команда доступна только администратору.")
        return
    users.truncate()
    bot.reply_to(message, "База данных очищена.")


# Bot polling
if __name__ == '__main__':
    bot.infinity_polling()

