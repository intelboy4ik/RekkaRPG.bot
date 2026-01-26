import random

from telebot import types


class StoreSystem:
    def __init__(self, bot, players, playerquery, amplifiers, amplifierquery, amplifier_system):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.amplifiers = amplifiers
        self.AmplifierQuery = amplifierquery
        self.amplifier_system = amplifier_system

    def register_handlers(self):
        self.bot.message_handler(commands=["store"])(self.open_store)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("buy_amplifier_"))(
            self.buy_amplifier_callback)
        self.bot.callback_query_handler(func=lambda call: call.data in ["buy_videotape_1", "buy_videotape_10"])(
            self.buy_videotape_callback)

    def open_store(self, message):
        amplifiers = self.amplifiers.search(self.AmplifierQuery.cost > 0)
        markup = types.InlineKeyboardMarkup()
        for amplifier in amplifiers:
            button = types.InlineKeyboardButton(
                text=f"{amplifier['name']}",
                callback_data=f"buy_amplifier_{amplifier.doc_id}"
            )
            markup.add(button)

        one_videotape_button = types.InlineKeyboardButton(
            text="📼 1 кассета",
            callback_data="buy_videotape_1"
        )
        ten_videotape_button = types.InlineKeyboardButton(
            text="📼 10 кассет",
            callback_data="buy_videotape_10"
        )
        markup.row(one_videotape_button, ten_videotape_button)

        amplifier_list = "\n\n".join([
            f"*{amplifier['name']}*"
            f"\n"
            f"{self.amplifier_system.format_amplifier_stats(amplifier["name"])}"
            f"\n"
            f"💰 Цена: {amplifier['cost']}"
            for amplifier in amplifiers
        ])

        random_phrase = random.choice(["Впервые в продаже!", "Специальное предложение!", "Только сегодня!", "Не пропустите!"])

        self.bot.send_message(
            message.chat.id,
            f"_🛍️ Магазин амплификаторов_\n\n{amplifier_list}"
            f"\n\n"
            f"_📺 {random_phrase} Видеокассеты для дешифровки!_"
            f"\n\n"
            f"1 кассета — 360 монеток, 10 кассет — 3600 монеток...",
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

    def buy_videotape_callback(self, call):
        quantity = 1 if call.data == "buy_videotape_1" else 10
        cost = 360 * quantity

        player = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        if not player:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        if player["internot"]["coins"] < cost:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно монеток для покупки видеокассет.",
                show_alert=True
            )
            return

        player["internot"]["coins"] -= cost
        player["signals"]["videotapes"] += quantity

        self.players.update({
            "internot": player["internot"],
            "signals": player["signals"]
        }, self.PlayerQuery.uid == call.from_user.id)

        self.bot.answer_callback_query(
            call.id,
            f"Вы успешно купили {quantity} видеокассету(ы)!",
            show_alert=True
        )