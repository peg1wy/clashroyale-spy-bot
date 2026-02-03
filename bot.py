import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
import os

TOKEN = os.environ["TOKEN"]

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ================= НАСТРОЙКИ =================
DEFAULT_MAX_ROUNDS = 3
DEFAULT_TURN_TIME = 60

games = {}  # chat_id -> game_data
spy_stats = {}  # user_id -> {"spy_count","caught_count","escaped_count"}

characters = ["Хог",
    "Огненная лучница",
    "Арбалет",
    "Землетрясение",
    "Тесла",
    "Валька",
    "Бревно",
    "Ледышка",
    "Огненный дух",
    "Гоблинская бочка",
    "Маленький принц",
    "Шар",
    "Банда гоблинов",
    "ПЕККА",
    "Летучка",
    "Принцесса",
    "Лучницы",
    "Боевой таран",
    "Бандитка",
    "Гоблин-гигант",
    "Целительница-воин",
    "Шустрый шахтер",
    "Золотой рыцарь",
    "Гоблинштейн",
    "Гоблины-копейщики",
    "Гигантский снежок",
    "Колдун",
    "Мортира",
    "Гоблинский бур",
    "Дротист",
    "Миньоны",
    "Хижина гоблинов",
    "Стражи",
    "Рыцарь",
    "Гигант",
    "Летучие мыши",
    "Бочка со скелетами",
    "Гигантский скелет",
    "Стрелы",
    "Принц",
    "Варварская бочка",
    "Король скелетов",
    "Стенобои",
    "Подрывник",
    "Королевские рекруты",
    "Электрогигант",
    "Повозка с пушкой",
    "Ночная ведьма",
    "Мини ПЕККА",
    "Мушкетер",
    "Королевская почта",
    "Ракета",
    "Эликсирный голем",
    "Разбойники",
    "Ведьма",
    "Пушка",
    "Главная бандитка",
    "Монах",
    "Королева лучниц",
    "Мегарыцарь",
    "Электродракон",
    "Сборщик эликсира",
    "Орда миньонов",
    "Зап",
    "Электрический дух",
    "Надгробие",
    "Зеркало",
    "Три мушкетера",
    "Адская башня",
    "Охотник",
    "Элитные варвары",
    "Гоблинская машина",
    "Заморозка",
    "Королевский гигант",
    "Торнадо",
    "Мегаминьон",
    "Молния",
    "Темный принц",
    "Клон",
    "Варвары",
    "Башня-бомбежка",
    "Проклятие гоблинов",
    "Дух исцеления",
    "Спарки",
    "Дровосек",
    "Мини-генераторы",
    "Хижина варваров",
    "Костяные драконы",
    "Огненный шар",
    "Голем",
    "Королевские кабаны",
    "Берсеркша",
    "Клетка с гоблином",
    "Гоблины",
    "Пламенный дракон",
    "Рыбак",
    "Палач",
    "Армия скелетов",
    "Печь",
    "Яд",
    "Дракончик",
    "Вышибала",
    "Магический лучник",
    "Громовержец",
    "Королевский призрак",
    "Ледяной колдун",
    "Шахтер",
    "Ярость",
    "Руническая гигантша",
    "Подозрительный куст",
    "Гоблин-подрывник",
    "Бездна",
    "Адская гонча",
    "Всадница на буйлуке",
    "Ведьмина бабушка",
    "Кладба",
    "Феникс",
    "Императрица духов",
    "Лоза",
    "Скелеты",
    "Ледяной голем"]
SPECIAL_ROLES = ["Аналитик", "Телохранитель", "Актёр"]  # новый режим

# ================= КНОПКИ =================
def main_keyboard(game=None):
    # Добавляем кнопку включения/выключения режима с ролями
    special_mode_text = "🧩 Режим с ролями: ВКЛ" if game and game.get("special_roles_enabled") else "🧩 Режим с ролями: ВЫКЛ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Создать игру", callback_data="newgame")],
        [InlineKeyboardButton(text="➕ Войти", callback_data="join")],
        [InlineKeyboardButton(text="▶️ Начать", callback_data="start")],
        [InlineKeyboardButton(text="⚙ Настройки раундов", callback_data="round_settings")],
        [InlineKeyboardButton(text="📊 Статистика группы", callback_data="show_stats")],
        [InlineKeyboardButton(text=special_mode_text, callback_data="toggle_special_mode")]
    ])

def turn_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить ход (голос)", callback_data="vote_skip")]
    ])

def vote_keyboard(players):
    kb = []
    for uid, name in players.items():
        kb.append([InlineKeyboardButton(text=f"🗳 {name}", callback_data=f"vote_{uid}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def round_settings_keyboard(game):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"⏱ Время хода: {game['turn_time']} +", callback_data="inc_time"),
            InlineKeyboardButton(text=f"⏱ Время хода: {game['turn_time']} -", callback_data="dec_time")
        ],
        [
            InlineKeyboardButton(text=f"🔄 Раундов: {game['max_rounds']} +", callback_data="inc_rounds"),
            InlineKeyboardButton(text=f"🔄 Раундов: {game['max_rounds']} -", callback_data="dec_rounds")
        ],
        [
            InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")
        ]
    ])

def roles_keyboard(uid, role_used):
    if role_used.get(uid):
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Использовать способность", callback_data=f"use_role_{uid}")]
    ])

# ================= СТАРТ =================
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if message.chat.type == "private":
        await message.answer("❌ Бот работает только в группе")
        return
    await message.answer(
        "🎭 <b>Шпион | Clash Royale</b>\n3–6 игроков\n\nСоздай игру 👇",
        reply_markup=main_keyboard()
    )

# ================= CALLBACK =================
@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    uid = call.from_user.id
    name = call.from_user.first_name
    data = call.data

    game = games.get(chat_id)

    # =================== ИГРА ===================
    if data == "newgame":
        games[chat_id] = {
            "players": {}, "scores": {}, "round": 0,
            "last_spy": None, "current_spy": None,
            "current_card": None, "order": [], "current_index": 0,
            "votes": {}, "timer_task": None,
            "turn_time": DEFAULT_TURN_TIME, "max_rounds": DEFAULT_MAX_ROUNDS,
            "skip_votes": set(),
            "special_roles_enabled": False,
            "roles": {}, "roles_used": {}
        }
        await call.message.edit_text("🟢 Игра создана! Жмите «Войти»", reply_markup=main_keyboard(games[chat_id]))
        await call.answer()

    elif data == "join":
        if not game:
            await call.answer("Сначала создай игру", show_alert=True)
            return
        if uid in game["players"]:
            await call.answer("Ты уже в игре", show_alert=True)
            return
        if len(game["players"]) >= 6:
            await call.answer("Максимум 6 игроков", show_alert=True)
            return
        game["players"][uid] = name
        game["scores"][uid] = 0
        await call.message.edit_text(f"✅ {name} вошёл ({len(game['players'])}/6)", reply_markup=main_keyboard(game))
        await call.answer()

    elif data == "start":
        if not game or len(game["players"]) < 3:
            await call.answer("Нужно минимум 3 игрока", show_alert=True)
            return
        await call.answer()
        await start_round(chat_id)

    elif data == "vote_skip":
        if not game:
            return
        game["skip_votes"].add(uid)
        if len(game["skip_votes"]) > len(game["players"]) // 2:
            if game["timer_task"]:
                game["timer_task"].cancel()
            game["current_index"] += 1
            await next_turn(chat_id)
        await call.answer(f"Голос за пропуск засчитан ({len(game['skip_votes'])}/{len(game['players'])})")

    elif data.startswith("vote_"):
        if not game:
            return
        target = int(data.split("_")[1])
        game["votes"][uid] = target
        await call.answer("Голос принят ✅")
        if len(game["votes"]) == len(game["players"]):
            await tally_votes(chat_id)

    elif data == "show_stats":
        await call.answer()
        await show_stats(chat_id)

    elif data == "round_settings":
        if not game:
            await call.answer("Сначала создай игру", show_alert=True)
            return
        await call.message.edit_text("⚙ Настройки раундов:", reply_markup=round_settings_keyboard(game))
        await call.answer()
    
    elif data == "back_to_main":
        if not game:
            await call.answer("Сначала создай игру", show_alert=True)
            return
        await call.message.edit_text(
            "🎭 <b>Шпион | Clash Royale</b>\n3–6 игроков\n\nСоздай игру 👇",
            reply_markup=main_keyboard()
        )
        await call.answer()

    elif data in ["inc_time","dec_time","inc_rounds","dec_rounds"]:
        if not game:
            return
        if data == "inc_time":
            game["turn_time"] += 5
        elif data == "dec_time":
            game["turn_time"] = max(5, game["turn_time"] - 5)
        elif data == "inc_rounds":
            game["max_rounds"] += 1
        elif data == "dec_rounds":
            game["max_rounds"] = max(1, game["max_rounds"] - 1)
        await call.message.edit_reply_markup(reply_markup=round_settings_keyboard(game))
        await call.answer()

    elif data == "toggle_special_mode":
        if not game:
            await call.answer("Сначала создай игру", show_alert=True)
            return
        game["special_roles_enabled"] = not game.get("special_roles_enabled", False)
        await call.message.edit_reply_markup(reply_markup=main_keyboard(game))
        await call.answer(f"Режим с ролями {'включён' if game['special_roles_enabled'] else 'выключен'}!")

    elif data.startswith("use_role_"):
        target_uid = int(data.split("_")[2])
        if game["roles_used"].get(target_uid):
            await call.answer("Способность уже использована", show_alert=True)
            return
        game["roles_used"][target_uid] = True
        role = game["roles"].get(target_uid)
        await call.answer(f"✅ Использована способность роли: {role}")

# ================= РАУНД =================
async def start_round(chat_id):
    game = games[chat_id]
    game["round"] += 1
    game["votes"] = {}
    game["skip_votes"] = set()
    players_ids = list(game["players"].keys())

    possible = players_ids[:]
    if game["last_spy"] in possible and len(players_ids) >= 4:
        possible.remove(game["last_spy"])
    spy = random.choice(possible)
    game["current_spy"] = spy
    game["last_spy"] = spy
    game["current_card"] = random.choice(characters)

    order = players_ids[:]
    random.shuffle(order)
    game["order"] = order
    game["current_index"] = 0

    if game.get("special_roles_enabled"):
        available_roles = SPECIAL_ROLES[:]
        random.shuffle(available_roles)
        for uid in players_ids:
            game["roles"][uid] = available_roles.pop() if available_roles else None
            game["roles_used"][uid] = False

    for uid in players_ids:
        role_text = f"\n🎭 Твоя роль: <b>{game['roles'].get(uid)}</b>" if game.get("special_roles_enabled") else ""
        if uid == spy:
            await bot.send_message(uid, f"🕵️ Ты <b>ШПИОН</b>\nСлушай и не пались{role_text}", reply_markup=roles_keyboard(uid, game["roles_used"]))
        else:
            await bot.send_message(uid, f"🟢 Ты не шпион\n<b>{game['current_card']}</b>{role_text}", reply_markup=roles_keyboard(uid, game["roles_used"]))

    await bot.send_message(chat_id, f"🔄 <b>Раунд {game['round']} / {game['max_rounds']}</b>\nНачинаем!")
    await next_turn(chat_id)

# ================= ХОД =================
async def next_turn(chat_id):
    game = games.get(chat_id)
    if not game:
        return
    if game["timer_task"]:
        game["timer_task"].cancel()

    if game["current_index"] >= len(game["order"]):
        await bot.send_message(chat_id, "🗳 Все походили! Голосуем")
        await start_vote(chat_id)
        return

    uid = game["order"][game["current_index"]]
    name = game["players"][uid]
    await bot.send_message(chat_id, f"🎤 Ходит: <b>{name}</b> ({game['turn_time']} сек)", reply_markup=turn_keyboard())
    game["timer_task"] = asyncio.create_task(turn_timer(chat_id))

async def turn_timer(chat_id):
    game = games.get(chat_id)
    if not game:
        return
    try:
        await asyncio.sleep(game["turn_time"])
    except asyncio.CancelledError:
        return
    game["current_index"] += 1
    await next_turn(chat_id)

# ================= ГОЛОСОВАНИЕ =================
async def start_vote(chat_id):
    game = games[chat_id]
    await bot.send_message(chat_id, "🗳 <b>Кто шпион?</b>", reply_markup=vote_keyboard(game["players"]))

async def tally_votes(chat_id):
    game = games[chat_id]
    votes = game["votes"]
    spy = game["current_spy"]
    count = {}
    for v in votes.values():
        if v is None:
            continue
        count[v] = count.get(v, 0) + 1
    max_votes = max(count.values()) if count else 0
    suspects = [uid for uid, c in count.items() if c == max_votes]

    text = "📊 <b>Результаты:</b>\n"
    if spy in suspects:
        text += f"✅ Шпион пойман: <b>{game['players'][spy]}</b>\n"
        for uid in game["players"]:
            if uid != spy:
                game["scores"][uid] += 1
        spy_stats.setdefault(spy, {"spy_count":0,"caught_count":0,"escaped_count":0})
        spy_stats[spy]["caught_count"] += 1
    else:
        text += f"❌ Шпион ушёл: <b>{game['players'][spy]}</b>\n"
        game["scores"][spy] += 2
        spy_stats.setdefault(spy, {"spy_count":0,"caught_count":0,"escaped_count":0})
        spy_stats[spy]["escaped_count"] += 1

    text += f"\n💡 Карта: <b>{game['current_card']}</b>\n"
    await bot.send_message(chat_id, text)

    if game["round"] < game["max_rounds"]:
        await start_round(chat_id)
    else:
        await finish_game(chat_id)

# ================= ФИНИШ =================
async def finish_game(chat_id):
    game = games[chat_id]
    text = "🏆 <b>Игра окончена!</b>\n\n"
    for uid, score in sorted(game["scores"].items(), key=lambda x: -x[1]):
        text += f"{game['players'][uid]} — {score} очков\n"
    await bot.send_message(chat_id, text)
    del games[chat_id]

# ================= СТАТИСТИКА =================
async def show_stats(chat_id):
    text = "<b>📊 Статистика участников группы:</b>\n"
    game_members = []
    try:
        members = await bot.get_chat_administrators(chat_id)
        for m in members:
            if not m.user.is_bot:
                game_members.append(m.user)
    except:
        pass

    all_ids = set()
    for game in games.values():
        all_ids.update(game["players"].keys())
    for uid in all_ids:
        if uid in spy_stats:
            s = spy_stats[uid]
        else:
            s = {"spy_count":0,"caught_count":0,"escaped_count":0}
        name = games[chat_id]["players"].get(uid, f"ID {uid}")
        text += f"{name} — 🕵️ {s['spy_count']}, ✅ {s['caught_count']}, ❌ {s['escaped_count']}\n"

    await bot.send_message(chat_id, text)

# ================= ОБРАБОТКА СООБЩЕНИЙ =================
@dp.message()
async def handle_player_messages(message: types.Message):
    chat_id = message.chat.id
    uid = message.from_user.id
    game = games.get(chat_id)
    if not game:
        return

    if game["current_index"] < len(game["order"]):
        current_uid = game["order"][game["current_index"]]
        if uid == current_uid:
            if game["timer_task"]:
                game["timer_task"].cancel()
            await message.reply(f"✅ {message.from_user.first_name} сделал ход!")
            game["current_index"] += 1
            await next_turn(chat_id)
            return

# ================= ЗАПУСК =================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())