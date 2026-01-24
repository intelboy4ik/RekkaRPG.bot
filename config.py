import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# ADMINS IDS
ADMINS_IDS = list(map(int, os.getenv("ADMINS_IDS").split(",")))

# Telegram consts
MAIN_GROUP_ID = int(os.getenv("MAIN_GROUP_ID"))
SHIYUI_THREAD_ID = int(os.getenv("SHIYUI_THREAD_ID"))
ROLEPLAY_THREAD_ID = int(os.getenv("ROLEPLAY_THREAD_ID"))
INTERNOT_UP_THREAD_ID = int(os.getenv("INTERNOT_UP_THREAD_ID"))

# Balance consts
MAX_LV = int(os.getenv("MAX_LV"))
POSTS_PER_LV = int(os.getenv("POSTS_PER_LV"))
DUEL_WINS_PER_LV = int(os.getenv("DUEL_WINS_PER_LV"))

MIN_DMG_MULTIPLIER = int(os.getenv("MIN_DMG_MULTIPLIER"))
MAX_DMG_MULTIPLIER = int(os.getenv("MAX_DMG_MULTIPLIER"))
BASE_DEFENSE = int(os.getenv("BASE_DEFENSE"))

# Equipment consts
ENGINES_POSSIBLE_STATS = list(map(str, os.getenv("ENGINES_POSSIBLE_STATS").split(",")))

# Admin check function
def is_admin(user_id):
    return user_id in ADMINS_IDS