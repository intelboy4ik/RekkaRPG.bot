import random

from telebot import types

from config import MIN_HP_PULL, MAX_HP_PULL, MIN_DEF_PULL, MAX_DEF_PULL, MIN_ATK_PULL, MAX_ATK_PULL, MIN_CRIT_DMG_PULL, \
    MAX_CRIT_DMG_PULL, BASE_ATK, BASE_DEF, BASE_HP, BASE_CRIT_DMG


class StatsSystem:
    def __init__(self, bot, players, playerquery):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery

    def register_handlers(self):
        self.bot.message_handler(commands=['rollstats'])(self.generate_stats)
        self.bot.message_handler(commands=["upgrade"])(self.upgrade_stat)
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("set_attribute_"))(
            self.set_attr_callback
        )
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("upgrade_stat_"))(
            self.upgrade_stat_callback
        )

    def generate_stats(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        if player_data["stats"]["base"]["HP"] != 0:
            self.bot.reply_to(message, "Вы уже сгенерировали свои характеристики!")
            return

        raw_stats = {
            "HP": sum(sorted([random.randint(MIN_HP_PULL, MAX_HP_PULL) for _ in range(4)])[1:]) + BASE_HP,
            "DEF": sum(sorted([random.randint(MIN_DEF_PULL, MAX_DEF_PULL) for _ in range(4)])[1:]) + BASE_DEF,
            "ATK": sum(sorted([random.randint(MIN_ATK_PULL, MAX_ATK_PULL) for _ in range(4)])[1:]) + BASE_ATK,
            "CRIT.DMG": sum(
                sorted(random.randint(MIN_CRIT_DMG_PULL, MAX_CRIT_DMG_PULL) for _ in range(4))[1:]) + BASE_CRIT_DMG,
            "PEN": 0,
            "ATTR.DMG": 0,
        }

        final_stats = {
            "❤️‍🩹 Здоровье": raw_stats["HP"],
            "🛡️ Защита": raw_stats["DEF"],
            "🗡️ Атака": raw_stats["ATK"],
            "💥 Крит. урон": f"{raw_stats['CRIT.DMG']}%",
        }

        player_data['stats']['base'] = raw_stats

        self.players.update({
            "stats": player_data["stats"]
        }, self.PlayerQuery.uid == message.from_user.id)

        physics_attr_button = types.InlineKeyboardButton(
            text="💥",
            callback_data="set_attribute_physics"
        )

        fire_attr_button = types.InlineKeyboardButton(
            text="🔥",
            callback_data="set_attribute_fire"
        )

        electricity_attr_button = types.InlineKeyboardButton(
            text="⚡️",
            callback_data="set_attribute_electricity"
        )

        ice_attr_button = types.InlineKeyboardButton(
            text="❄️",
            callback_data="set_attribute_ice"
        )

        markup = types.InlineKeyboardMarkup()
        markup.row(physics_attr_button, electricity_attr_button)
        markup.row(fire_attr_button, ice_attr_button)

        self.bot.send_dice(message.chat.id, message_thread_id=message.message_thread_id)
        self.bot.reply_to(
            message,
            "Полученные характеристики:\n" + "\n".join(
                [f"{key}: {value}" for key, value in final_stats.items()]
            )
        )
        self.bot.reply_to(
            message,
            "Выберите свой атрибут (изменить будет нельзя!)"
            "\n"
            "\n"
            "*💥 Физический* - увеличивает урон каждого удара.\n"
            "*⚡️ Электрический* - вызывает шок наносящий доп. урон.\n"
            "*🔥 Огненный* - с шансом 1/6 поджигает противника вынуждая пропустить ход.\n"
            "*❄️ Ледяной* - повышает шанс критического попадания.\n"
            ,
            parse_mode="Markdown",
            reply_markup=markup
        )

    def set_attr_callback(self, call):
        attr = call.data.split("_")[2]
        player_data = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        if not player_data:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        if player_data["attribute"]:
            self.bot.answer_callback_query(
                call.id,
                "Вы уже задали себе атрибут!",
                show_alert=True
            )
            return

        player_data["attribute"] = attr
        self.players.update({"attribute": player_data["attribute"]}, self.PlayerQuery.uid == call.from_user.id)
        self.bot.answer_callback_query(
            call.id,
            "Атрибут установлен!",
            show_alert=True
        )

    def upgrade_stat(self, message):
        markup = types.InlineKeyboardMarkup()

        hp_button = types.InlineKeyboardButton(
            text="❤️‍🩹 Здоровье",
            callback_data="upgrade_stat_HP"
        )

        def_button = types.InlineKeyboardButton(
            text="🛡️ Защита",
            callback_data="upgrade_stat_DEF"
        )

        atk_button = types.InlineKeyboardButton(
            text="⚔️ Атака",
            callback_data="upgrade_stat_ATK"
        )

        pen_button = types.InlineKeyboardButton(
            text="🗡️ Пробивание",
            callback_data="upgrade_stat_PEN"
        )

        crit_dmg_button = types.InlineKeyboardButton(
            text="💥 Крит. урон",
            callback_data="upgrade_stat_CRIT.DMG"
        )

        markup.row(hp_button, def_button)
        markup.row(pen_button, atk_button)
        markup.add(crit_dmg_button)

        self.bot.reply_to(message, "Выберите характеристику для прокачки", reply_markup=markup)

    def upgrade_stat_callback(self, call):
        stat = call.data.split("_")[2]
        player_data = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        if not player_data:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        if player_data["stats"]["points"] < 1:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно очков характеристик.",
                show_alert=True
            )
            return

        stats_upgrades = {
            "HP": random.randint(75, 135),
            "DEF": random.randint(25, 45),
            "ATK": random.randint(25, 45),
            "PEN": random.randint(1, 2),
            "CRIT.DMG": random.randint(1, 3),
        }

        upgrade_amount = stats_upgrades.get(stat, 0)
        self.calculate_stat_upgrade(player_data, stat, upgrade_amount)
        player_data["stats"]["points"] -= 1
        self.players.update({"stats": player_data["stats"]}, self.PlayerQuery.uid == player_data["uid"])

    def give_point_to_player(self, player_data, new_lv):
        if new_lv % 5 != 0:
            return

        player_data["stats"]["points"] += 1

        self.players.update({"stats": player_data["stats"]}, self.PlayerQuery.uid == player_data["uid"])

    def calculate_stat_upgrade(self, player_data, stat, amount):
        player_data["stats"]["base"][stat] += amount
        self.players.update({"stats": player_data["stats"]}, self.PlayerQuery.uid == player_data["uid"])

    @staticmethod
    def recalculate_stats(player_data):
        visible = {}
        base = player_data["stats"]["base"]
        flat = player_data["stats"]["modifiers"]["flat"]
        percent = player_data["stats"]["modifiers"]["percent"]

        for key, base_value in base.items():
            flat_bonus = flat.get(key, 0)
            percent_bonus = percent.get(key, 0)
            visible[key] = int(base_value * (1 + percent_bonus / 100) + flat_bonus)

        return visible
