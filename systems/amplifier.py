from telebot import types

import config


class AmplifierSystem:
    def __init__(self, bot, amplifiers, amplifierquery, user, userequery, stats_system=None):
        self.bot = bot
        self.amplifiers = amplifiers
        self.AmplifierQuery = amplifierquery
        self.user = user
        self.UserQuery = userequery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(commands=["addamplifier"])(self.add_amplifier)
        self.bot.message_handler(commands=["equip"])(self.equip_amplifier)
        self.bot.message_handler(commands=["unequip"])(self.unequip_amplifier)
        self.bot.message_handler(commands=["store"])(self.open_amplifier_store)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("buy_amplifier_"))(
            self.buy_amplifier_callback)

    def add_amplifier(self, message):
        if not config.is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return

        parts = message.text.split(" ")
        if len(parts) != 6:
            self.bot.reply_to(
                message,
                "Неверный формат команды! Используйте: /addamplifier <название> <атака> <характеристика> <значение> <цена>"
            )
            return
        amplifier_name = parts[1].replace("_", " ")

        if self.amplifiers.get(self.AmplifierQuery.name == amplifier_name):
            self.bot.reply_to(message, "Амплификатор с таким именем уже существует!")
            return

        if len(self.amplifiers) >= 12:
            self.bot.reply_to(message, "Максимальное количество амплификаторов достигнуто!")
            return

        amplifier_stats = {
            "ATK": parts[2],
            parts[3].upper(): parts[4],
        }
        self.amplifiers.insert({
            "name": amplifier_name,
            "stats": amplifier_stats,
            "cost": int(parts[5])
        })
        self.bot.reply_to(message, f"Амплификатор {amplifier_name} успешно добавлен.")

    def equip_amplifier(self, message):
        user_data = self.user.get(self.UserQuery.user_id == message.from_user.id)
        if not user_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        if user_data["amplifiers"]["equipped"]:
            self.bot.reply_to(message, "У вас уже есть экипированный амплификатор!")
            return

        parts = message.text.split(" ")

        amplifier = self.amplifiers.get(self.AmplifierQuery.name == " ".join(parts[1:]))
        if not amplifier:
            self.bot.reply_to(message, "Такого амплификатора не существует!")
            return

        if amplifier["name"] not in user_data["amplifiers"]["owned"]:
            self.bot.reply_to(message, "У вас нет этого амплификатора в инвентаре!")
            return

        for key, value in amplifier["stats"].items():
            if key == "CRIT.DMG" or key == "ATK" or key == "PEN":
                user_data["stats"]["modifiers"]["flat"][key] = user_data["stats"]["modifiers"]["flat"].get(
                    key,
                    0
                ) + int(value)
            else:
                user_data["stats"]["modifiers"]["percent"][key] = user_data["stats"]["modifiers"]["percent"].get(
                    key,
                    0
                ) + int(value)

        user_data["amplifiers"]["equipped"] = amplifier["name"]

        self.user.update({
            "stats": user_data["stats"],
            "amplifiers": user_data["amplifiers"]
        }, self.UserQuery.user_id == message.from_user.id)

        self.bot.reply_to(message, f"Амплификатор {amplifier['name']} успешно экипирован!")

    def unequip_amplifier(self, message):
        user_data = self.user.get(self.UserQuery.user_id == message.from_user.id)
        if not user_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        if "equipped" not in user_data["amplifiers"] or not user_data["amplifiers"]["equipped"]:
            self.bot.reply_to(message, "У вас нет экипированного амплификатора!")
            return

        amplifier = self.amplifiers.get(self.AmplifierQuery.name == user_data["amplifiers"]["equipped"])
        if not amplifier:
            self.bot.reply_to(message, "Экипированный амплификатор не найден!")
            return

        for key, value in amplifier["stats"].items():
            if key == "CRIT.DMG" or key == "ATK" or key == "PEN":
                user_data["stats"]["modifiers"]["flat"][key] = (user_data["stats"]["modifiers"]["flat"].get(
                    key,
                    0
                ) - int(value))
            else:
                user_data["stats"]["modifiers"]["percent"][key] = user_data["stats"]["modifiers"]["percent"].get(
                    key,
                    0
                ) - int(value)

        user_data["amplifiers"]["equipped"] = None

        self.user.update({
            "stats": user_data["stats"],
            "amplifiers": user_data["amplifiers"]
        }, self.UserQuery.user_id == message.from_user.id)

        self.bot.reply_to(message, f"Амплификатор {amplifier['name']} успешно снят!")

    def open_amplifier_store(self, message):
        markup = types.InlineKeyboardMarkup()
        for amplifier in self.amplifiers.all():
            button = types.InlineKeyboardButton(
                text=f"{amplifier['name']} • {amplifier['cost']} 🪙",
                callback_data=f"buy_amplifier_{amplifier.doc_id}"
            )
            markup.row(button)

        self.bot.send_message(
            message.chat.id,
            f"_🛍️ Магазин амплификаторов_\n\n" +
            "\n".join(
                [f"*{amplifier['name']}* • Атака {amplifier['stats']['ATK']}\n" for amplifier in self.amplifiers]),
            reply_markup=markup,
            parse_mode="Markdown"
        )

    def buy_amplifier_callback(self, call):
        amp_id = call.data.split("_")[2]

        amplifier = self.amplifiers.get(doc_id=amp_id)
        amplifier_name = amplifier["name"]

        user = self.user.get(self.UserQuery.user_id == call.from_user.id)

        if not user:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        if user["internot"]["coins"] < amplifier["cost"]:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно монеток для покупки этого амплификатора.",
                show_alert=True
            )
            return

        user["internot"]["coins"] -= amplifier["cost"]
        if "owned" not in user["amplifiers"]:
            user["amplifiers"]["owned"] = []
        user["amplifiers"]["owned"].append(amplifier_name)

        self.user.update({
            "internot": user["internot"],
            "amplifiers": user["amplifiers"]
        }, self.UserQuery.user_id == call.from_user.id)

        self.bot.answer_callback_query(call.id, f"Вы успешно купили амплификатор {amplifier_name}!", show_alert=True)
