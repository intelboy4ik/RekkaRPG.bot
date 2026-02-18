import config


class RedeemSystem:
    def __init__(self, bot, players, playerquery, amplifier, amplifierquery, codes, codequery):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.amplifier = amplifier
        self.AmplifierQuery = amplifierquery
        self.codes = codes
        self.CodeQuery = codequery

    def register_handlers(self):
        self.bot.message_handler(commands=["addredeemcode"])(self.add_redeem_code)
        self.bot.message_handler(commands=["removeredeemcode"])(self.remove_redeem_code)
        self.bot.message_handler(commands=["redeem"])(self.redeem_code)

    def add_redeem_code(self, message):
        if not config.is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return
        parts = message.text.split(" ")

        if len(parts) != 4:
            self.bot.reply_to(message, "Неверный формат команды! Используйте: /addredeemcode <тип> <награда> <код>")
            return

        code_type = parts[1]
        code_reward = parts[2]
        code = parts[3]

        code_reward.replace("_", " ")

        if code_type not in ["videotape", "denny", "amplifier"]:
            self.bot.reply_to(message, "Неверный тип кода! Допустимые типы: videotape, denny, amplifier")
            return

        if self.codes.get(self.CodeQuery.code == code):
            self.bot.reply_to(message, "Такой код уже существует!")
            return

        self.codes.insert({
            "code": code.upper(),
            "type": code_type,
            "reward": code_reward,
            "redeemed_by": []
        })
        self.bot.reply_to(message, f"Код {code} успешно добавлен.")

    def remove_redeem_code(self, message):
        if not config.is_admin(message.from_user.id):
            self.bot.reply_to(message, "У вас нет прав для использования этой команды.")
            return
        parts = message.text.split(" ")

        if len(parts) != 2:
            self.bot.reply_to(message, "Неверный формат команды! Используйте: /removeredeemcode <код>")
            return

        code = parts[1]

        if not self.codes.get(self.CodeQuery.code == code):
            self.bot.reply_to(message, "Такой код не найден!")
            return

        self.codes.remove(self.CodeQuery.code == code)
        self.bot.reply_to(message, f"Код {code} успешно удален.")

    def redeem_code(self, message):
        parts = message.text.split(" ")
        code = parts[1]

        if len(parts) != 2:
            self.bot.reply_to(message, "Неверный формат команды! Используйте: /redeem <код>")
            return

        redeem_code = self.codes.get(self.CodeQuery.code == code.upper())
        if not redeem_code:
            self.bot.reply_to(message, "Промокод не найден!")
            return

        player = self.players.get(self.PlayerQuery.uid == message.from_user.id)

        if not player:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        if message.from_user.id in redeem_code["redeemed_by"]:
            self.bot.reply_to(message, "Вы уже использовали этот код!")
            return

        match redeem_code["type"]:
            case "videotape":
                quantity = int(redeem_code["reward"])
                player["channel"]["masterTapes"] += quantity
                self.players.update({"channel": player["channel"]}, self.PlayerQuery.uid == message.from_user.id)
                self.bot.reply_to(message, f"Вы успешно получили {quantity} видеокассет!")
            case "denny":
                amount = int(redeem_code["reward"])
                player["interknot"]["denny"] += amount
                self.players.update({"interknot": player["interknot"]}, self.PlayerQuery.uid == message.from_user.id)
                self.bot.reply_to(message, f"Вы успешно получили {amount} денни!")
            case "amplifier":
                amplifier_name = redeem_code["reward"]
                amplifier = self.amplifier.get(self.AmplifierQuery.name == amplifier_name)

                if not amplifier:
                    self.bot.reply_to(message, "Амплификатор из кода не найден!")
                    return

                if "owned" not in player["amplifiers"]:
                    player["amplifiers"]["owned"] = []
                player["amplifiers"]["owned"].append(amplifier_name)

                self.players.update({"amplifiers": player["amplifiers"]}, self.PlayerQuery.uid == message.from_user.id)
                self.bot.reply_to(message, f"Вы успешно получили амплификатор {amplifier_name}!")

        redeem_code["redeemed_by"].append(message.from_user.id)
        self.codes.update({"redeemed_by": redeem_code["redeemed_by"]}, self.CodeQuery.code == code.upper())
