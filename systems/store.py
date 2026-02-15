import random

from telebot import types

from config import GACHA_CURRENCY_NAME


class StoreSystem:
    def __init__(self, bot, players, playerquery, weapons, weaponquery, weapon_system):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.weapons = weapons
        self.WeaponQuery = weaponquery
        self.weapon_system = weapon_system

    def register_handlers(self):
        self.bot.message_handler(commands=["store"])(self.open_store)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("buy_weapon_"))(
            self.buy_weapon_callback)
        self.bot.callback_query_handler(func=lambda call: call.data in [f"buy_{GACHA_CURRENCY_NAME}_1", f"buy_{GACHA_CURRENCY_NAME}_10"])(
            self.buy_videotape_callback)

    def open_store(self, message):
        weapons = self.weapons.search(self.WeaponQuery.cost > 0)
        markup = types.InlineKeyboardMarkup()
        for weapon in weapons:
            button = types.InlineKeyboardButton(
                text=f"{weapon['name']}",
                callback_data=f"buy_weapon_{weapon.doc_id}"
            )
            markup.add(button)

        one_pull_button = types.InlineKeyboardButton(
            text="📼 1 кассета",
            callback_data=f"buy_{GACHA_CURRENCY_NAME}_1"
        )
        ten_pull_button = types.InlineKeyboardButton(
            text="📼 10 кассет",
            callback_data=f"buy_{GACHA_CURRENCY_NAME}_10"
        )
        markup.row(one_pull_button, ten_pull_button)

        weapon_list = "\n\n".join([
            f"*{weapon['name']}*"
            f"\n"
            f"{self.weapon_system.format_weapon_stats(weapon["name"])}"
            f"\n"
            f"💰 Цена: {weapon['cost']}"
            for weapon in weapons
        ])

        random_phrase = random.choice(["Впервые в продаже!", "Специальное предложение!", "Только сегодня!", "Не пропустите!"])

        self.bot.send_message(
            message.chat.id,
            f"_🛍️ Магазин амплификаторов_\n\n{weapon_list}"
            f"\n\n"
            f"_📺 {random_phrase} Видеокассеты для дешифровки!_"
            f"\n\n"
            f"1 кассета — 360 денни, 10 кассет — 3600 денни...",
            reply_markup=markup,
            message_thread_id=message.message_thread_id,
            parse_mode="Markdown"
        )

    def buy_weapon_callback(self, call):
        amp_id = call.data.split("_")[2]

        weapon = self.weapons.get(doc_id=amp_id)
        weapon_name = weapon["name"]

        player = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        if not player:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        if player["progression"]["money"] < weapon["cost"]:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно денни для покупки этого амплификатора.",
                show_alert=True
            )
            return

        player["progression"]["money"] -= weapon["cost"]
        if "owned" not in player["weapons"]:
            player["weapons"]["owned"] = []
        player["weapons"]["owned"].append(weapon_name)

        self.players.update({
            "progression": player["progression"],
            "weapons": player["weapons"]
        }, self.PlayerQuery.uid == call.from_user.id)

        self.bot.answer_callback_query(call.id, f"Вы успешно купили амплификатор {weapon_name}!", show_alert=True)

    def buy_videotape_callback(self, call):
        quantity = 1 if call.data == f"buy_{GACHA_CURRENCY_NAME}_1" else 10
        cost = 360 * quantity

        player = self.players.get(self.PlayerQuery.uid == call.from_user.id)

        if not player:
            self.bot.answer_callback_query(
                call.id,
                "У вас нет профиля! Создайте его с помощью команды /createprofile",
                show_alert=True
            )
            return

        if player["progression"]["money"] < cost:
            self.bot.answer_callback_query(
                call.id,
                "У вас недостаточно денни для покупки видеокассет.",
                show_alert=True
            )
            return

        player["progression"]["money"] -= cost
        player["gacha"][GACHA_CURRENCY_NAME] += quantity

        self.players.update({
            "progression": player["progression"],
            "gacha": player["gacha"]
        }, self.PlayerQuery.uid == call.from_user.id)

        self.bot.answer_callback_query(
            call.id,
            f"Вы успешно купили {quantity} видеокассету(ы)!",
            show_alert=True
        )