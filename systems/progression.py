import random
from datetime import date

from config import MAIN_GROUP_ID, INTERNOT_UP_THREAD_ID, ROLEPLAY_THREAD_ID, POSTS_PER_LV, MAX_LV, INTERNOT_THREAD_ID


class ProgressionSystem:
    def __init__(self, bot, players, playerquery, stats_system=None):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(
            func=lambda message: message.message_thread_id == ROLEPLAY_THREAD_ID
        )(self.posts_counter)
        self.bot.message_handler(commands=['daily'])(self.daily_reward)

    def posts_counter(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            return

        progression = player_data["progression"]
        progression["posts"] += 1

        # всегда сохраняем посты
        self.players.update({"progression": progression}, self.PlayerQuery.uid == player_data["uid"])

        if progression["posts"] % POSTS_PER_LV == 0:
            if self.up_progression_lv(player_data):
                self.send_congrats_message(player_data, "за активность в ролевом чате")

    def daily_reward(self, message):
        if message.message_thread_id != INTERNOT_THREAD_ID:
            self.bot.reply_to(message, "Эту команду можно использовать только в чате Интернота.")
            return

        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            self.bot.reply_to(message, "У вас нет профиля! Создайте его с помощью команды /createprofile")
            return

        today = date.today().isoformat()
        last_daily = player_data["progression"].get("last_daily")

        if last_daily == today:
            self.bot.reply_to(message, "Вы уже получили ежедневную награду сегодня! Приходите завтра.")
            return

        denny_bonus = random.randint(120, 600)
        player_data["progression"]["denny"] += denny_bonus
        player_data["progression"]["last_daily"] = today

        self.players.update({"progression": player_data["progression"]}, self.PlayerQuery.uid == player_data["uid"])
        self.bot.reply_to(message, f"Небольшая награда за ежедневную отметку в чате Интернота!\n\n💰{denny_bonus} денни")

    def up_progression_lv(self, player_data) -> bool:
        progression = player_data["progression"]

        if progression["lv"] >= MAX_LV:
            return False

        progression["lv"] += 1
        self.players.update({"progression": progression}, self.PlayerQuery.uid == player_data["uid"])
        self.stats_system.give_point_to_player(player_data, progression["lv"])
        return True

    def send_congrats_message(self, player_data, reason):
        self.bot.send_message(
            MAIN_GROUP_ID,
            f"Поздравляем! Уровень Интернота {player_data['username']} повышен {reason}!🎉",
            message_thread_id=INTERNOT_UP_THREAD_ID
        )
