import os
import json
import asyncio
from datetime import datetime
import time

import telebot
from telethon import TelegramClient, functions

# ====================== إعدادات البوت ======================
BOT_TOKEN ="8425268390:AAEnWKfhl_RKGFVLgB9-rn90fJOnpLCCGjw"  # ضع توكن البوت
OWNER_ID = 7391486173             # ايديك كمطور
DEV_NAME = "FaDi مطور البوت"
DEV_USER = "@F_7_Qi"             # يوزر المطور الحقيقي
API_ID = 29851140      # ضع api_id هنا
API_HASH = "fb5712881689d5fb2f7efdc5f89c7091"  # ضع api_hash هنا

CHANNEL_INTERVAL = 25*60  # كل 25 دقيقة
MESSAGES_PER_CHANNEL = 7

# ====================== إنشاء الملفات والمجلدات ======================
os.makedirs("sessions", exist_ok=True)
if not os.path.exists("users.json"):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)
if not os.path.exists("codes.json"):
    default_codes = {"CODES":[{"code":"VIP123","used":False},{"code":"VIP456","used":False},{"code":"VIP789","used":False}]}
    with open("codes.json","w",encoding="utf-8") as f:
        json.dump(default_codes,f,ensure_ascii=False, indent=4)

active_clients = {}

# ====================== دوال تحميل وحفظ ======================
def load_users():
    with open("users.json","r",encoding="utf-8") as f:
        return json.load(f)
def save_users(users):
    with open("users.json","w",encoding="utf-8") as f:
        json.dump(users,f,ensure_ascii=False,indent=4)
def load_codes():
    with open("codes.json","r",encoding="utf-8") as f:
        return json.load(f)
def save_codes(codes):
    with open("codes.json","w",encoding="utf-8") as f:
        json.dump(codes,f,ensure_ascii=False,indent=4)

# ====================== Telebot ======================
bot = telebot.TeleBot(BOT_TOKEN)

def account_menu():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("🆔 ID HASH", callback_data="add_id"))
    kb.add(telebot.types.InlineKeyboardButton("🌐 IP HASH", callback_data="add_ip"))
    kb.add(telebot.types.InlineKeyboardButton("📂 أرسل ملف السيزون", callback_data="add_session"))
    kb.add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
    return kb

def main_menu():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("🔐 ضع حسابك", callback_data="account"))
    kb.add(telebot.types.InlineKeyboardButton("🚀 بدء التشغيل", callback_data="start_bot"))
    kb.add(telebot.types.InlineKeyboardButton("⏹ إيقاف التشغيل", callback_data="stop_bot"))
    kb.add(telebot.types.InlineKeyboardButton("📊 حالتي", callback_data="status"))
    return kb

# ====================== /start ======================
@bot.message_handler(commands=["start"])
def start(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    # إذا أنت المطور، فعل الحساب تلقائيًا
    if uid == str(OWNER_ID):
        if uid not in users:
            users[uid] = {"active":True,"role":"owner","id_hash":None,"ip_hash":None,"session_file":None,"total_channels":0,"remaining_time":None,"channels_info":[]}
            save_users(users)
    
    if uid not in users:
        users[uid] = {"active":False,"role":"user","id_hash":None,"ip_hash":None,"session_file":None,"total_channels":0,"remaining_time":None,"channels_info":[]}
        save_users(users)
    
    if not users[uid]["active"]:
        bot.send_message(m.chat.id,
            f"🚫 حسابك غير مفعل.\nمطور البوت: {DEV_USER}\nأرسل كود التفعيل:"
        )
        return
    
    bot.send_message(m.chat.id,
        f"👋 أهلاً بك\nمطور البوت: {DEV_USER}\nاختر من القائمة:",
        reply_markup=main_menu()
    )

# ====================== تفعيل الكود ======================
@bot.message_handler(func=lambda m: True)
def activate_code(m):
    uid = str(m.from_user.id)
    users = load_users()
    if users[uid]["active"]:
        return
    user_input = m.text.strip()
    codes_data = load_codes()
    for code in codes_data["CODES"]:
        if code["code"]==user_input:
            if not code["used"]:
                code["used"]=True
                save_codes(codes_data)
                users[uid]["active"]=True
                users[uid]["role"]="owner"
                save_users(users)
                bot.send_message(m.chat.id,
                    f"✅ تم تفعيل البوت بنجاح! مرحبًا VIP.\nمطور البوت: {DEV_USER}"
                )
                return
            else:
                bot.send_message(m.chat.id,"❌ هذا الكود تم استخدامه سابقًا.")
                return
    bot.send_message(m.chat.id,"❌ الكود غير صحيح، حاول مرة أخرى.")

# ====================== Telethon Userbot ======================
async def userbot_task(client, uid):
    try:
        now = datetime.now()
        title = f"FaDi Channel {now.strftime('%d-%m-%Y %H:%M:%S')}"
        ch = await client(functions.channels.CreateChannelRequest(title=title, about="قناة خاصة", megagroup=False))
        ch_id = ch.chats[0].id
        for i in range(1,MESSAGES_PER_CHANNEL+1):
            await client.send_message(ch_id,f"رسالة {i} من {DEV_USER} بتاريخ {now.strftime('%d-%m-%Y %H:%M:%S')}")
        users = load_users()
        users[uid]["channels_info"].append({"title":title,"id":ch_id,"created_at":now.strftime('%d-%m-%Y %H:%M:%S')})
        users[uid]["total_channels"]+=1
        users[uid]["remaining_time"]=CHANNEL_INTERVAL
        save_users(users)
        await client.delete_dialog(ch_id)
    except Exception as e:
        print(f"Error: {e}")

async def userbot_loop(client, uid):
    while True:
        await userbot_task(client, uid)
        await asyncio.sleep(CHANNEL_INTERVAL)

def start_userbot_loop(session_file, uid):
    client = TelegramClient(f"sessions/{session_file}", API_ID, API_HASH)
    client.start()
    loop = asyncio.get_event_loop()
    loop.create_task(userbot_loop(client, uid))
    return client

# ====================== الأزرار ======================
@bot.callback_query_handler(func=lambda c: True)
def handle_buttons(c):
    uid = str(c.from_user.id)
    users = load_users()
    user = users[uid]
    if not user.get("active"):
        return bot.answer_callback_query(c.id,"❌ غير مفعل")
    if c.data=="account":
        bot.edit_message_text("🔐 ضع بيانات حسابك:",c.message.chat.id,c.message.message_id,reply_markup=account_menu())
    elif c.data=="back":
        bot.edit_message_text("👋 القائمة الرئيسية:",c.message.chat.id,c.message.message_id,reply_markup=main_menu())
    elif c.data=="add_id":
        msg=bot.send_message(c.message.chat.id,"🆔 أرسل ID HASH:")
        bot.register_next_step_handler(msg,lambda m: save_data("id_hash",m))
    elif c.data=="add_ip":
        msg=bot.send_message(c.message.chat.id,"🌐 أرسل IP HASH:")
        bot.register_next_step_handler(msg,lambda m: save_data("ip_hash",m))
    elif c.data=="add_session":
        msg=bot.send_message(c.message.chat.id,"📂 أرسل ملف السيزون:")
        bot.register_next_step_handler(msg,save_session_file)
    elif c.data=="start_bot":
        if not user.get("id_hash") or not user.get("ip_hash") or not user.get("session_file"):
            return bot.answer_callback_query(c.id,"❌ لازم تضيف ID HASH + IP HASH + SESSION")
        if uid in active_clients:
            return bot.answer_callback_query(c.id,"✅ Userbot بالفعل يعمل")
        client=start_userbot_loop(user["session_file"],uid)
        active_clients[uid]=client
        bot.answer_callback_query(c.id,"🚀 تم بدء التشغيل")
    elif c.data=="stop_bot":
        client=active_clients.get(uid)
        if client:
            client.disconnect()
            del active_clients[uid]
            bot.answer_callback_query(c.id,"⏹ تم إيقاف Userbot")
        else:
            bot.answer_callback_query(c.id,"❌ Userbot غير مفعل")
    elif c.data=="status":
        status_msg=f"""
📊 حالة حسابك:

👤 مطور البوت: {DEV_USER}
✅ مفعل: {'نعم' if user.get('active') else 'لا'}
🛡 الدور: {user.get('role','user')}
🆔 ID HASH: {"✅ موجود" if user.get("id_hash") else "❌ لم يُدخل"}
🌐 IP HASH: {"✅ موجود" if user.get("ip_hash") else "❌ لم يُدخل"}
📂 SESSION: {"✅ موجود" if user.get("session_file") else "❌ لم يُدخل"}
🚀 Userbot: {"✅ يعمل" if uid in active_clients else "⏹ متوقف"}
📊 عدد القنوات المنشأة: {user.get("total_channels",0)}
⏳ الوقت المتبقي للقناة التالية: {user.get("remaining_time","غير محدد")}
"""
        bot.send_message(c.message.chat.id,status_msg)

# ====================== حفظ البيانات ======================
def save_data(field,m):
    uid=str(m.from_user.id)
    users=load_users()
    users[uid][field]=m.text
    save_users(users)
    bot.send_message(m.chat.id,f"✅ تم حفظ {field}")

def save_session_file(m):
    uid=str(m.from_user.id)
    if not m.document:
        bot.send_message(m.chat.id,"❌ هذا ليس ملف")
        return
    file_path=f"sessions/{uid}.session"
    file_info = bot.get_file(m.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_path,"wb") as f:
        f.write(downloaded_file)
    users=load_users()
    users[uid]["session_file"]=str(uid)+".session"
    save_users(users)
    bot.send_message(m.chat.id,f"✅ تم حفظ ملف السيزون\n🚀 الحساب جاهز للتشغيل\nمطور البوت: {DEV_USER}")

# ====================== تشغيل البوت ======================
bot.infinity_polling()