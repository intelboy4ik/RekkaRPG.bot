import random
import os
from dotenv import load_dotenv

load_dotenv()

from config import MAIN_GROUP_ID, INTERNOT_UP_THREAD_ID, ROLEPLAY_THREAD_ID, POSTS_PER_LV, MAX_LV

class InternotSystem:
    def __init__(self, bot, users, userquery):
        self.bot = bot
        self.users = users
        self.UserQuery = userquery

    def register_handlers(self):
        self.bot.message_handler(func=lambda message: True)(self.post_counter)

    def post_counter(self, message):
        target_id = ROLEPLAY_THREAD_ID
        if message.message_thread_id == target_id:
            user_data = self.users.get(self.UserQuery.user_id == message.from_user.id)
            if not user_data:
                return

            current_posts = user_data["internot"]["posts"]
            new_posts = current_posts + 1

            if new_posts < POSTS_PER_LV:
                self.users.update({
                    "internot":
                        {
                            "lv": user_data['internot']['lv'],
                            "posts": new_posts,
                            "duel_wins": user_data["internot"]["duel_wins"]
                        }
                },
                    self.UserQuery.user_id == user_data["user_id"]
                )
                return
            new_lv = self.up_internot_lv(user_data)
            self.users.update({
                "internot":
                    {
                        "lv": new_lv,
                        "posts": 0,
                        "duel_wins": user_data["internot"]["duel_wins"]
                    }
            },
                self.UserQuery.user_id == user_data["user_id"])
            self.send_congrats_message(user_data, "за активность в рп чате")

    def up_internot_lv(self, user_data):
        current_lv = user_data["internot"]["lv"]
        if current_lv == MAX_LV:
            return

        new_lv = current_lv + 1
        self.users.update(
            {
                "internot":
                    {
                        "lv": new_lv,
                        "posts": 0,
                        "duel_wins": user_data["internot"]["duel_wins"]
                    }
            },
            self.UserQuery.user_id == user_data["user_id"])

        self._upgrade_user_chars(user_data, new_lv)

        return new_lv

    def send_congrats_message(self, user_data, reason):
        self.bot.send_message(
            MAIN_GROUP_ID,
            f"Поздравляем! {user_data['username']} получил повышение уровня Интернота {reason}!🎉",
            message_thread_id=INTERNOT_UP_THREAD_ID
        )

    def _upgrade_user_chars(self, user_data, new_lv):
        if new_lv % 5 == 0:
            lv_hp_boost = random.randint(75, 125)
            lv_defense_boost = random.randint(15, 35)
            lv_atk_boost = random.randint(15, 50)
            lv_crit_boost = random.randint(1, 5)

            updated_chars = {
                "HP": user_data["chars"]["HP"] + lv_hp_boost,
                "DEF": user_data["chars"]["DEF"] + lv_defense_boost,
                "ATK": user_data["chars"]["ATK"] + lv_atk_boost,
                "CRIT.DMG": user_data["chars"]["CRIT.DMG"] + lv_crit_boost
            }

            self.users.update({"chars": updated_chars}, self.UserQuery.user_id == user_data["user_id"])
