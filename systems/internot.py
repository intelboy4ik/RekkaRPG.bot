import random

from config import MAIN_GROUP_ID, INTERNOT_UP_THREAD_ID, ROLEPLAY_THREAD_ID, POSTS_PER_LV, MAX_LV


class InternotSystem:
    def __init__(self, bot, users, userquery, stats_system=None):
        self.bot = bot
        self.users = users
        self.UserQuery = userquery
        self.stats_system = stats_system

    def register_handlers(self):
        self.bot.message_handler(
            func=lambda message: message.message_thread_id == ROLEPLAY_THREAD_ID
        )(self.posts_counter)

    def posts_counter(self, message):
        user_data = self.users.get(self.UserQuery.user_id == message.from_user.id)
        if not user_data:
            return

        internot = user_data["internot"]
        internot["posts"] += 1

        # всегда сохраняем посты
        self.users.update({"internot": internot}, self.UserQuery.user_id == user_data["user_id"])

        if internot["posts"] % POSTS_PER_LV == 0:
            if self.up_internot_lv(user_data):
                self.send_congrats_message(user_data, "за активность в ролевом чате")

    def up_internot_lv(self, user_data) -> bool:
        internot = user_data["internot"]

        if internot["lv"] >= MAX_LV:
            return False

        internot["lv"] += 1
        self.users.update({"internot": internot}, self.UserQuery.user_id == user_data["user_id"])
        self._upgrade_user_stats(user_data, internot["lv"])
        return True

    def send_congrats_message(self, user_data, reason):
        self.bot.send_message(
            MAIN_GROUP_ID,
            f"Поздравляем! {user_data['username']} получил повышение уровня Интернота {reason}!🎉",
            message_thread_id=INTERNOT_UP_THREAD_ID
        )

    def _upgrade_user_stats(self, user_data, new_lv):
        if new_lv % 5 != 0:
            return

        bonuses = {
            "HP": random.randint(65, 115),
            "DEF": random.randint(15, 35),
            "ATK": random.randint(15, 35),
            "CRIT.DMG": random.randint(1, 3),
            "P.DMG": 0,
        }

        for stat, bonus in bonuses.items():
            user_data["stats"]["base"][stat] = user_data["stats"]["base"].get(stat, 0) + bonus

        self.users.update({"stats": user_data["stats"]}, self.UserQuery.user_id == user_data["user_id"])

