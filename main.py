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
MaxieID = 1298778443
WinzuID = 1949329868

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
        bot.send_message(MaxieID, f"Пришла новая заявка! \n{message.text}")
        bot.send_message(WinzuID, f"Пришла новая заявка! \n{message.text}")
        bot.reply_to(message, "Ваша заявка на вступление принята.")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Произошла непредвиденная ошибка, попробуйте снова.")
    finally:
        forward_waiting.pop(message.from_user.id, None)


# Profile and stats commands
@bot.message_handler(commands=["createprofile"])
def create_profile(message):
    if not users.get(User.user_id == message.from_user.id):
        users.insert({
            "user_id": message.from_user.id,
            "username": f"@{message.from_user.username}",
            "role": "не задана",
            "internot": {
                "lv": 1,
                "posts": 0,
                "duel_wins": 0
            },
            "stats": {
                "HP": 0,
                "ATK": 0,
                "CRIT.DMG": 0
            }
        })
        bot.reply_to(message, "Профиль успешно создан!\n\nИспользуйте команду /rollstats чтобы сгенерировать ваши характеристики или /myprofile чтобы просмотреть его.")
    else:
        bot.reply_to(message, "У вас уже есть профиль!")

@bot.message_handler(commands=['myprofile'])
def my_profile(message):
    if not users.get(User.user_id == message.from_user.id):
        bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
        return
    user = users.get(User.user_id == message.from_user.id)
    stats = user["stats"]
    if user["stats"]["HP"] != 0:
        bot.reply_to(
            message,
            f"Игрок | {user['username']}\n\nРоль • {user['role']}\nУр. Интернота • {user["internot"]["lv"]}\n\n❤️‍🩹 Здоровье: {stats['HP']}\n🗡️ Атака: {stats['ATK']}\n💥 Крит. урон: {stats['CRIT.DMG']}%"
        )
        return
    bot.reply_to(
        message, f"Игрок | {user['username']}\n\nХарактеристики ещё не заданы. Воспользуйтесь командой /rollstats чтобы их сгенерировать."
    )

@bot.message_handler(commands=["viewid"])
def view_profile(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Эта команда доступна только администратору.")
        return
    try:
        parts = message.text.split(" ")
        username = parts[1]
        user = users.get(User.username == username)
        if not user:
            bot.reply_to(message, "Игрок не найден.")
            return
        bot.reply_to(
            message, f"ID | {user['user_id']}\nИгрок | {user['username']}."
        )
    except (IndexError, ValueError):
        bot.reply_to(message, "Пожалуйста, используйте команду в формате: /viewid @username")

@bot.message_handler(commands=['deleteprofile'])
def delete_profile(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Эта команда доступна только администратору.")
        return
    try:
        parts = message.text.split(" ")
        user_id = int(parts[1])
        if users.remove(User.user_id == user_id):
            bot.reply_to(message, f"Профиль с ID {user_id} успешно удален.")
        else:
            bot.reply_to(message, f"Профиль с ID {user_id} не найден.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Пожалуйста, введите корректный числовой ID.")


# Roll commands
@bot.message_handler(commands=['rollstats'])
def generate_stats(message):
    user = users.get(User.user_id == message.from_user.id)
    if not user:
        bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
        return

    if user["stats"]["HP"] != 0:
        bot.reply_to(message, "Вы уже сгенерировали свои характеристики!")
        return

    raw_stats = {
        "HP": [random.randint(800, 2400), random.randint(800, 2400), random.randint(800, 2400)],
        "ATK": [random.randint(120, 360), random.randint(120, 360), random.randint(120, 360)],
        "CRIT.DMG": [random.randint(135, 215), random.randint(135, 215), random.randint(135, 215)],
    }


    average_stats = {
        "❤️‍🩹 Здоровье": int(sum(raw_stats["HP"]) / len(raw_stats["HP"])),
        "🗡️ Атака": int(sum(raw_stats["ATK"]) / len(raw_stats["ATK"])),
        "💥 Крит. урон": f"{int(sum(raw_stats['CRIT.DMG']) / len(raw_stats['CRIT.DMG']))}%"
    }

    users.update({"stats": {
        "HP": int(sum(raw_stats["HP"]) / len(raw_stats["HP"])),
        "ATK": int(sum(raw_stats["ATK"]) / len(raw_stats["ATK"])),
        "CRIT.DMG": int(sum(raw_stats["CRIT.DMG"]) / len(raw_stats["CRIT.DMG"]))
        }
    }, User.user_id == message.from_user.id)

    bot.reply_to(message, "Сгенерированные характеристики:\n" + "\n".join([f"{key}: {value}" for key, value in average_stats.items()]))

@bot.message_handler(commands=['rolldice'])
def rolldice(message):
    bot.reply_to(message, "🎲 Выпавшее число: " + str(random.randint(1, 25)))

#Roleplay system
@bot.message_handler(commands=['fight'])
def fight(message):
    user = users.get(User.user_id == message.from_user.id)
    if not user:
        bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
        return

    duel = active_duels.get(message.chat.id)
    if not duel:
        bot.reply_to(message, "Извините, вы не можете бить воздух. Вызовите кого-нибудь на дуэль с помощью команды /duel @username")
        return

    # Damage formula
    damage_multiplier = random.randint(75, 95) / 100

    base_defense = random.randint(35, 60)

    check_crit = random.randint(1, 25)

    match check_crit:
        case 18 | 19 | 20 | 21 | 22:
            damage = (damage_multiplier * user["stats"]["ATK"]) * (user["stats"]["CRIT.DMG"] / 100) - base_defense
            if duel["initiator"]["ID"] == user["user_id"]:
                duel["duelist"]["HP"] -= int(damage)
            else:
                duel["initiator"]["HP"] -= int(damage)
            bot.reply_to(message, f"️️⚔️ Критический удар! Вы нанесли {int(damage)} урона противнику!")
        case 23 | 24 | 25:
            damage = (damage_multiplier * user["stats"]["ATK"]) * (user["stats"]["CRIT.DMG"] / 100) * 2 - base_defense
            if duel["initiator"]["ID"] == user["user_id"]:
                 duel["duelist"]["HP"] -= int(damage)
            else:
                 duel["initiator"]["HP"] -= int(damage)
            bot.reply_to(message, f"💥 Двойной крит! Вы нанесли {int(damage)} урона противнику!")
        case _:
            damage = (damage_multiplier * user["stats"]["ATK"]) - base_defense
            if duel["initiator"]["ID"] == user["user_id"]:
                duel["duelist"]["HP"] -= int(damage)
            else:
                duel["initiator"]["HP"] -= int(damage)
            bot.reply_to(message, f"👊 Вы нанесли {int(damage)} урона противнику!")

    if duel["initiator"]["HP"] <= 0 or duel["duelist"]["HP"] <= 0:
        winner = "initiator" if duel["duelist"]["HP"] <= 0 else "duelist"
        winner_user = users.get(User.user_id == duel[winner]["ID"])

        winner_user["internot"]["duel_wins"] += 1

        if winner_user["internot"]["duel_wins"] % 5 == 0:
            if winner_user["internot"]["lv"] == 60:
                return
            winner_user["internot"]["lv"] += 1
            bot.send_message(message.chat.id,
            f"Поздравляем! {winner_user['username']} получил повышение уровня Интернота за победы в дуэлях!",
            message_thread_id=418
        )

        users.update(
            {"internot":
                 {"duel_wins": winner_user["internot"]["duel_wins"], "lv": winner_user["internot"]["lv"], "posts": winner_user["internot"]["posts"]}
             },
            User.user_id == winner_user["user_id"]
        )

        if winner_user["internot"]["lv"] % 5 == 0:
            lv_hp_boost = random.randint(75, 125)
            lv_atk_boost = random.randint(15, 50)
            lv_crit_boost = random.randint(1, 5)

            updated_stats = {
                "HP": user["stats"]["HP"] + lv_hp_boost,
                "ATK": user["stats"]["ATK"] + lv_atk_boost,
                "CRIT.DMG": user["stats"]["CRIT.DMG"] + lv_crit_boost
            }

            users.update({"stats": updated_stats}, User.user_id == winner_user["user_id"])

        bot.send_message(message.chat.id, f"Бой окончен! 🏆 Победитель: {winner_user['username']}", message_thread_id=message.message_thread_id)
        active_duels.pop(message.chat.id, None)

@bot.message_handler(commands=['duel'])
def initiate_duel(message):
    if message.chat.id != -1003690262252 or message.message_thread_id != 135:
        bot.reply_to(message, "Дуэли можно вызывать только в Обороне шиюй.")
        return

    parts = message.text.split(" ")
    if len(parts) != 2:
        bot.reply_to(message, "Пожалуйста, используйте команду в формате: /duel @username")
        return

    initiator = users.get(User.user_id == message.from_user.id)
    duelist = users.get(User.username == parts[1])
    if not duelist or duelist["stats"]["HP"] <= 0:
        bot.reply_to(message, "Игрок не найден либо не готов к бою.")
        return
    if initiator["user_id"] == duelist["user_id"]:
        bot.reply_to(message, "Вы не можете вызвать себя на дуэль!")
        return

    active_duels[message.chat.id] = {
        "is_active": True,
        "initiator": {
            "ID": initiator["user_id"],
            "HP": initiator["stats"]["HP"]
        },
        "duelist": {
            "ID": duelist["user_id"],
            "HP": duelist["stats"]["HP"]
        }
    }

    markup = types.InlineKeyboardMarkup()
    accept_duel = types.InlineKeyboardButton("Согласиться", callback_data="duel_accepted")
    decline_duel = types.InlineKeyboardButton("Отказаться", callback_data="duel_declined")
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
        bot.send_message(
            call.message.chat.id,
            f"{duelist['role']}\n❤️‍🩹 {duelist['stats']['HP']} • 🗡️ {duelist['stats']['ATK']} • 💥 {duelist['stats']['CRIT.DMG']}%"
            f"\n\nДля начала боя используйте команду /fight\n\n"
            f"{initiator['role']}\n❤️‍🩹 {initiator['stats']['HP']} • 🗡️ {initiator['stats']['ATK']} • 💥 {initiator['stats']['CRIT.DMG']}%",
            message_thread_id = call.message.message_thread_id
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
@bot.message_handler(func=lambda message: True)
def post_counter(message):
    target_id = 2
    if message.message_thread_id == target_id:
        user = users.get(User.user_id == message.from_user.id)
        if not user:
            return

        current_lv = user["internot"]["lv"]
        if current_lv == 60:
            return

        current_posts = user["internot"]["posts"]
        new_posts = current_posts + 1

        if new_posts < 3:
            users.update({"internot": {"lv": current_lv, "posts": new_posts}}, User.user_id == user["user_id"])
            return
        new_lv = current_lv + 1
        users.update({"internot": {"lv": new_lv, "posts": 0}}, User.user_id == user["user_id"])
        bot.send_message(
            message.chat.id,
            f"Поздравляем! {user['username']} получил повышение уровня Интернота за активность в ролевом!",
            message_thread_id=418
        )

        if new_lv % 5 == 0:
            lv_hp_boost = random.randint(75, 125)
            lv_atk_boost = random.randint(15, 50)
            lv_crit_boost = random.randint(1, 5)

            updated_stats = {
                "HP": user["stats"]["HP"] + lv_hp_boost,
                "ATK": user["stats"]["ATK"] + lv_atk_boost,
                "CRIT.DMG": user["stats"]["CRIT.DMG"] + lv_crit_boost
            }

            users.update({"stats": updated_stats}, User.user_id == user["user_id"])




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
    return user_id in [MaxieID, WinzuID]


# Bot polling
bot.infinity_polling()

