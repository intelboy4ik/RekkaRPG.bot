import random
import os
from dotenv import load_dotenv

load_dotenv()

ROLEPLAY_THREAD_ID = int(os.getenv("ROLEPLAY_THREAD_ID"))
INTERNOT_UP_THREAD_ID = int(os.getenv("INTERNOT_UP_THREAD_ID"))

MAX_LV = int(os.getenv("MAX_LV"))
POSTS_PER_LV = int(os.getenv("POSTS_PER_LV"))

class InternotSystem:
    def __init__(self, bot, users, user):
        self.bot = bot
        self.users = users
        self.User = user

    def register_handler(self):
        self.bot.message_handler(func=lambda message: True)(self.post_counter)

    def post_counter(self, message):
        target_id = ROLEPLAY_THREAD_ID
        if message.message_thread_id == target_id:
            user = self.users.get(self.User.user_id == message.from_user.id)
            if not user:
                return

            current_posts = user["internot"]["posts"]
            new_posts = current_posts + 1

            if new_posts < POSTS_PER_LV:
                self.users.update({"internot": {"lv": user['internot']['lv'], "posts": new_posts}}, self.User.user_id == user["user_id"])
                return
            new_lv = self.up_internot_lv(user)
            self.users.update({"internot": {"lv": new_lv, "posts": 0}}, self.User.user_id == user["user_id"])
            self.bot.send_message(
                message.chat.id,
                f"Поздравляем! {user['username']} получил повышение уровня Интернота за активность в ролевом!",
                message_thread_id=INTERNOT_UP_THREAD_ID
            )

    def up_internot_lv(self, user):
        current_lv = user["internot"]["lv"]
        if current_lv == MAX_LV:
            return

        new_lv = current_lv + 1
        self.users.update({"internot": {"lv": new_lv, "posts": 0}}, self.User.user_id == user["user_id"])

        if new_lv % 5 == 0:
            lv_hp_boost = random.randint(75, 125)
            lv_defense_boost = random.randint(15, 35)
            lv_atk_boost = random.randint(15, 50)
            lv_crit_boost = random.randint(1, 5)

            updated_chars = {
                "HP": user["chars"]["HP"] + lv_hp_boost,
                "DEF": user["chars"]["DEF"] + lv_defense_boost,
                "ATK": user["chars"]["ATK"] + lv_atk_boost,
                "CRIT.DMG": user["chars"]["CRIT.DMG"] + lv_crit_boost
            }

            self.users.update({"chars": updated_chars}, self.User.user_id == user["user_id"])

        return new_lv