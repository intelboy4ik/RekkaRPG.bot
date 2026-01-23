import random

import telebot

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage

import config
from systems.profile import ProfileSystem
from systems.internot import InternotSystem
from systems.combat import CombatSystem
from systems.amplifier import AmplifierSystem
from systems.stats import StatsSystem

from commands.base import BaseCommands

# Initialize database
db = TinyDB("database.json", storage=JSONStorage)
users = db.table("users")
engines = db.table("amplifiers")
UserQuery = Query()
EngineQuery = Query()

# Initialize bot
token = config.TOKEN
bot = telebot.TeleBot(token=token)

# Initialize classes
# Systems classes
stats_system = StatsSystem(bot, users, UserQuery)
profile_system = ProfileSystem(bot, users, UserQuery, stats_system)
internot_system = InternotSystem(bot, users, UserQuery, stats_system)
amplifier_system = AmplifierSystem(bot, engines, EngineQuery, users, UserQuery, stats_system)
fight_system = CombatSystem(bot, users, UserQuery, internot_system, stats_system)

# Commands classes
base_commands = BaseCommands(bot, users, UserQuery)

# Profile system
profile_system.register_handlers()

# Fight system
fight_system.register_handlers()

# Internot system
internot_system.register_handlers()

# Amplifier system
amplifier_system.register_handlers()

# Base commands
base_commands.register_handlers()


# Roll commands
stats_system.register_handlers()

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
    if not config.is_admin(message.from_user.id):
        bot.reply_to(message, "Эта команда доступна только администратору.")
        return
    users.truncate()
    bot.reply_to(message, "База данных очищена.")


# Bot polling
if __name__ == '__main__':
    bot.infinity_polling()
