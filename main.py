import random

import telebot

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage

import config
from systems.profile import ProfileSystem
from systems.progression import ProgressionSystem
from systems.duel import DuelSystem
from systems.amplifier import AmplifierSystem
from systems.stats import StatsSystem
from systems.store import StoreSystem
from systems.decoder import DecoderSystem
from systems.redeem import RedeemSystem

from commands.base import BaseCommands

# Initialize database
db = TinyDB("database.json", storage=JSONStorage)

# Tables
players = db.table("players")
amplifiers = db.table("amplifiers")
codes = db.table("codes")

# Queries
PlayerQuery = Query()
AmplifierQuery = Query()
CodeQuery = Query()

# Initialize bot
token = config.TOKEN
bot = telebot.TeleBot(token=token)

# Initialize classes
# Systems classes
stats_system = StatsSystem(bot, players, PlayerQuery)
profile_system = ProfileSystem(bot, players, PlayerQuery, stats_system)
progression_system = ProgressionSystem(bot, players, PlayerQuery, stats_system)
amplifier_system = AmplifierSystem(bot, amplifiers, AmplifierQuery, players, PlayerQuery, stats_system)
duel_system = DuelSystem(bot, players, PlayerQuery, progression_system, stats_system)
store_system = StoreSystem(bot, players, PlayerQuery, amplifiers, AmplifierQuery, amplifier_system)
decoder_system = DecoderSystem(bot, players, PlayerQuery, amplifiers, AmplifierQuery)
redeem_system = RedeemSystem(bot, players, PlayerQuery, amplifiers, AmplifierQuery, codes, CodeQuery)

# Commands classes
base_commands = BaseCommands(bot, players, PlayerQuery)

# Profile system
profile_system.register_handlers()

# Fight system
duel_system.register_handlers()

# Internot system
progression_system.register_handlers()

# Amplifier system
amplifier_system.register_handlers()

# Store system
store_system.register_handlers()

# Decoder system
decoder_system.register_handlers()

# Redeem system
redeem_system.register_handlers()

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
    players.truncate()
    bot.reply_to(message, "База данных очищена.")


# Bot polling
if __name__ == '__main__':
    bot.infinity_polling()
