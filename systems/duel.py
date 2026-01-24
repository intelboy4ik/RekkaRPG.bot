import random

from telebot import types

from config import MAIN_GROUP_ID, SHIYUI_THREAD_ID, DUEL_WINS_PER_LV, MIN_DMG_MULTIPLIER, MAX_DMG_MULTIPLIER, \
    BASE_DUEL_DEFENSE


class DuelSystem:
    def __init__(self, bot, players, playerquery, internot, stats_system=None):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.active_duels = {}
        self.internot = internot
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(commands=['duel'])(self.initiate_duel)
        self.bot.callback_query_handler(func=lambda call: call.data in ["duel_accepted", "duel_declined"])(
            self.duel_callback_handler)
        self.bot.callback_query_handler(func=lambda call: call.data in ["player_attacks", "player_runaway"])(
            self.duel_callback_query)

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

        initiator = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        duelist = self.players.get(self.PlayerQuery.username == parts[1])

        duelist_stats = None
        initiator_stats = None

        if initiator and duelist:
            duelist_stats = self.stats_system.recalc_stats(duelist)
            initiator_stats = self.stats_system.recalc_stats(initiator)

        if not duelist_stats or duelist_stats["HP"] <= 0:
            self.bot.reply_to(message, "Игрок не найден либо не готов к бою.")
            return

        if not initiator_stats or initiator_stats["HP"] <= 0:
            self.bot.reply_to(message, "Вы не готовы к дуэли")
            return

        if initiator["uid"] == duelist["uid"]:
            self.bot.reply_to(message, "Вы не можете вызвать себя на дуэль!")
            return

        self.active_duels[message.chat.id] = {
            "is_active": True,
            "turn": None,
            "initiator": {
                "ID": initiator["uid"],
                "HP": initiator_stats["HP"],
                "DEF": initiator_stats["DEF"],
            },
            "duelist": {
                "ID": duelist["uid"],
                "HP": duelist_stats["HP"],
                "DEF": duelist_stats["DEF"],
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

            initiator = self.players.get(self.PlayerQuery.uid == duel["initiator"]["ID"])
            duelist = self.players.get(self.PlayerQuery.uid == duel["duelist"]["ID"])

            # Stats
            duelist_stats = self.stats_system.recalc_stats(duelist)
            initiator_stats = self.stats_system.recalc_stats(initiator)

            markup = types.InlineKeyboardMarkup()
            attack = types.InlineKeyboardButton("🗡️ Атаковать", callback_data="player_attacks")
            runaway = types.InlineKeyboardButton("🏃‍♂️‍➡️ Сбежать", callback_data="player_runaway")
            markup.row(attack, runaway)

            first_turn = random.choice([initiator, duelist])

            duel["turn"] = first_turn["uid"]

            self.bot.send_message(
                call.message.chat.id,
                f"{duelist['role']}\n❤️‍🩹 {duelist_stats['HP']} • ⚔️ {duelist_stats['ATK']} • 💥 {duelist_stats['CRIT.DMG']}%"
                f"\n\nПервый ход делает... {first_turn['username']}\n\n"
                f"{initiator['role']}\n❤️‍🩹 {initiator_stats['HP']} • ️⚔️ {initiator_stats['ATK']} • 💥 {initiator_stats['CRIT.DMG']}%",
                message_thread_id=call.message.message_thread_id,
                reply_markup=markup
            )

        else:
            self.active_duels.get(call.message.chat.id)["is_active"] = False
            self.bot.answer_callback_query(call.id, "Вы отказались от боя.")
            self.bot.send_message(
                call.message.chat.id,
                "Игрок отказался от боя.",
                message_thread_id=call.message.message_thread_id
            )

    """
    Основная боевая система, побег и бой
    """

    def duel_callback_query(self, call):
        player_data = self.players.get(self.PlayerQuery.uid == call.from_user.id)
        if not player_data:
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
        attack = types.InlineKeyboardButton("🗡️ Атаковать", callback_data="player_attacks")
        runaway = types.InlineKeyboardButton("🏃‍♂️‍➡️ Сбежать", callback_data="player_runaway")
        markup.row(attack, runaway)

        if duel["turn"] != player_data['uid']:
            self.bot.answer_callback_query(
                call.id,
                "Сейчас не ваш ход!",
            )
            return

        if duel["turn"] == duel["initiator"]["ID"]:
            duel["turn"] = duel["duelist"]["ID"]
        else:
            duel["turn"] = duel["initiator"]["ID"]

        next_turn = self.players.get(self.PlayerQuery.uid == duel["turn"])

        if call.data == "player_attacks":
            player_stats = self.stats_system.recalc_stats(player_data)
            enemy = duel["initiator"] if duel["duelist"]["ID"] == player_data["uid"] else duel["duelist"]

            damage, is_crit, is_double_crit, is_miss = self.calculate_damage(player_stats, enemy["DEF"])

            if duel["initiator"]["ID"] == player_data["uid"]:
                duel["duelist"]["HP"] -= int(damage)
            else:
                duel["initiator"]["HP"] -= int(damage)

            if is_miss:
                self.bot.send_message(
                    call.message.chat.id,
                    f"💨 Промах! Вы не нанесли урона противнику!"
                    f"\n\n"
                    f"Ход переходит к {next_turn['username']}",
                    reply_markup=markup,
                    message_thread_id=call.message.message_thread_id
                )
                return

            if is_crit:
                self.bot.send_message(
                    call.message.chat.id,
                    f"️️⚔️ Критический удар! Вы нанесли {int(damage)} урона противнику!"
                    f"\n\n"
                    f"Ход переходит к {next_turn['username']}",
                    reply_markup=markup,
                    message_thread_id=call.message.message_thread_id
                )
                return

            if is_double_crit:
                self.bot.send_message(
                    call.message.chat.id,
                    f"💥 Двойной крит! Вы нанесли {int(damage)} урона противнику!"
                    f"\n\n"
                    f"Ход переходит к {next_turn['username']}",
                    reply_markup=markup,
                    message_thread_id=call.message.message_thread_id
                )
                return

            self.bot.send_message(
                call.message.chat.id,
                f"👊 Вы нанесли {int(damage)} урона противнику!"
                f"\n\n"
                f"Ход переходит к {next_turn['username']}",
                reply_markup=markup,
                message_thread_id=call.message.message_thread_id
            )

            if duel["initiator"]["HP"] <= 0 or duel["duelist"]["HP"] <= 0:
                winner = "initiator" if duel["duelist"]["HP"] <= 0 else "duelist"
                winner_user_data = self.players.get(self.PlayerQuery.uid == duel[winner]["ID"])

                winner_user_data["internot"]["duel_wins"] += 1

                coins_wins = random.randint(125, 300)
                winner_user_data["internot"]["coins"] += coins_wins

                self.players.update({
                    "internot": winner_user_data["internot"]
                },
                    self.PlayerQuery.uid == winner_user_data["uid"]
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
                    call.message.chat.id,
                    f"Бой окончен!\n"
                    f"🏆 Победитель: {winner_user_data['username']}\n\nНачисляем {coins_wins} монеток...",
                    message_thread_id=call.message.message_thread_id
                )
                self.active_duels.pop(call.message.chat.id, None)
        else:
            dice = random.randint(1, 18)
            if dice <= 16:
                self.bot.send_message(
                    call.message.chat.id,
                    f"{player_data['username']} попытался сбежать, но ничего не вышло!"
                    f"\n\n"
                    f"Ход переходит к {next_turn['username']}...",
                    message_thread_id=call.message.message_thread_id, reply_markup=markup
                )
                return
            self.bot.send_message(
                call.message.chat.id, f"{player_data['username']} сбежал с поля боя!",
                message_thread_id=call.message.message_thread_id
            )

            self.active_duels.pop(call.message.chat.id, None)

    @staticmethod
    def calculate_damage(player_stats, enemy_def):
        damage_multiplier = random.randint(MIN_DMG_MULTIPLIER, MAX_DMG_MULTIPLIER) / 100

        base_defense = BASE_DUEL_DEFENSE

        final_defense = (enemy_def + base_defense - player_stats["PEN"]) / 1000

        damage = damage_multiplier * player_stats["ATK"] * (1 - final_defense)

        dice = random.randint(1, 25)
        is_crit = False
        is_double_crit = False
        is_miss = False

        match dice:
            case 1 | 2 | 3:
                damage = 0
                is_miss = True
            case 21 | 22 | 23 | 24:
                damage *= player_stats["CRIT.DMG"] / 100
                is_crit = True
            case 25:
                damage *= player_stats["CRIT.DMG"] / 100 * 2
                is_double_crit = True

        return damage, is_crit, is_double_crit, is_miss
