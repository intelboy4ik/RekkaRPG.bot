from telebot import types

from config import is_admin, AMPLIFIER_POSSIBLE_STATS


class AmplifierSystem:
    def __init__(self, bot, amplifiers, amplifierquery, players, playerquery, stats_system=None):
        self.bot = bot
        self.amplifiers = amplifiers
        self.AmplifierQuery = amplifierquery
        self.players = players
        self.PlayerQuery = playerquery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(commands=["addamplifier"])(self.add_amplifier)
        self.bot.message_handler(commands=["removeamplifier"])(self.remove_amplifier)
        self.bot.message_handler(commands=["equip"])(self.equip_amplifier)
        self.bot.message_handler(commands=["unequip"])(self.unequip_amplifier)
        self.bot.message_handler(commands=["inventory"])(self.open_inventory)
        self.bot.message_handler(commands=["store"])(self.open_amplifier_store)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("buy_amplifier_"))(
            self.buy_amplifier_callback)

    def add_amplifier(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return

        parts = message.text.split(" ")
        if len(parts) != 6:
            self.bot.reply_to(
                message,
                "Неверный формат команды! Используйте: /addamplifier <название> <атака> <характеристика> <значение> <цена>"
            )
            return

        name = parts[1].replace("_", " ")
        attack = int(parts[2])

        stat = parts[3].upper()
        if stat not in ENGINES_POSSIBLE_STATS:
            self.bot.reply_to(
                message,
                f"Неверная характеристика! Допустимые характеристики: {', '.join(ENGINES_POSSIBLE_STATS)}"
            )
            return
        stat_value = int(parts[4])

        cost = int(parts[5])

        if self.amplifiers.get(self.AmplifierQuery.name == name):
            self.bot.reply_to(message, "Амплификатор с таким именем уже существует!")
            return

        if len(self.amplifiers) >= 12:
            self.bot.reply_to(message, "Достигнуто максимальное количество амплификаторов!")
            return

        amplifier_stats = {
            "ATK": attack,
            stat: stat_value,
        }
        self.amplifiers.insert({
            "name": name,
            "stats": amplifier_stats,
            "cost": cost
        })
        self.bot.reply_to(message, f"Амплификатор {name} успешно добавлен.")

    def remove_amplifier(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return

        parts = message.text.split(" ")
        if len(parts) != 2:
            self.bot.reply_to(
                message,
                "Неверный формат команды! Используйте: /removeamplifier <название>"
            )
            return

        name = parts[1].replace("_", " ")

        amplifier = self.amplifiers.get(self.AmplifierQuery.name == name)
        if not amplifier:
            self.bot.reply_to(message, "Амплификатор с таким именем не найден!")
            return

        self.amplifiers.remove(self.AmplifierQuery.name == name)
        self.bot.reply_to(message, f"Амплификатор {name} успешно удален.")

    def equip_amplifier(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        player_stats = player_data["stats"]

        if player_data["amplifiers"]["equipped"]:
            self.bot.reply_to(message, "У вас уже есть экипированный амплификатор!")
            return

        parts = message.text.split(" ")

        amplifier = self.amplifiers.get(self.AmplifierQuery.name == " ".join(parts[1:]))
        if not amplifier:
            self.bot.reply_to(message, "Такого амплификатора не существует!")
            return

        if amplifier["name"] not in player_data["amplifiers"]["owned"]:
            self.bot.reply_to(message, "У вас нет этого амплификатора в инвентаре!")
            return

        for key, value in amplifier["stats"].items():
            match key:
                case "ATK":
                    player_stats["base"][key] += value
                case "CRIT.DMG" | "PEN":
                    player_stats["modifiers"]["flat"][key] = player_stats["modifiers"]["flat"].get(key, 0) + value
                case _:
                    player_stats["modifiers"]["percent"][key] = player_stats["modifiers"]["percent"].get(key, 0) + value

        player_data["amplifiers"]["equipped"] = amplifier["name"]

        self.players.update({
            "stats": player_data["stats"],
            "amplifiers": player_data["amplifiers"]
        }, self.PlayerQuery.uid == message.from_user.id)

        self.bot.reply_to(message, f"Амплификатор {amplifier['name']} успешно экипирован!")

    def unequip_amplifier(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        player_stats = player_data["stats"]

        if "equipped" not in player_data["amplifiers"] or not player_data["amplifiers"]["equipped"]:
            self.bot.reply_to(message, "У вас нет амплификатора!")
            return

        amplifier = self.amplifiers.get(self.AmplifierQuery.name == player_data["amplifiers"]["equipped"])
        if not amplifier:
            self.bot.reply_to(message, "Экипированный амплификатор не найден!")
            return

        for key, value in amplifier["stats"].items():
            match key:
                case "ATK":
                    player_stats["base"][key] -= int(value)
                case "CRIT.DMG" | "PEN":
                    player_stats["modifiers"]["flat"][key] = player_stats["modifiers"]["flat"].get(key, 0) - value
                case _:
                    player_stats["modifiers"]["percent"][key] = player_stats["modifiers"]["percent"].get(key, 0) - value

        player_data["amplifiers"]["equipped"] = None

        self.players.update({
            "stats": player_data["stats"],
            "amplifiers": player_data["amplifiers"]
        }, self.PlayerQuery.uid == message.from_user.id)

        self.bot.reply_to(message, f"Амплификатор {amplifier['name']} успешно снят!")

    def format_amplifier_stats(self, amplifier_name):
        amplifier = self.amplifiers.get(self.AmplifierQuery.name == amplifier_name)
        stats = amplifier['stats']
        atk = stats.get('ATK', 0)

        extra_stat = None
        extra_value = None
        for key, value in stats.items():
            if key != 'ATK':
                extra_stat = key
                extra_value = value
                break

        stat_display = {
            'CRIT.DMG': '💥 Крит. урон',
            'PEN': '🗡️ Пробивание',
            'HP': '❤️‍🩹 Здоровье',
            'DEF': '🛡️ Защита',
        }

        extra_text = ""
        if extra_stat and extra_value:
            stat_name = stat_display.get(extra_stat, extra_stat)
            if extra_stat not in ('ATK', 'PEN'):
                extra_text = f" • {stat_name} +{extra_value}%"
            else:
                extra_text = f" • {stat_name} +{extra_value}"

        return f"⚔️ Атака +{atk}{extra_text}"

    def open_inventory(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        owned_amplifiers = player_data["amplifiers"].get("owned", [])
        if not owned_amplifiers:
            self.bot.reply_to(message, "Ваш инвентарь экипировки пуст!")
            return

        inventory_text = "_🎒 Ваш инвентарь 🎒_\n\n" + "\n".join(
            [f"*{amplifier}*" + (" (экипирован)" if amplifier == player_data["amplifiers"]["equipped"] else "") + f"\n{self.format_amplifier_stats(amplifier)}" for
             amplifier in
             owned_amplifiers])

        self.bot.send_message(
            message.chat.id,
            inventory_text,
            message_thread_id=message.message_thread_id,
            parse_mode="Markdown"
        )

    def open_amplifier_store(self, message):
        markup = types.InlineKeyboardMarkup()
        for amplifier in self.amplifiers.all():
            button = types.InlineKeyboardButton(
                text=f"{amplifier['name']} — 💰{amplifier['cost']}",
                callback_data=f"buy_amplifier_{amplifier.doc_id}"
            )
            markup.add(button)

        amplifier_list = "\n\n".join([
            f"*{amplifier['name']}*\n{self.format_amplifier_stats(amplifier["name"])}\n💰 Цена: {amplifier['cost']}"
            for amplifier in self.amplifiers.all()
        ])

        self.bot.send_message(
            message.chat.id,
            f"_🛍️ Магазин амплификаторов 🛍️_\n\n{amplifier_list}",
            reply_markup=markup,
            message_thread_id=message.message_thread_id,
            parse_mode="Markdown"
        )

    def buy_amplifier_callback(self, call):
        amp_id = call.data.split("_")[2]

        amplifier = self.amplifiers.get(doc_id=amp_id)
        amplifier_name = amplifier["name"]

        player = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        if not player:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        if player["internot"]["coins"] < amplifier["cost"]:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно монеток для покупки этого амплификатора.",
                show_alert=True
            )
            return

        player["internot"]["coins"] -= amplifier["cost"]
        if "owned" not in player["amplifiers"]:
            player["amplifiers"]["owned"] = []
        player["amplifiers"]["owned"].append(amplifier_name)

        self.players.update({
            "internot": player["internot"],
            "amplifiers": player["amplifiers"]
        }, self.PlayerQuery.uid == call.from_user.id)

        self.bot.answer_callback_query(call.id, f"Вы успешно купили амплификатор {amplifier_name}!", show_alert=True)


