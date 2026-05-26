from datetime import datetime

CAT = [
    "喵～你终于看我了！",
    "本喵不是很在乎你...才怪～",
    "喵？你在干什么呢？",
    "我需要一个纸箱。",
    "休息时间到，不要打扰本喵。",
    "喵喵喵！（翻译：给我摸头！）",
    "这里是本喵的地盘。",
    "好无聊...陪我玩嘛。",
    "我闻到了食物的味道...",
    "嗯...太阳晒得好舒服～",
    "你今天有没有想我？",
    "喵呜...抱抱我嘛～",
    "本喵决定在这里睡觉了。",
    "铲屎官，你还不快来陪我？",
]

DOG = [
    "汪汪！主人你来啦！",
    "我要出去玩！！",
    "球！球！球！扔球嘛！",
    "主人，我爱你！汪！",
    "我是最乖的狗狗！",
    "可以给我零食吗？",
    "陪我玩嘛！（尾巴摇摇）",
    "汪！有陌生人！（其实是快递员）",
    "今天能带我出去遛遛吗？",
    "我把你的拖鞋藏起来了...嘿嘿",
    "主人，抱抱！",
    "我想吃骨头！",
    "汪汪汪！（我好想你呀！）",
    "今天我超级乖的！给我奖励！",
]

GENERIC = [
    "今天也要加油哦！",
    "要好好吃饭！",
    "工作累了就休息一下～",
    "我一直在这里陪着你！",
    "记得多喝水哦～",
    "有我陪着你，不要担心！",
]

# ── 时间感知台词 ───────────────────────────────────────────────────────────────

MORNING = {
    "cat": ["喵～早上好！今天也要元气满满哦！", "早！本喵已经醒了，你呢？", "早安～记得吃早饭！"],
    "dog": ["汪汪！早上好！！今天也是美好的一天！", "主人早！快来陪我玩！", "早安！我等你好久了！"],
    "generic": ["早上好！新的一天开始了！", "早安～今天也要加油！"],
}

EVENING = {
    "cat": ["喵...今天也辛苦了～", "该休息了，本喵也累了...", "夜深了，早点睡哦～"],
    "dog": ["主人今天辛苦了！", "汪...困了...陪我一会儿嘛", "要记得早点睡觉哦！"],
    "generic": ["辛苦了，好好休息～", "夜深了，注意身体哦。"],
}

WAKEUP = {
    "cat": ["喵呜...（伸懒腰）早上好～", "唔...天亮了吗...（揉眼睛）"],
    "dog": ["汪！！天亮了！！好开心！！", "汪汪...（打哈欠）早上好～"],
    "generic": ["唔...（伸懒腰）早上好～"],
}

SLEEP_ZZZ = ["Zzz...", "Zzz～", "呼～呼～", "zzzZZZ..."]

# ── 互动台词 ──────────────────────────────────────────────────────────────────

INTERACTION = {
    ("cat",  "cat"):     ["喵？你也在这里！", "同类！", "我们一起溜达吧～"],
    ("cat",  "dog"):     ["汪...？", "...（后退一步）", "你...你好"],
    ("dog",  "cat"):     ["汪！新朋友！", "（摇尾巴）喵喵？", "一起玩嘛！"],
    ("dog",  "dog"):     ["汪汪！！", "找到同伴了！", "一起去散步吧！"],
    ("generic", "cat"):  ["你好呀！", "嗨！"],
    ("generic", "dog"):  ["你好呀！", "嗨！"],
    ("cat",  "generic"): ["喵？", "你好。"],
    ("dog",  "generic"): ["汪！你好！", "新朋友！"],
}

HOME_LINES = ["终于回来了～", "这里才是我的地盘！", "哼，不许再把我扔走！"]


def get_phrases(pet_type: str) -> list:
    return {"cat": CAT, "dog": DOG}.get(pet_type, GENERIC)


def get_time_phrase(pet_type: str, time_state: str) -> str:
    bank = {"morning": MORNING, "evening": EVENING, "wakeup": WAKEUP}.get(time_state)
    if not bank:
        return ""
    lines = bank.get(pet_type) or bank.get("generic", [""])
    return __import__("random").choice(lines)


def get_interaction_phrase(my_type: str, other_type: str) -> str:
    key = (my_type, other_type)
    lines = INTERACTION.get(key) or INTERACTION.get((my_type, "generic"), ["你好！"])
    return __import__("random").choice(lines)


def detect_type(image_file: str) -> str:
    name = image_file.lower()
    if any(k in name for k in ["cat", "猫", "kitty", "kitten", "neko"]):
        return "cat"
    if any(k in name for k in ["dog", "狗", "puppy", "汪", "woof", "pet"]):
        return "dog"
    return "generic"


def current_time_state() -> str:
    h = datetime.now().hour
    if 6 <= h < 9:   return "morning"
    if 9 <= h < 18:  return "day"
    if 18 <= h < 22: return "evening"
    return "sleeping"   # 22:00 - 6:00
