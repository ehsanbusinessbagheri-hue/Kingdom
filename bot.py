# ==============================
# bot.py - ربات اصلی با هوش مصنوعی DeepSeek
# ==============================
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import json
import random
from datetime import datetime
import logging
import requests

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# دریافت توکن از متغیرهای محیطی (تغییر امنیتی مهم)
TOKEN = os.environ.get('TOKEN', '8073552841:AAFgBCNYM13V4MpSKUIxz_1Wt2RjBHVC8dg')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 854255491))
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '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')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@kingdarkdom')

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# وضعیت بازی
game_state = {
    "status": "waiting",
    "current_turn": 0,
    "max_turns": 50,
    "players": {},
    "illuminati_offers": [],
    "current_praetor": None,
    "game_history": []
}

# تمدن‌های بازی
CIVILIZATIONS = {
    "Rome": "Legion's Steel: +20% Defense for all infantry units",
    "Germany": "Savage Onslaught: +30% Damage when attacking NPC monsters",
    "Britain": "Longbow Volley: +25% Attack Range for all archer units",
    "China": "Ancient Wisdom: -15% Research Time for all technologies",
    "Arabia": "Desert Navigation: +20% Movement Speed for all units",
    "Korea": "Mountain Defense: +25% Defense when fighting in mountainous regions",
    "Ottomans": "Royal Artillery: +15% Damage for all siege weapons",
    "Vikings": "Viking Raid: +30% Attack Power when assaulting coastal cities"
}

# منابع اولیه
STARTING_RESOURCES = {
    "food": 1000,
    "wood": 800,
    "stone": 600,
    "gold": 400,
    "power_score": 0
}

def ask_deepseek(prompt):
    """ارسال درخواست به هوش مصنوعی DeepSeek"""
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are the Game Master for 'Dark Kingdom: Shadows of the Illuminati'. You manage the game world, narrate the story, and respond to player actions. You must follow instructions from the Human God (admin) exactly."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return "⚠️ خطا در ارتباط با هوش مصنوعی. لطفاً دوباره تلاش کنید."

def save_game_state():
    """ذخیره وضعیت بازی در کانال"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_str = json.dumps(game_state, indent=2, ensure_ascii=False)
        
        # فقط آخرین ۵۰۰۰ کاراکتر را ذخیره کن (محدودیت تلگرام)
        if len(state_str) > 4000:
            state_str = state_str[:4000] + "\n... (truncated)"
            
        bot.send_message(CHANNEL_ID, f"🔄 وضعیت بازی - {timestamp}\n{state_str}")
    except Exception as e:
        logger.error(f"Error saving game state: {e}")

def start_game(update: Update, context: CallbackContext):
    """شروع بازی جدید"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ فقط ادمین می‌تواند بازی را شروع کند!")
        return
    
    game_state.update({
        "status": "active",
        "current_turn": 1,
        "players": {},
        "illuminati_offers": [],
        "current_praetor": None,
        "game_history": []
    })
    
    # استفاده از هوش مصنوعی برای روایت شروع بازی
    prompt = """Create an epic opening narration for "Dark Kingdom: Shadows of the Illuminati" game. 
    The old world crumbled in fire and shadow. From its ashes, new Lords have risen. 
    But a hidden hand guides fate from the depths - the Illuminati. 
    Write a compelling 3-4 paragraph introduction in Persian."""
    
    opening_narration = ask_deepseek(prompt)
    
    update.message.reply_text(
        f"🎮 بازی Dark Kingdom شروع شد!\n\n"
        f"📜 داستان:\n{opening_narration}\n\n"
        f"دستور /join برای پیوستن به بازی"
    )
    save_game_state()

def join_game(update: Update, context: CallbackContext):
    """پیوستن به بازی"""
    if game_state["status"] != "active":
        update.message.reply_text("⚠️ بازی فعال نیست. منتظر شروع بازی باشید.")
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if user_id in game_state["players"]:
        update.message.reply_text("✅ شما قبلاً در بازی عضو شده‌اید!")
        return
    
    if len(context.args) < 1:
        # نمایش لیست تمدن‌ها
        keyboard = []
        for civ in CIVILIZATIONS:
            keyboard.append([InlineKeyboardButton(civ, callback_data=f"join_{civ}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "🏛️ انتخاب تمدن:\n\n" +
            "\n".join([f"• {civ}: {desc}" for civ, desc in CIVILIZATIONS.items()]),
            reply_markup=reply_markup
        )
        return
    
    civilization = context.args[0]
    if civilization not in CIVILIZATIONS:
        update.message.reply_text("❌ تمدن نامعتبر! از بین گزینه‌های زیر انتخاب کنید:\n" + 
                                 ", ".join(CIVILIZATIONS.keys()))
        return
    
    # افزودن بازیکن
    game_state["players"][user_id] = {
        "username": username,
        "civilization": civilization,
        "resources": STARTING_RESOURCES.copy(),
        "actions_remaining": 3,
        "location": random.choice(["North", "South", "East", "West"]),
        "power_score": 0
    }
    
    # استفاده از هوش مصنوعی برای خوش‌آمدگویی
    prompt = f"""Player {username} has joined the game as {civilization} civilization. 
    Their starting location is {game_state['players'][user_id]['location']}. 
    Create a welcome message in Persian that describes their arrival in the game world."""
    
    welcome_message = ask_deepseek(prompt)
    
    update.message.reply_text(welcome_message)
    save_game_state()

def handle_admin_command(update: Update, context: CallbackContext):
    """پردازش دستورات ادمین"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ فقط ادمین می‌تواند از این دستور استفاده کند!")
        return
    
    command = update.message.text
    prompt = f"""
    As the Game Master, you received this command from the Human God (admin): "{command}"
    Current game state: {json.dumps(game_state, ensure_ascii=False)}
    
    Respond to this command and execute any game changes as instructed.
    Provide your response in Persian.
    """
    
    ai_response = ask_deepseek(prompt)
    update.message.reply_text(ai_response)
    
    # ذخیره پاسخ در تاریخچه بازی
    game_state["game_history"].append({
        "type": "admin_command",
        "command": command,
        "response": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    save_game_state()

def handle_illuminati(update: Update, context: CallbackContext):
    """مدیریت دستورات Illuminati"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text.startswith("Ave Imperator"):
        offer = text.replace("Ave Imperator", "").strip()
        
        if not offer:
            update.message.reply_text("❌ پس از Ave Imperator باید یک پیشنهاد وارد کنید!")
            return
        
        game_state["current_praetor"] = user_id
        game_state["illuminati_offers"].append({
            "praetor": user_id,
            "offer": offer,
            "timestamp": datetime.now().isoformat()
        })
        
        # استفاده از هوش مصنوعی برای پاسخ به پیشنهاد Illuminati
        prompt = f"""
        Player {update.effective_user.first_name} has become the Praetor with the offer: "{offer}"
        Current game state: {json.dumps(game_state, ensure_ascii=False)}
        
        Respond to this Illuminati offer in character as the Game Master.
        Provide your response in Persian.
        """
        
        ai_response = ask_deepseek(prompt)
        update.message.reply_text(ai_response)
        
        # ذخیره در تاریخچه
        game_state["game_history"].append({
            "type": "illuminati_offer",
            "praetor": user_id,
            "offer": offer,
            "response": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        save_game_state()

def next_turn(update: Update, context: CallbackContext):
    """حرکت به نوبت بعدی"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ فقط ادمین می‌تواند نوبت را تغییر دهد!")
        return
    
    if game_state["status"] != "active":
        update.message.reply_text("⚠️ بازی فعال نیست!")
        return
    
    game_state["current_turn"] += 1
    
    # بازسازی actions برای همه بازیکنان
    for player_id in game_state["players"]:
        game_state["players"][player_id]["actions_remaining"] = 3
    
    # استفاده از هوش مصنوعی برای توصیف نوبت جدید
    prompt = f"""
    Advance the game to turn {game_state['current_turn']}. 
    Current game state: {json.dumps(game_state, ensure_ascii=False)}
    
    Describe what happens in this new turn, any random events, and the overall situation.
    Provide your response in Persian as the Game Master.
    """
    
    ai_response = ask_deepseek(prompt)
    update.message.reply_text(ai_response)
    
    # ذخیره در تاریخچه
    game_state["game_history"].append({
        "type": "turn_advance",
        "turn": game_state["current_turn"],
        "description": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    save_game_state()

def main():
    """تابع اصلی"""
    global bot
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    bot = updater.bot
    
    # handlers
    dp.add_handler(CommandHandler("start_game", start_game))
    dp.add_handler(CommandHandler("join", join_game))
    dp.add_handler(CommandHandler("next_turn", next_turn))
    dp.add_handler(CommandHandler("admin", handle_admin_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_illuminati))
    
    print("🤖 ربات Dark Kingdom با هوش مصنوعی DeepSeek فعال شد!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()