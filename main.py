import random

import os
from dotenv import load_dotenv

load_dotenv()

import telebot
from telebot import types

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

import signal
import sys

from commands.profile import ProfileHandler
from systems.internot_system import InternotSystem

# Initialize database
db = TinyDB("database.json", storage=CachingMiddleware(JSONStorage))
users = db.table("users")
User = Query()

# Graceful exit
def graceful_exit(signum, frame):
    db.close()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

# Initialize bot
token = os.getenv("TOKEN")
bot = telebot.TeleBot(token=token)

#Tech waiting dict
forward_waiting = {}

# Active duels storage
active_duels = {}

# ADMIN ID'S
ADMINS_IDS = list(map(int, os.getenv("ADMINS_IDS").split(",")))

#BALANCE CONSTANTS
MAX_LV = int(os.getenv("MAX_LV"))
DUEL_WINS_PER_LV = int(os.getenv("DUEL_WINS_PER_LV"))
POSTS_PER_LV = int(os.getenv("POSTS_PER_LV"))

#TELEGRAM CONSTANTS
MAIN_GROUP_ID = int(os.getenv("MAIN_GROUP_ID"))
SHIYUI_THREAD_ID = int(os.getenv("SHIYUI_THREAD_ID"))
ROLEPLAY_THREAD_ID = int(os.getenv("ROLEPLAY_THREAD_ID"))
INTERNOT_UP_THREAD_ID = int(os.getenv("INTERNOT_UP_THREAD_ID"))

profile_handler = ProfileHandler(bot, users, User)
internot_system = InternotSystem(bot, users, User)

# Base commands
@bot.message_handler(commands=['start', "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        "Привет! Я бот помощник проекта Zone03.\nДля вступления пожалуйста напиши: /getinvite"
    )

@bot.message_handler(commands=['getinvite'])
def get_invite(message):
    forward_waiting[message.from_user.id] = True
    bot.reply_to(message, "Пожалуйста, отправьте сообщение по следующей форме:\n- Желаемая роль;\n- Насколько хорошо вы знакомы с ZZZ (0-10)?\n- Ваш возраст;\n- Ваш юз;")

@bot.message_handler(func=lambda message: forward_waiting.get(message.from_user.id, False))
def forward_message(message):
    try:
        for ID in ADMINS_IDS:
            bot.send_message(ID, f"Пришла новая заявка! \n{message.text}")
        bot.reply_to(message, "Ваша заявка на вступление принята.")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Произошла непредвиденная ошибка, попробуйте снова.")
    finally:
        forward_waiting.pop(message.from_user.id, None)

# Profile and chars commands
profile_handler.register_commands()

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

#Fight system
@bot.callback_query_handler(func=lambda call: call.data in ["player_fights", "player_runaway"])
def fight_callback_query(call):
    user = users.get(User.user_id == call.from_user.id)
    if not user:
        bot.reply_to(call.message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
        return

    duel = active_duels.get(call.message.chat.id)
    if not duel:
        bot.answer_callback_query(call.message, "Извините, вы не можете бить воздух. Вызовите кого-нибудь на дуэль с помощью команды /duel @username")
        return

    markup = types.InlineKeyboardMarkup()
    fight = types.InlineKeyboardButton("🗡️ Атаковать", callback_data="player_fights")
    runaway = types.InlineKeyboardButton("🏃‍♂️‍➡️ Сбежать", callback_data="player_runaway")
    markup.row(fight, runaway)

    if duel["turn"] != user['user_id']:
        bot.answer_callback_query(
            call.id,
            "Сейчас не ваш ход!",
        )
        return

    if duel["turn"] == duel["initiator"]["ID"]:
        duel["turn"] = duel["duelist"]["ID"]
    else:
        duel["turn"] = duel["initiator"]["ID"]

    next_turn = users.get(User.user_id == duel["turn"])

    if call.data == "player_fights":

        # Damage formula
        damage_multiplier = random.randint(65, 95) / 100

        base_defense = 45

        final_defense = (user['chars']['DEF'] + base_defense) / 1000

        damage = damage_multiplier * user["chars"]["ATK"] * (1 - final_defense)

        check_crit = random.randint(1, 25)

        match check_crit:
            case 21 | 22 | 23 | 24:
                damage *= user["chars"]["CRIT.DMG"] / 100
                if duel["initiator"]["ID"] == user["user_id"]:
                    duel["duelist"]["HP"] -= int(damage)
                else:
                    duel["initiator"]["HP"] -= int(damage)
                bot.send_message(
                    call.message.chat.id,
                    f"️️⚔️ Критический удар! Вы нанесли {int(damage)} урона противнику!\n\nХод переходит к {next_turn['username']}...",
                    reply_markup=markup,
                    message_thread_id=call.message.message_thread_id
                )
            case 25:
                damage *= user["chars"]["CRIT.DMG"] / 100 * 2
                if duel["initiator"]["ID"] == user["user_id"]:
                     duel["duelist"]["HP"] -= int(damage)
                else:
                     duel["initiator"]["HP"] -= int(damage)
                bot.send_message(
                    call.message.chat.id,
                    f"💥 Двойной крит! Вы нанесли {int(damage)} урона противнику!\n\nХод переходит к {next_turn['username']}...",
                    reply_markup=markup,
                    message_thread_id=call.message.message_thread_id
                )
            case _:
                if duel["initiator"]["ID"] == user["user_id"]:
                    duel["duelist"]["HP"] -= int(damage)
                else:
                    duel["initiator"]["HP"] -= int(damage)
                bot.send_message(
                    call.message.chat.id,
                    f"👊 Вы нанесли {int(damage)} урона противнику!\n\nХод переходит к {next_turn['username']}...",
                    reply_markup=markup,
                    message_thread_id=call.message.message_thread_id
                )

        if duel["initiator"]["HP"] <= 0 or duel["duelist"]["HP"] <= 0:
            winner = "initiator" if duel["duelist"]["HP"] <= 0 else "duelist"
            winner_user = users.get(User.user_id == duel[winner]["ID"])

            winner_user["internot"]["duel_wins"] += 1

            if winner_user["internot"]["duel_wins"] % DUEL_WINS_PER_LV == 0:
                if winner_user["internot"]["lv"] == MAX_LV:
                    return
                winner_user["internot"]["lv"] += 1
                bot.send_message(call.message.chat.id,
                f"Поздравляем! {winner_user['username']} получил повышение уровня Интернота за победы в дуэлях!",
                message_thread_id=INTERNOT_UP_THREAD_ID
            )

            users.update(
                {"internot":
                     {"duel_wins": winner_user["internot"]["duel_wins"], "lv": winner_user["internot"]["lv"], "posts": winner_user["internot"]["posts"]}
                 },
                User.user_id == winner_user["user_id"]
            )

            if winner_user["internot"]["lv"] % 5 == 0:
                lv_hp_boost = random.randint(75, 125)
                lv_defense_boost = random.randint(15, 35)
                lv_atk_boost = random.randint(15, 50)
                lv_crit_boost = random.randint(1, 5)

                updated_chars = {
                    "HP": winner_user["chars"]["HP"] + lv_hp_boost,
                    "DEF": winner_user["chars"]["DEF"] + lv_defense_boost,
                    "ATK": winner_user["chars"]["ATK"] + lv_atk_boost,
                    "CRIT.DMG": winner_user["chars"]["CRIT.DMG"] + lv_crit_boost
                }

                users.update({"chars": updated_chars}, User.user_id == winner_user["user_id"])

            bot.send_message(call.message.chat.id, f"Бой окончен! 🏆 Победитель: {winner_user['username']}", message_thread_id=call.message.message_thread_id)
    else:
        dice = random.randint(1, 18)

        if dice <= 16:
            bot.send_message(call.message.chat.id, f"{user['username']} попытался сбежать, но ничего не вышло!\n\nХод переходит к {next_turn['username']}...", message_thread_id=call.message.message_thread_id, reply_markup=markup)
            return
        bot.send_message(call.message.chat.id, f"{user['username']} сбежал с поля боя!", message_thread_id=call.message.message_thread_id)

        active_duels.pop(call.message.chat.id, None)

@bot.message_handler(commands=['duel'])
def initiate_duel(message):
    if message.chat.id != MAIN_GROUP_ID or message.message_thread_id != SHIYUI_THREAD_ID:
        bot.reply_to(message, "Дуэли можно вызывать только в Обороне шиюй.")
        return

    parts = message.text.split(" ")
    if len(parts) != 2:
        bot.reply_to(message, "Пожалуйста, используйте команду в формате: /duel @username")
        return

    initiator = users.get(User.user_id == message.from_user.id)
    duelist = users.get(User.username == parts[1])
    
    if not duelist or duelist["chars"]["HP"] <= 0:
        bot.reply_to(message, "Игрок не найден либо не готов к бою.")
        return
    
    if initiator["chars"]["HP"] <= 0:
        bot.reply_to(message, "Вы не готовы к дуэли")
        return

    if initiator["user_id"] == duelist["user_id"]:
        bot.reply_to(message, "Вы не можете вызвать себя на дуэль!")
        return

    active_duels[message.chat.id] = {
        "is_active": True,
        "turn": None,
        "initiator": {
            "ID": initiator["user_id"],
            "HP": initiator["chars"]["HP"]
        },
        "duelist": {
            "ID": duelist["user_id"],
            "HP": duelist["chars"]["HP"]
        }
    }

    markup = types.InlineKeyboardMarkup()
    accept_duel = types.InlineKeyboardButton("✅ Согласиться", callback_data="duel_accepted")
    decline_duel = types.InlineKeyboardButton("❎ Отказаться", callback_data="duel_declined")
    markup.row(accept_duel, decline_duel)

    bot.send_message(message.chat.id, f"Внимание! {initiator['username']} вызвал на бой {duelist['username']}!", reply_markup=markup, message_thread_id=message.message_thread_id)

@bot.callback_query_handler(func=lambda call: call.data in ["duel_accepted", "duel_declined"])
def duel_callback_handler(call):
    duel = active_duels.get(call.message.chat.id)
    if duel["is_active"] == False:
        bot.answer_callback_query(call.id, "Дуэль не найдена или уже началась.")
        return

    if call.from_user.id != duel["duelist"]["ID"]:
        bot.answer_callback_query(call.id, "Только вызванный игрок может принять или отклонить дуэль.")
        return

    if call.data == "duel_accepted":
        bot.answer_callback_query(call.id, "Вы согласились на дуэль!")

        active_duels.get(call.message.chat.id)["is_active"] = False

        initiator = users.get(User.user_id == duel["initiator"]["ID"])
        duelist = users.get(User.user_id == duel["duelist"]["ID"])

        markup = types.InlineKeyboardMarkup()
        fight = types.InlineKeyboardButton("🗡️ Атаковать", callback_data="player_fights")
        runaway = types.InlineKeyboardButton("🏃‍♂️‍➡️ Сбежать", callback_data="player_runaway")
        markup.row(fight, runaway)

        first_turn = random.choice([initiator, duelist])

        duel["turn"] = first_turn["user_id"]

        bot.send_message(
            call.message.chat.id,
            f"{duelist['role']}\n❤️‍🩹 {duelist['chars']['HP']} • 🗡️ {duelist['chars']['ATK']} • 💥 {duelist['chars']['CRIT.DMG']}%"
            f"\n\nПервый ход делает... { first_turn['username'] }\n\n"
            f"{initiator['role']}\n❤️‍🩹 {initiator['chars']['HP']} • 🗡️ {initiator['chars']['ATK']} • 💥 {initiator['chars']['CRIT.DMG']}%",
            message_thread_id = call.message.message_thread_id,
            reply_markup=markup
        )


    else:
        active_duels.get(call.message.chat.id)["is_active"] = False
        bot.answer_callback_query(call.id, "Вы отказались от боя.")
        bot.send_message(call.message.chat.id, "Игрок отказался от боя.", message_thread_id = call.message.message_thread_id)

@bot.message_handler(commands=['setrole'])
def set_role(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Эта команда доступна только администратору.")
        return
    try:
        parts = message.text.split(" ")
        username = parts[1]
        role = " ".join(parts[2:])
        if users.update({"role": role}, User.username == username):
            bot.reply_to(message, f"Роль игрока {username} успешно установлена на '{role}'.")
        else:
            bot.reply_to(message, f"Профиль игрока {username} не найден.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Пожалуйста, используйте команду в формате: /setrole @username роль")


#INTERNOT SYSTEM
internot_system.register_handler()

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


# Permission checker
def is_admin(user_id):
    return user_id in ADMINS_IDS


# Bot polling
bot.infinity_polling()

