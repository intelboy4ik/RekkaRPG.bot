import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# ADMINS IDS
ADMINS_IDS = list(map(int, os.getenv("ADMINS_IDS").split(",")))

# Telegram consts
MAIN_GROUP_ID = int(os.getenv("MAIN_GROUP_ID"))
MAIN_THREAD_ID = int(os.getenv("MAIN_THREAD_ID"))
DUEL_THREAD_ID = int(os.getenv("DUEL_THREAD_ID"))
ROLEPLAY_THREAD_ID = int(os.getenv("ROLEPLAY_THREAD_ID"))
LV_UP_THREAD_ID = int(os.getenv("LV_UP_THREAD_ID"))

# Balance consts
MAX_LV = int(os.getenv("MAX_LV"))
POSTS_PER_LV = int(os.getenv("POSTS_PER_LV"))
DUEL_WINS_PER_LV = int(os.getenv("DUEL_WINS_PER_LV"))

MIN_DMG_MULTIPLIER = int(os.getenv("MIN_DMG_MULTIPLIER"))
MAX_DMG_MULTIPLIER = int(os.getenv("MAX_DMG_MULTIPLIER"))
MIN_SHOCK_MULTIPLIER = int(os.getenv("MIN_SHOCK_MULTIPLIER"))
MAX_SHOCK_MULTIPLIER = int(os.getenv("MAX_SHOCK_MULTIPLIER"))
BASE_DUEL_DEFENSE = int(os.getenv("BASE_DUEL_DEFENSE"))

MIN_HP_PULL = int(os.getenv("MIN_HP_PULL"))
MAX_HP_PULL = int(os.getenv("MAX_HP_PULL"))
MIN_DEF_PULL = int(os.getenv("MIN_DEF_PULL"))
MAX_DEF_PULL = int(os.getenv("MAX_DEF_PULL"))
MIN_ATK_PULL = int(os.getenv("MIN_ATK_PULL"))
MAX_ATK_PULL = int(os.getenv("MAX_ATK_PULL"))
MIN_CRIT_DMG_PULL = int(os.getenv("MIN_CRIT_DMG_PULL"))
MAX_CRIT_DMG_PULL = int(os.getenv("MAX_CRIT_DMG_PULL"))

BASE_HP = int(os.getenv("BASE_HP"))
BASE_DEF = int(os.getenv("BASE_DEF"))
BASE_ATK = int(os.getenv("BASE_ATK"))
BASE_CRIT_DMG = int(os.getenv("BASE_CRIT_DMG"))

# Equipment consts
AMPLIFIER_POSSIBLE_STATS = list(map(str, os.getenv("AMPLIFIER_POSSIBLE_STATS").split(",")))

# Admin check function
def is_admin(user_id):
    return user_id in ADMINS_IDS