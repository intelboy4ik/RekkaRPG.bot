import random

from telebot import types


class DecoderSystem:
    def __init__(self, bot, players, playerquery, amplifiers, amplifierquery):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.amplifiers = amplifiers
        self.AmplifierQuery = amplifierquery
        self.b_tier_amplifiers = self.amplifiers.search(self.AmplifierQuery.tier == "B")
        self.a_tier_amplifiers = self.amplifiers.search(self.AmplifierQuery.tier == "A")
        self.s_tier_amplifiers = self.amplifiers.search(self.AmplifierQuery.tier == "S")

    def register_handlers(self):
        self.bot.message_handler(commands=["decoder"])(self.open_signal)
        self.bot.callback_query_handler(
            func=lambda call: call.data in ["try_decode_x1", "try_decode_x10"]
        )(self.try_decode_callback)
        self.bot.message_handler(commands=["decoderinfo"])(self.info)

    def open_signal(self, message):
        markup = types.InlineKeyboardMarkup()
        button_search_x1 = types.InlineKeyboardButton("🔍 Попытка (1x)", callback_data="try_decode_x1")
        button_search_x10 = types.InlineKeyboardButton("🔍 Попытка (10x)", callback_data="try_decode_x10")
        markup.row(button_search_x1, button_search_x10)
        self.bot.reply_to(
            message,
            "_📺 Открыта дешифровка записей._"
            "\n\n"
            "**Выберите действие:**",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    def try_decode_callback(self, call):
        player_data = self.players.get(self.PlayerQuery.uid == call.from_user.id)
        if not player_data:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        result = []

        if call.data == "try_decode_x1":
            if player_data["decoder"]["videotapes"] < 1:
                self.bot.answer_callback_query(
                    call.id,
                    "У вас недостаточно видеокассет для дешифровки.",
                    show_alert=True,
                )
                return
            result.append(self.calc_decode_res(call))
            self.bot.send_message(
                call.message.chat.id,
                "_🔍 Вы провели расшифровку одной видеокассеты._"
                "\n\n"
                "*Результаты*"
                "\n" +
                "\n".join(
                    f"{'🔶' if amp['tier'] == 'S' else '🔸' if amp['tier'] == "A" else '🔹'} {amp['name']}" for amp in
                    result),
                parse_mode="Markdown",
                message_thread_id=call.message.message_thread_id
            )
            return

        if player_data["decoder"]["videotapes"] < 10:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно видеокассет для дешифровки.",
                show_alert=True,
            )
            return
        for _ in range(10):
            result.append(self.calc_decode_res(call))
        self.bot.send_message(
            call.message.chat.id,
            "_🔍 Вы провели расшифровку десяти видеокассет._"
            "\n\n"
            "*Результаты*"
            "\n" +
            "\n".join(
                f"{'🔶' if amp['tier'] == 'S' else '🔸' if amp['tier'] == "A" else '🔹'} {amp['name']}" for amp in result),
            parse_mode="Markdown",
            message_thread_id=call.message.message_thread_id
        )

    def info(self, message):
        self.bot.reply_to(
            message,
            f"*Приветствуем в справочной Интернота!*"
            f"\n\n"
            f"В этой статье мы расскажем о системе дешифровки записей и видеокассетах."
            f"\n\n"
            f"• *Видеокассеты* — это специальный ресурс, необходимый для дешифровки записей."
            f"\n\n"
            f"• *Дешифровка записей* позволяет игрокам находить различные амплификаторы, которые могут улучшить их характеристики в бою."
            f"\n"
            f"При расшифровке записей вы можете получить амплификаторы трёх уровней редкости: 🔹B, 🔸A и 🔶S."
            f"\n\n"
            f"• *Каковы шансы получения амплификаторов?*"
            f"\n"
            f"🔶 Амплификаторы редкости S имеют шанс выпадения около **1.2%**."
            f"\n"
            f"🔸 Амплификаторы редкости A имеют шанс выпадения около **14%**."
            f"\n"
            f"🔹 Амплификаторы редкости B имеют наибольший шанс выпадения."
            f"\n\n"
            f"• *Система гарантий:*"
            f"\n"
            f"Амплификаторы тиров A и S имеют систему гарантий, которая увеличивает ваши шансы на получение этих амплификаторов при последующих дешифровках."
            f"\n"
            f"Так, амплификатор тира A гарантированно выпадет в течении **10 расшифровок**, а амплификатор тира S — в течении **90 расшифровок**."
            f"\n\n"
            f"• *Повторное получение*"
            f"При дешифровке, вы можете получить амплификатор, который уже есть в вашем инвентаре."
            f"Если это произойдёт, вы получите компенсацию в виде видеокассет или денни."
            f"Амплификаторы редкости B компенсируются **денни**, в то время как амплификаторы редкости A и S компенсируются **видеокассетами**."
            ,
            parse_mode="Markdown"
        )

    def calc_decode_res(self, call):
        player = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        player["decoder"]["videotapes"] -= 1
        player["decoder"]["decoded"] += 1

        player["decoder"]["guarantee"]["a-tier"] -= 1
        player["decoder"]["guarantee"]["s-tier"] -= 1

        dice = random.randint(1, 1000)

        if dice <= 12 or player["decoder"]["guarantee"]["s-tier"] <= 0:
            amplifier = random.choice(self.s_tier_amplifiers)

            if amplifier["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amplifier["name"])
            else:
                player["decoder"]["videotapes"] += 5

            player["decoder"]["guarantee"]["a-tier"] = 10
            player["decoder"]["guarantee"]["s-tier"] = 90

        elif dice <= 140 or player["decoder"]["guarantee"]["a-tier"] <= 0:
            amplifier = random.choice(self.a_tier_amplifiers)

            if amplifier["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amplifier["name"])
            else:
                player["decoder"]["videotapes"] += 2

            player["decoder"]["guarantee"]["a-tier"] = 10

        else:
            amplifier = random.choice(self.b_tier_amplifiers)

            if amplifier["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amplifier["name"])
            else:
                player["progression"]["denny"] += 35

        self.players.update(
            {
                "decoder": player["decoder"],
                "amplifiers": player["amplifiers"],
                "progression": player["progression"],
            },
            self.PlayerQuery.uid == player["uid"]
        )

        return amplifier
