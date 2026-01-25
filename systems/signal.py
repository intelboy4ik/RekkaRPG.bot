import random

from telebot import types


class SignalSystem:
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
        self.bot.message_handler(commands=["opensignals"])(self.open_signal)
        self.bot.callback_query_handler(
            func=lambda call: call.data in ["search_signal_x1", "search_signal_x10"]
        )(self.search_signal_callback)
        self.bot.message_handler(commands=["infosignals"])(self.info)

    def open_signal(self, message):
        markup = types.InlineKeyboardMarkup()
        button_search_x1 = types.InlineKeyboardButton("🔍 Искать (1x)", callback_data="search_signal_x1")
        button_search_x10 = types.InlineKeyboardButton("🔍 Искать (10x)", callback_data="search_signal_x10")
        markup.row(button_search_x1, button_search_x10)
        self.bot.reply_to(message, "_📺 Открыт поиск сигналов._\n\n**Выберите действие:**", reply_markup=markup,
                          parse_mode="Markdown")

    def search_signal_callback(self, call):
        player_data = self.players.get(self.PlayerQuery.uid == call.from_user.id)
        if not player_data:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        result = []

        if call.data == "search_signal_x1":
            if player_data["signals"]["videotapes"] < 1:
                self.bot.answer_callback_query(
                    call.id,
                    "У вас недостаточно кассет для поиска сигнала.",
                    show_alert=True,
                )
                return
            result.append(self.calc_search_res(call))
            self.bot.send_message(
                call.message.chat.id,
                "_🔍 Вы провели поиск сигнала с использованием 1 видеокассеты._"
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

        if player_data["signals"]["videotapes"] < 10:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно видеокассет для поиска сигнала.",
                show_alert=True,
            )
            return
        for _ in range(10):
            result.append(self.calc_search_res(call))
        self.bot.send_message(
            call.message.chat.id,
            "_🔍 Вы провели поиск сигнала с использованием 10 видеокассет._"
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
            f"В этой статье мы расскажем о системе поиска сигналов и видеокассетах."
            f"\n\n"
            f"• *Видеокассеты* — это специальный ресурс, необходимый для поиска сигналов."
            f"\n"
            f"Каждая попытка поиска сигнала требует определённого количества видеокассет."
            f"\n\n"
            f"• *Поиск сигналов* позволяет игрокам находить различные амплификаторы, которые могут улучшить их характеристики в бою."
            f"\n"
            f"При поиске сигнала вы можете получить амплификаторы трёх уровней редкости: 🔹B, 🔸A и 🔶S."
            f"\n\n"
            f"• *Каковы шансы получения амплификаторов?*"
            f"\n"
            f"🔶 Амплификаторы тира S имеют шанс выпадения около **1.2%**."
            f"\n"
            f"🔸 Амплификаторы тира A имеют шанс выпадения около **14%**."
            f"\n"
            f"🔹 Амплификаторы тира B имеют наибольший шанс выпадения."
            f"\n\n"
            f"• *Система гарантий:*"
            f"\n"
            f"Амплификаторы тиров A и S имеют систему гарантий, которая увеличивает ваши шансы на получение этих амплификаторов при последующих поисках."
            f"\n"
            f"Так, амплификатор тира A гарантированно выпадет в течении **10 поисков**, а амплификатор тира S — в течении **90 поисков**."
            f"\n\n"
            f"• *Повторное получение*"
            f"При поиске сигнала, вы можете получить амплификатор, который уже есть в вашем инвентаре."
            f"Если это произойдёт, вы получите компенсацию в виде видеокассет или монеток."
            f"Амплификаторы тира B компенсируются **монетками**, в то время как амплификаторы тиров A и S компенсируются **видеокассетами**."
            ,
            parse_mode="Markdown"
        )

    def calc_search_res(self, call):
        player = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        player["signals"]["videotapes"] -= 1
        player["signals"]["searched"] += 1

        player["signals"]["guarantee"]["a-tier"] -= 1
        player["signals"]["guarantee"]["s-tier"] -= 1

        dice = random.randint(1, 1000)

        if dice <= 12 or player["signals"]["guarantee"]["s-tier"] <= 0:
            amplifier = random.choice(self.s_tier_amplifiers)

            if amplifier["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amplifier["name"])
            else:
                player["signals"]["videotapes"] += 5

            player["signals"]["guarantee"]["a-tier"] = 10
            player["signals"]["guarantee"]["s-tier"] = 90

        elif dice <= 140 or player["signals"]["guarantee"]["a-tier"] <= 0:
            amplifier = random.choice(self.a_tier_amplifiers)

            if amplifier["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amplifier["name"])
            else:
                player["signals"]["videotapes"] += 2

            player["signals"]["guarantee"]["a-tier"] = 10

        else:
            amplifier = random.choice(self.b_tier_amplifiers)

            if amplifier["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amplifier["name"])
            else:
                player["internot"]["coins"] += 35

        self.players.update(
            {
                "signals": player["signals"],
                "amplifiers": player["amplifiers"],
                "internot": player["internot"],
            },
            self.PlayerQuery.uid == player["uid"]
        )

        return amplifier
