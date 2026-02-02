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

    def add_amplifier(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return

        parts = message.text.split(" ")
        if len(parts) != 7:
            self.bot.reply_to(
                message,
                "Неверный формат команды!"
                "\n\n"
                "Используйте: /addamplifier <название> <атака> <характеристика> <значение> <тир> <цена>"
            )
            return

        name = parts[1].replace("_", " ")
        attack = int(parts[2])

        stat = parts[3].upper()
        if stat not in AMPLIFIER_POSSIBLE_STATS:
            self.bot.reply_to(
                message,
                f"Неверная характеристика! Допустимые характеристики: {', '.join(AMPLIFIER_POSSIBLE_STATS)}"
            )
            return
        stat_value = int(parts[4])

        tier = parts[5].upper()
        if tier not in ["B", "A", "S"]:
            self.bot.reply_to(
                message,
                "Неверный тир! Допустимые тиры: B, A, S"
            )
            return

        cost = int(parts[6])

        if self.amplifiers.get(self.AmplifierQuery.name == name):
            self.bot.reply_to(message, "Амплификатор с таким именем уже существует!")
            return

        amplifier_stats = {
            "ATK": attack,
            stat: stat_value,
        }
        self.amplifiers.insert({
            "name": name,
            "stats": amplifier_stats,
            "cost": cost,
            "tier": tier
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

        parts = message.text.split(" ")

        amplifier = self.amplifiers.get(self.AmplifierQuery.name == " ".join(parts[1:]))
        if not amplifier:
            self.bot.reply_to(message, "Такого амплификатора не существует!")
            return

        if amplifier["name"] not in player_data["amplifiers"]["owned"]:
            self.bot.reply_to(message, "У вас нет этого амплификатора в инвентаре!")
            return

        if player_data["amplifiers"]["equipped"]:
            self.bot.reply_to(message, "Сначала снимите текущий амплификатор с помощью команды /unequip")
            return

        for key, value in amplifier["stats"].items():
            match key:
                case "CRIT.DMG" | "PEN" | "ATK":
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
                case "CRIT.DMG" | "PEN" | "ATK":
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
                extra_text = f"{stat_name} +{extra_value}%"
            else:
                extra_text = f"{stat_name} +{extra_value}"

        return f"⚔️ Атака +{atk}\n{extra_text}"

    def open_inventory(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        owned_amplifiers = player_data["amplifiers"].get("owned", [])
        if not owned_amplifiers:
            self.bot.reply_to(message, "Ваш инвентарь пуст!")
            return

        inventory_text = "_🎒 Ваш инвентарь_\n\n" + "\n".join(
            [
                f"*{amplifier}*"
                + (" (экипирован)" if amplifier == player_data["amplifiers"]["equipped"] else "")
                + f"\n{self.format_amplifier_stats(amplifier)}\n"
                for amplifier in owned_amplifiers
            ]
        )

        self.bot.send_message(
            message.chat.id,
            inventory_text,
            message_thread_id=message.message_thread_id,
            parse_mode="Markdown"
        )
