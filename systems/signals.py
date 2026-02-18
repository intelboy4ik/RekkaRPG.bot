import random

from telebot import types


class SignalSystem:
    def __init__(self, bot, players, playerquery, amplifiers, amplifierquery):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.amplifiers = amplifiers
        self.AmplifierQuery = amplifierquery
        self.b_rank_amplifiers = self.amplifiers.search(self.AmplifierQuery.rank == "B")
        self.a_rank_amplifiers = self.amplifiers.search(self.AmplifierQuery.rank == "A")
        self.s_rank_amplifiers = self.amplifiers.search(self.AmplifierQuery.rank == "S")

    def register_handlers(self):
        self.bot.message_handler(commands=["signal"])(self.open_channel)
        self.bot.callback_query_handler(
            func=lambda call: call.data in ["search_x1", "search_x10"]
        )(self.pull_callback)
        self.bot.message_handler(commands=["sgnlinfo"])(self.info)

    def open_channel(self, message):
        markup = types.InlineKeyboardMarkup()
        button_search_x1 = types.InlineKeyboardButton("🔍 Поиск (1x)", callback_data="search_x1")
        button_search_x10 = types.InlineKeyboardButton("🔍 Поиск (10x)", callback_data="search_x10")
        markup.row(button_search_x1, button_search_x10)
        self.bot.reply_to(
            message,
            "_📺 Открыт поиск сигналов._"
            "\n\n"
            "**Выберите действие:**",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    def pull_callback(self, call):
        player_data = self.players.get(self.PlayerQuery.uid == call.from_user.id)
        if not player_data:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        result = []

        rank_emojis = {
            "S": "🔶",
            "A": "🔸",
            "B": "🔹"
        }

        if call.data == "search_x1":
            if player_data["channel"]["masterTapes"] < 1:
                self.bot.answer_callback_query(
                    call.id,
                    "У вас недостаточно шифрокопий для поиска.",
                    show_alert=True,
                )
                return
            result.append(self.calc_pull_res(call))
            self.bot.send_message(
                call.message.chat.id,
                "_🔍 Вы провели поиск с использованием одной шифрокопии._"
                "\n\n"
                "*Результаты*"
                "\n" +
                "\n".join(
                    f"{rank_emojis[amp["rank"]]} {amp['name']}" for amp in
                    result),
                parse_mode="Markdown",
                message_thread_id=call.message.message_thread_id
            )
            return

        if player_data["channel"]["masterTapes"] < 10:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно шифрокопий для поиска сигнала.",
                show_alert=True,
            )
            return

        for _ in range(10):
            result.append(self.calc_pull_res(call))

        self.bot.send_message(
            call.message.chat.id,
            "_🔍 Вы провели поиск с использованием десяти шифрокопий._"
            "\n\n"
            "*Результаты*"
            "\n" +
            "\n".join(
                f"{rank_emojis[amp["rank"]]} {amp['name']}" for amp in result),
            parse_mode="Markdown",
            message_thread_id=call.message.message_thread_id
        )

    def info(self, message):
        self.bot.reply_to(
            message,
            f"*Приветствуем в справочной Интернота!*"
            f"\n\n"
            f"В этой статье мы расскажем о системе поиска сигналов и шифрокопиях."
            f"\n\n"
            f"• *Шифрокопии* — это специальный ресурс, необходимый для поиска сигналов."
            f"\n\n"
            f"• *Поиск сигнала* позволяет игрокам получать различные амплификаторы, которые могут улучшить их характеристики в бою."
            f"\n"
            f"При поиске записей вы можете получить амплификаторы трёх уровней редкости: 🔹B, 🔸A и 🔶S."
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
            f"Амплификаторы редкости A и S имеют систему гарантий, которая увеличивает ваши шансы на получение этих амплификаторов при последующих дешифровках."
            f"\n"
            f"Так, амплификатор редкости A гарантированно выпадет в течении **10 поисков**, а амплификатор редкости S — в течении **90 поисков**."
            f"\n\n"
            f"• *Повторное получение*"
            f"При дешифровке, вы можете получить амплификатор, который уже есть в вашем инвентаре."
            f"Если это произойдёт, вы получите компенсацию в виде видеокассет или денни."
            f"Амплификаторы редкости B компенсируются **денни**, в то время как амплификаторы редкости A и S компенсируются **шифрокопиями**."
            ,
            parse_mode="Markdown"
        )

    def calc_pull_res(self, call):
        player = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        player["channel"]["masterTapes"] -= 1
        player["channel"]["pulled"] += 1

        player["channel"]["guarantee"]["a-rank"] -= 1
        player["channel"]["guarantee"]["s-rank"] -= 1

        dice = random.randint(1, 1000)

        if dice <= 12 or player["channel"]["guarantee"]["s-rank"] <= 0:
            amp = random.choice(self.s_rank_amplifiers)

            if amp["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amp["name"])
            else:
                player["channel"]["masterTapes"] += 5

            player["channel"]["guarantee"]["a-rank"] = 10
            player["channel"]["guarantee"]["s-rank"] = 90

        elif dice <= 140 or player["channel"]["guarantee"]["a-rank"] <= 0:
            amp = random.choice(self.a_rank_amplifiers)

            if amp["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amp["name"])
            else:
                player["channel"]["masterTapes"] += 2

            player["channel"]["guarantee"]["a-rank"] = 10

        else:
            amp = random.choice(self.b_rank_amplifiers)

            if amp["name"] not in player["amplifiers"]["owned"]:
                player["amplifiers"]["owned"].append(amp["name"])
            else:
                player["interknot"]["denny"] += 35

        self.players.update(
            {
                "channel": player["channel"],
                "amplifiers": player["amplifiers"],
                "interknot": player["interknot"],
            },
            self.PlayerQuery.uid == player["uid"]
        )

        return amp
