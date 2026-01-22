import random

from telebot import types

from config import MAIN_GROUP_ID, SHIYUI_THREAD_ID, DUEL_WINS_PER_LV


class CombatSystem:
    def __init__(self, bot, users, userquery, internot):
        self.bot = bot
        self.users = users
        self.UserQuery = userquery
        self.active_duels = {}
        self.internot = internot

    def register_handlers(self):
        self.bot.message_handler(commands=['duel'])(self.initiate_duel)
        self.bot.callback_query_handler(func=lambda call: call.data in ["duel_accepted", "duel_declined"])(
            self.duel_callback_handler)
        self.bot.callback_query_handler(func=lambda call: call.data in ["player_fights", "player_runaway"])(
            self.combat_callback_query)

    """
    Инициация дуэли
    """

    def initiate_duel(self, message):
        if message.chat.id != MAIN_GROUP_ID or message.message_thread_id != SHIYUI_THREAD_ID:
            self.bot.reply_to(message, "Дуэли можно вызывать только в Обороне шиюй.")
            return

        parts = message.text.split(" ")
        if len(parts) != 2:
            self.bot.reply_to(message, "Пожалуйста, используйте команду в формате: /duel @username")
            return

        initiator = self.users.get(self.UserQuery.user_id == message.from_user.id)
        duelist = self.users.get(self.UserQuery.username == parts[1])

        if not duelist or duelist["chars"]["HP"] <= 0:
            self.bot.reply_to(message, "Игрок не найден либо не готов к бою.")
            return

        if initiator["chars"]["HP"] <= 0:
            self.bot.reply_to(message, "Вы не готовы к дуэли")
            return

        # if initiator["user_id"] == duelist["user_id"]:
        #     self.bot.reply_to(message, "Вы не можете вызвать себя на дуэль!")
        #     return

        self.active_duels[message.chat.id] = {
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

        self.bot.send_message(
            message.chat.id,
            f"Внимание! {initiator['username']} вызвал на бой {duelist['username']}!",
            reply_markup=markup, message_thread_id=message.message_thread_id)

    """
    Принятие/Отказ дуэли
    """

    def duel_callback_handler(self, call):
        duel = self.active_duels.get(call.message.chat.id)
        if not duel["is_active"]:
            self.bot.answer_callback_query(call.id, "Дуэль не найдена или уже началась.")
            return

        if call.from_user.id != duel["duelist"]["ID"]:
            self.bot.answer_callback_query(call.id, "Только вызванный игрок может принять или отклонить дуэль.")
            return

        if call.data == "duel_accepted":
            self.bot.answer_callback_query(call.id, "Вы согласились на дуэль!")

            self.active_duels.get(call.message.chat.id)["is_active"] = False

            initiator = self.users.get(self.UserQuery.user_id == duel["initiator"]["ID"])
            duelist = self.users.get(self.UserQuery.user_id == duel["duelist"]["ID"])

            markup = types.InlineKeyboardMarkup()
            fight = types.InlineKeyboardButton("🗡️ Атаковать", callback_data="player_fights")
            runaway = types.InlineKeyboardButton("🏃‍♂️‍➡️ Сбежать", callback_data="player_runaway")
            markup.row(fight, runaway)

            first_turn = random.choice([initiator, duelist])

            duel["turn"] = first_turn["user_id"]

            self.bot.send_message(
                call.message.chat.id,
                f"{duelist['role']}\n❤️‍🩹 {duelist['chars']['HP']} • 🗡️ {duelist['chars']['ATK']} • 💥 {duelist['chars']['CRIT.DMG']}%"
                f"\n\nПервый ход делает... {first_turn['username']}\n\n"
                f"{initiator['role']}\n❤️‍🩹 {initiator['chars']['HP']} • 🗡️ {initiator['chars']['ATK']} • 💥 {initiator['chars']['CRIT.DMG']}%",
                message_thread_id=call.message.message_thread_id,
                reply_markup=markup
            )

        else:
            self.active_duels.get(call.message.chat.id)["is_active"] = False
            self.bot.answer_callback_query(call.id, "Вы отказались от боя.")
            self.bot.send_message(call.message.chat.id, "Игрок отказался от боя.",
                                  message_thread_id=call.message.message_thread_id)

    """
    Основная боевая система, побег и бой
    """

    def combat_callback_query(self, call):
        user_data = self.users.get(self.UserQuery.user_id == call.from_user.id)
        if not user_data:
            self.bot.reply_to(call.message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        duel = self.active_duels.get(call.message.chat.id)
        if not duel:
            self.bot.answer_callback_query(
                call.message,
                "Извините, вы не можете бить воздух. Вызовите кого-нибудь на дуэль с помощью команды /duel @username"
            )
            return

        markup = types.InlineKeyboardMarkup()
        fight = types.InlineKeyboardButton("🗡️ Атаковать", callback_data="player_fights")
        runaway = types.InlineKeyboardButton("🏃‍♂️‍➡️ Сбежать", callback_data="player_runaway")
        markup.row(fight, runaway)

        if duel["turn"] != user_data['user_id']:
            self.bot.answer_callback_query(
                call.id,
                "Сейчас не ваш ход!",
            )
            return

        if duel["turn"] == duel["initiator"]["ID"]:
            duel["turn"] = duel["duelist"]["ID"]
        else:
            duel["turn"] = duel["initiator"]["ID"]

        next_turn = self.users.get(self.UserQuery.user_id == duel["turn"])

        if call.data == "player_fights":

            # Damage formula
            damage_multiplier = random.randint(65, 95) / 100

            base_defense = 45

            final_defense = (user_data['chars']['DEF'] + base_defense) / 1000

            damage = damage_multiplier * user_data["chars"]["ATK"] * (1 - final_defense)

            check_crit = random.randint(1, 25)

            match check_crit:
                case 21 | 22 | 23 | 24:
                    damage *= user_data["chars"]["CRIT.DMG"] / 100
                    self.bot.send_message(
                        call.message.chat.id,
                        f"️️⚔️ Критический удар! Вы нанесли {int(damage)} урона противнику!"
                        f"\n\n"
                        f"Ход переходит к {next_turn['username']}...",
                        reply_markup=markup,
                        message_thread_id=call.message.message_thread_id
                    )
                case 25:
                    damage *= user_data["chars"]["CRIT.DMG"] / 100 * 2
                    self.bot.send_message(
                        call.message.chat.id,
                        f"💥 Двойной крит! Вы нанесли {int(damage)} урона противнику!"
                        f"\n\n"
                        f"Ход переходит к {next_turn['username']}...",
                        reply_markup=markup,
                        message_thread_id=call.message.message_thread_id
                    )
                case _:
                    self.bot.send_message(
                        call.message.chat.id,
                        f"👊 Вы нанесли {int(damage)} урона противнику!"
                        f"\n\n"
                        f"Ход переходит к {next_turn['username']}...",
                        reply_markup=markup,
                        message_thread_id=call.message.message_thread_id
                    )

            if duel["initiator"]["ID"] == user_data["user_id"]:
                duel["duelist"]["HP"] -= int(damage)
            else:
                duel["initiator"]["HP"] -= int(damage)

            if duel["initiator"]["HP"] <= 0 or duel["duelist"]["HP"] <= 0:
                winner = "initiator" if duel["duelist"]["HP"] <= 0 else "duelist"
                winner_user_data = self.users.get(self.UserQuery.user_id == duel[winner]["ID"])

                winner_user_data["internot"]["duel_wins"] += 1

                self.users.update({
                    "internot":
                        {
                            "duel_wins": winner_user_data["internot"]["duel_wins"],
                            "lv": winner_user_data["internot"]["lv"],
                            "posts": winner_user_data["internot"]["posts"]
                        }
                },
                    self.UserQuery.user_id == winner_user_data["user_id"]
                )

                if winner_user_data["internot"]["duel_wins"] % DUEL_WINS_PER_LV == 0:
                    self.internot.up_internot_lv(
                        winner_user_data
                    )
                    self.internot.send_congrats_message(
                        winner_user_data,
                        "за победы в дуэлях"
                    )

                self.bot.send_message(
                    call.message.chat.id, f"Бой окончен! 🏆 Победитель: {winner_user_data['username']}",
                    message_thread_id=call.message.message_thread_id
                )
                self.active_duels.pop(call.message.chat.id, None)
        else:
            dice = random.randint(1, 18)

            if dice <= 16:
                self.bot.send_message(
                    call.message.chat.id,
                    f"{user_data['username']} попытался сбежать, но ничего не вышло!"
                    f"\n\n"
                    f"Ход переходит к {next_turn['username']}...",
                    message_thread_id=call.message.message_thread_id, reply_markup=markup
                )
                return
            self.bot.send_message(
                call.message.chat.id, f"{user_data['username']} сбежал с поля боя!",
                message_thread_id=call.message.message_thread_id
            )

            self.active_duels.pop(call.message.chat.id, None)
