import logging
import os
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Admin ID & Support
ADMIN_ID = 7458685213
ADMIN_SUPPORT = "@nahidbro204"

# In-memory database
users_db = {}
order_counter = 1000

def get_user(user_id, referrer_id=None):
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': 0.0,
            'referred_by': referrer_id,
            'team': [],
            'pending_action': None,
            'withdraw_data': {},
            'deposit_data': {},
            'sell_data': {}
        }
        if referrer_id and referrer_id in users_db and referrer_id != user_id:
            if user_id not in users_db[referrer_id]['team']:
                users_db[referrer_id]['team'].append(user_id)
    return users_db[user_id]

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referrer_id = int(args[0]) if args and args[0].isdigit() else None
    
    get_user(user.id, referrer_id)
    
    keyboard = [
        [InlineKeyboardButton("🛒 জিমেইল ক্রয় (Gmail Buy)", callback_data="menu_buy")],
        [InlineKeyboardButton("📤 জিমেইল বিক্রি (Gmail Sell)", callback_data="menu_sell")],
        [InlineKeyboardButton("💰 ডিপোজিট (Deposit)", callback_data="menu_deposit")],
        [InlineKeyboardButton("💸 উইথড্র (Withdraw)", callback_data="menu_withdraw")],
        [InlineKeyboardButton("👥 আমার টিম (My Team)", callback_data="menu_team")],
        [InlineKeyboardButton("👤 ব্যালেন্স ও প্রোফাইল", callback_data="menu_profile"),
         InlineKeyboardButton("📞 সাপোর্ট", url=f"https://t.me/{ADMIN_SUPPORT.replace('@','')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🌟 **স্বাগতম, {user.first_name}!**\n\n"
        f"আমাদের ডিজিটাল সার্ভিস শপে আপনাকে স্বাগতম। নিচে থেকে আপনার প্রয়োজনীয় অপশনটি সিলেক্ট করুন:"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# Main Menu Callback Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    data = query.data
    
    if data == "main_menu":
        user_data['pending_action'] = None
        await start(update, context)
        
    elif data == "menu_buy":
        user_data['pending_action'] = 'buy_gmail'
        text = (
            "🛒 **জি-মেইল ক্রয় মেনু (GMAIL BUY MENU)** 🛒\n\n"
            "🟢 **স্ট্যাটাস:** `স্টক এভেইলেবল (ইনস্ট্যান্ট ডেলিভারি)`\n"
            "💵 **মূল্য:** `প্রতি পিস জিমেইল মাত্র ৩০ টাকা (30 TK)`\n\n"
            "📝 **আপনি কতগুলো জিমেইল ক্রয় করবেন নিচে লিখুন (সংখ্যায়):**"
        )
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "menu_sell":
        user_data['pending_action'] = 'sell_gmail_category'
        text = (
            "📤 **জিমেইল বিক্রি মেনু (Gmail Sell)**\n\n"
            "আমাদের ৭টি ক্যাটাগরির যেকোনো একটি সিলেক্ট করুন যা আপনি বিক্রি করতে চান:"
        )
        cats = [
            "1. Fresh Gmail", "2. Old Gmail", "3. Phone Verified", 
            "4. Recovery Added", "5. 2FA Enabled", "6. Profile Setup", "7. Custom Bulk"
        ]
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"sell_cat_{i}")] for i, cat in enumerate(cats, 1)]
        keyboard.append([InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")])
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data.startswith("sell_cat_"):
        cat_id = data.split("_")[2]
        user_data['sell_data']['cat_id'] = cat_id
        user_data['pending_action'] = 'sell_details'
        text = (
            "📤 **জিমেইল বিক্রি বিবরণ (Gmail Details)**\n\n"
            "দয়া করে আপনার জিমেইলের বিবরণ দিন (Email:Password:Recovery mail).\n"
            "যদি রিকভারি মেইল না থাকে তবে শুধু Email:Password দিয়ে সেন্ড করুন।"
        )
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="menu_sell")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_deposit":
        user_data['pending_action'] = 'deposit_amount'
        text = (
            "💰 **ডিপোজিট মেনু (Deposit)**\n\n"
            "নিম্নলিখিত নম্বরে সেন্ড মানি করুন:\n"
            "📌 **Bkash / Nagad (Personal):** `01715914270`\n\n"
            "⚠️ **সর্বনিম্ন ডিপোজিট ৬০ টাকা।**\n\n"
            "📝 **আপনি কত টাকা ডিপোজিট করেছেন তা অংক লিখে পাঠান (যেমন: 100):**"
        )
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_withdraw":
        user_data['pending_action'] = 'withdraw_method'
        text = (
            "💸 **উইথড্র কনসোল (Withdrawal Console)**\n\n"
            "আপনার অ্যাকাউন্ট ব্যালেন্স: **" + str(user_data['balance']) + " BDT**\n\n"
            "দয়া করে আপনার পেমেন্ট মেথড সিলেক্ট করুন:"
        )
        keyboard = [
            [InlineKeyboardButton("bKash (Personal)", callback_data="wd_bkash")],
            [InlineKeyboardButton("Nagad (Personal)", callback_data="wd_nagad")],
            [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data in ["wd_bkash", "wd_nagad"]:
        method = "bKash (Personal)" if data == "wd_bkash" else "Nagad (Personal)"
        user_data['withdraw_data']['method'] = method
        user_data['pending_action'] = 'withdraw_amount'
        
        text = (
            f"💸 **Withdrawal - {method}**\n\n"
            "📝 **আপনি কত টাকা উইথড্র করতে চান তা লিখুন:**\n"
            "⚠️ _সর্বনিম্ন উইথড্র ১১০ টাকা।_"
        )
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="menu_withdraw")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_team":
        team_list = user_data['team']
        total_team = len(team_list)
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        text = (
            f"👥 **আপনার টিম ও রেফারেল রিপোর্ট**\n\n"
            f"🔹 **মোট টিম মেম্বার:** `{total_team} জন`\n\n"
            f"🔗 **আপনার রেফারেল লিংক:**\n`{ref_link}`\n\n"
            f"📋 **আপনার টিমের তালিকা:**\n"
        )
        if total_team == 0:
            text += "এখনো কেউ আপনার লিংকে জয়েন করেনি।"
        else:
            for idx, member_id in enumerate(team_list, 1):
                text += f"{idx}. User ID: `{member_id}`\n"
                
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_profile":
        text = (
            f"👤 **আপনার প্রোফাইল**\n\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"💰 **Balance:** `{user_data['balance']} BDT`\n"
            f"👥 **Total Referrals:** `{len(user_data['team'])}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("admin_approve_dep_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        target_user = get_user(target_user_id)
        target_user['balance'] += amount
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **Approved by Admin (Deposit: {amount} BDT)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ আপনার ডিপোজিট সফল হয়েছে! আপনার অ্যাকাউন্টে {amount} BDT যোগ করা হয়েছে।")
        except:
            pass

    elif data.startswith("admin_cancel_dep_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **Cancelled by Admin (Deposit: {amount} BDT)**")
        try:
            await context.bot.send_message(target_user_id, f"❌ আপনার ডিপোজিট রিকোয়েস্টটি ({amount} BDT) অ্যাডমিন কর্তৃক বাতিল করা হয়েছে।")
        except:
            pass

    elif data.startswith("admin_approve_sell_"):
        target_user_id = int(data.split("_")[3])
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **Gmail Sell Approved by Admin**")
        try:
            await context.bot.send_message(target_user_id, f"✅ আপনার জিমেইল বিক্রি সফল হয়েছে! অ্যাডমিন আপনার জিমেইল যাচাই করে ব্যালেন্স আপডেট করে দিয়েছেন।")
        except:
            pass

    elif data.startswith("admin_cancel_sell_"):
        target_user_id = int(data.split("_")[3])
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **Gmail Sell Cancelled by Admin**")
        try:
            await context.bot.send_message(target_user_id, f"❌ আপনার জিমেইল বিক্রির রিকোয়েস্টটি বাতিল করা হয়েছে।")
        except:
            pass

    elif data.startswith("admin_approve_wd_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        
        await query.message.edit_text(query.message.text + f"\n\n✅ **Successful (Paid by Admin)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ আপনার উইথড্র সফল হয়েছে! অ্যাডমিন পেমেন্ট সম্পন্ন করেছেন ({amount} BDT)।")
        except:
            pass

    elif data.startswith("admin_reject_wd_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        target_user = get_user(target_user_id)
        target_user['balance'] += amount  
        
        await query.message.edit_text(query.message.text + f"\n\n❌ **Cancelled by Admin (Balance Refunded)**")
        try:
            await context.bot.send_message(target_user_id, f"❌ আপনার উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে এবং {amount} BDT আপনার অ্যাকাউন্টে ফিরিয়ে দেওয়া হয়েছে।")
        except:
            pass

# Message / Input Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_counter
    user = update.effective_user
    user_id = user.id
    user_data = get_user(user_id)
    text = update.message.text.strip()
    
    action = user_data.get('pending_action')
    if not action:
        return

    if action == 'buy_gmail':
        if not text.isdigit():
            await update.message.reply_text("❌ দয়া করে সঠিক সংখ্যা লিখুন।")
            return
        
        quantity = int(text)
        total_cost = quantity * 30
        
        if user_data['balance'] < total_cost:
            await update.message.reply_text("আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই")
            return
        
        user_data['balance'] -= total_cost
        user_data['pending_action'] = None
        
        await update.message.reply_text(
