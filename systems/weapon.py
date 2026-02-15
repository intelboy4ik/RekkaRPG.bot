from config import is_admin, WEAPON_POSSIBLE_STATS


class WeaponSystem:
    def __init__(self, bot, weapons, weaponqueery, players, playerquery, stats_system=None):
        self.bot = bot
        self.weapons = weapons
        self.WeaponQuery = weaponqueery
        self.players = players
        self.PlayerQuery = playerquery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(commands=["addweapon"])(self.add_weapon)
        self.bot.message_handler(commands=["removeweapon"])(self.remove_weapon)
        self.bot.message_handler(commands=["equip"])(self.equip_weapon)
        self.bot.message_handler(commands=["unequip"])(self.unequip_weapon)
        self.bot.message_handler(commands=["inventory"])(self.open_inventory)
        self.bot.message_handler(commands=["weaponsinfo"])(self.info)

    def add_weapon(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return

        parts = message.text.split(" ")
        if len(parts) < 7:
            self.bot.reply_to(
                message,
                "Неверный формат команды!"
                "\n\n"
                "Используйте: /addweapon <название> <атака> <характеристика> <значение> <тир> <цена>"
            )
            return

        name = parts[1].replace("_", " ")
        attack = int(parts[2])

        stat = parts[3].upper()
        if stat not in WEAPON_POSSIBLE_STATS:
            self.bot.reply_to(
                message,
                f"Неверная характеристика! Допустимые характеристики: {', '.join(WEAPON_POSSIBLE_STATS)}"
            )
            return
        stat_value = int(parts[4])

        rank = parts[5].upper()
        if rank not in ["B", "A", "S"]:
            self.bot.reply_to(
                message,
                "Неверный тир! Допустимые ранги: B, A, S"
            )
            return

        cost = int(parts[6])

        attr_name = None
        attr_bonus = None

        if len(parts) == 9:
            attr_name = parts[7]
            attr_bonus = int(parts[8])

        if self.weapons.get(self.WeaponQuery.name == name):
            self.bot.reply_to(message, "Амплификатор с таким именем уже существует!")
            return

        weapon_stats = {
            "ATK": attack,
            stat: stat_value,
        }
        self.weapons.insert({
            "name": name,
            "stats": weapon_stats,
            "attribute": {
                "name": attr_name,
                "bonus": attr_bonus,
            },
            "cost": cost,
            "rank": rank
        })
        self.bot.reply_to(message, f"Амплификатор {name} успешно добавлен.")

    def remove_weapon(self, message):
        if not is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return

        parts = message.text.split(" ")
        if len(parts) != 2:
            self.bot.reply_to(
                message,
                "Неверный формат команды! Используйте: /removeweapon <название>"
            )
            return

        name = parts[1].replace("_", " ")

        weapons = self.weapons.get(self.WeaponQuery.name == name)
        if not weapons:
            self.bot.reply_to(message, "Амплификатор с таким именем не найден!")
            return

        self.weapons.remove(self.WeaponQuery.name == name)
        self.bot.reply_to(message, f"Амплификатор {name} успешно удален.")

    def equip_weapon(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        player_stats = player_data["stats"]

        parts = message.text.split(" ")

        weapons = self.weapons.get(self.WeaponQuery.name == " ".join(parts[1:]))
        if not weapons:
            self.bot.reply_to(message, "Такого амплификатора не существует!")
            return

        if weapons["name"] not in player_data["weapons"]["owned"]:
            self.bot.reply_to(message, "У вас нет этого амплификатора в инвентаре!")
            return

        if player_data["weapons"]["equipped"]:
            self.bot.reply_to(message, "Сначала снимите текущий амплификатор с помощью команды /unequip")
            return

        if weapons['attribute']['name'] == player_data["attribute"]:
            player_stats["ATTR.DMG"] = weapons['attribute']['bonus']

        for key, value in weapons["stats"].items():
            match key:
                case "ATK":
                    player_stats["base"]["ATK"] += value
                case "CRIT.DMG" | "PEN" if weapons['attribute']['name'] == player_data["attribute"]:
                    player_stats["modifiers"]["flat"][key] = player_stats["modifiers"]["flat"].get(key, 0) + value
                case _ if weapons['attribute']['name'] == player_data["attribute"]:
                    player_stats["modifiers"]["percent"][key] = player_stats["modifiers"]["percent"].get(key, 0) + value

        player_data["weapons"]["equipped"] = weapons["name"]

        self.players.update({
            "stats": player_data["stats"],
            "weapons": player_data["weapons"]
        }, self.PlayerQuery.uid == message.from_user.id)

        self.bot.reply_to(message, f"Амплификатор {weapons['name']} успешно экипирован!")

    def unequip_weapon(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        player_stats = player_data["stats"]

        if "equipped" not in player_data["weapons"] or not player_data["weapons"]["equipped"]:
            self.bot.reply_to(message, "У вас нет амплификатора!")
            return

        weapons = self.weapons.get(self.WeaponQuery.name == player_data["weapons"]["equipped"])
        if not weapons:
            self.bot.reply_to(message, "Экипированный амплификатор не найден!")
            return

        if weapons['attribute']['name'] == player_data["attribute"]:
            player_stats["ATTR.DMG"] = weapons['attribute']['bonus']

        for key, value in weapons["stats"].items():
            match key:
                case "ATK":
                    player_stats["base"]["ATK"] -= value
                case "CRIT.DMG" | "PEN" if weapons['attribute']['name'] == player_data["attribute"]:
                    player_stats["modifiers"]["flat"][key] = player_stats["modifiers"]["flat"].get(key, 0) - value
                case _ if weapons['attribute']['name'] == player_data["attribute"]:
                    player_stats["modifiers"]["percent"][key] = player_stats["modifiers"]["percent"].get(key, 0) - value

        player_data["weapons"]["equipped"] = None

        self.players.update({
            "stats": player_data["stats"],
            "weapons": player_data["weapons"]
        }, self.PlayerQuery.uid == message.from_user.id)

        self.bot.reply_to(message, f"Амплификатор {weapons['name']} успешно снят!")

    def format_weapon_stats(self, weapon_name):
        weapons = self.weapons.get(self.WeaponQuery.name == weapon_name)
        stats = weapons['stats']
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

        attr_emojis = {
            "fire": "🔥",
            "ice": "❄️",
            "electricity": "⚡️",
            "physics": "💥"
        }

        attr_name = weapons["attribute"]["name"]
        bonus = weapons["attribute"]["bonus"]

        emoji = attr_emojis.get(attr_name, "")

        attr_text = f"{emoji} {bonus}%".lstrip()

        return f"⚔️ Атака +{atk}\n{extra_text}\n{attr_text}"

    def open_inventory(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        owned_weapons = player_data["weapons"].get("owned", [])
        if not owned_weapons:
            self.bot.reply_to(message, "Ваш инвентарь пуст!")
            return

        inventory_text = "_🎒 Ваш инвентарь_\n\n" + "\n".join(
            [
                f"*{weapons}*"
                + (" (экипирован)" if weapons == player_data["weapons"]["equipped"] else "")
                + f"\n{self.format_weapon_stats(weapons)}\n"
                for weapons in owned_weapons
            ]
        )

        self.bot.send_message(
            message.chat.id,
            inventory_text,
            message_thread_id=message.message_thread_id,
            parse_mode="Markdown"
        )

    def info(self, message):
        self.bot.reply_to(
            message,
            f"*Приветствуем в справочной Интернота!*"
            f"\n\n"
            f"В этой статье мы расскажем об Амплификаторах."
            f"\n\n"
            f"• *Амплификатор* — это предмет экипировки, который даёт вашему персонажу дополнительные характеристики."
            f"\n\n"
            f"• *Как это работает?*"
            f"\n"
            f"После того как вы получили амплификатор в декодере, вы можете экипировать его."
            f"\n"
            f"Так вы получите бонус к базовой атаке, и к дополнительной характеристике."
            f"\n\n"
            f"• *Характеристика работает не всегда*."
            f"\n"
            f"Чтобы характеристика работало, необходимо чтобы атрибут амплификатора совпадал с вашим."
            ,
            parse_mode="Markdown"
        )