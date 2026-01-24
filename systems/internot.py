import random

from config import MAIN_GROUP_ID, INTERNOT_UP_THREAD_ID, ROLEPLAY_THREAD_ID, POSTS_PER_LV, MAX_LV


class InternotSystem:
    def __init__(self, bot, players, playerquery, stats_system=None):
        self.bot = bot
        self.players = players
        self.PlayerQuery = playerquery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(
            func=lambda message: message.message_thread_id == ROLEPLAY_THREAD_ID
        )(self.posts_counter)

    def posts_counter(self, message):
        player_data = self.players.get(self.PlayerQuery.uid == message.from_user.id)
        if not player_data:
            return

        internot = player_data["internot"]
        internot["posts"] += 1

        # всегда сохраняем посты
        self.players.update({"internot": internot}, self.PlayerQuery.uid == player_data["uid"])

        if internot["posts"] % POSTS_PER_LV == 0:
            if self.up_internot_lv(player_data):
                self.send_congrats_message(player_data, "за активность в ролевом чате")

    def up_internot_lv(self, player_data) -> bool:
        internot = player_data["internot"]

        if internot["lv"] >= MAX_LV:
            return False

        internot["lv"] += 1
        self.players.update({"internot": internot}, self.PlayerQuery.uid == player_data["uid"])
        self._upgrade_player_stats(player_data, internot["lv"])
        return True

    def send_congrats_message(self, player_data, reason):
        self.bot.send_message(
            MAIN_GROUP_ID,
            f"Поздравляем! {player_data['username']} получил повышение уровня Интернота {reason}!🎉",
            message_thread_id=INTERNOT_UP_THREAD_ID
        )

    def _upgrade_player_stats(self, player_data, new_lv):
        if new_lv % 5 != 0:
            return

        bonuses = {
            "HP": random.randint(75, 135),
            "DEF": random.randint(25, 45),
            "ATK": random.randint(25, 45),
            "CRIT.DMG": random.randint(1, 3),
            "P.DMG": 2,
        }

        for stat, bonus in bonuses.items():
            player_data["stats"]["base"][stat] = player_data["stats"]["base"].get(stat, 0) + bonus

        self.players.update({"stats": player_data["stats"]}, self.PlayerQuery.uid == player_data["uid"])

