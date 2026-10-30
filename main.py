import logging
import os
import threading
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Admin ID & Support
ADMIN_ID = 7458685213
ADMIN_SUPPORT = "@nahidbro204"
OFFICIAL_GROUP_LINK = "https://t.me/nahidgmailsallar204"

# Final Category-wise Sell Prices
SELL_PRICES = {
    "1": 20.0,  # Fresh Gmail
    "2": 35.0,  # Old Gmail
    "3": 25.0,  # Recovery Added
    "4": 30.0,  # 2FA Enabled
    "5": 15.0   # Facebook Created Gmail
}

CATEGORY_NAMES = {
    "1": "Fresh Gmail",
    "2": "Old Gmail",
    "3": "Recovery Added",
    "4": "2FA Enabled",
    "5": "Facebook created Gmail"
}

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
            'sell_data': {},
            'is_verified': False
        }
        if referrer_id and referrer_id in users_db and referrer_id != user_id:
            if user_id not in users_db[referrer_id]['team']:
                users_db[referrer_id]['team'].append(user_id)
    return users_db[user_id]

# Start Command - Shows Notice and Join/Verify buttons first
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referrer_id = int(args[0]) if args and args[0].isdigit() else None
    
    user_data = get_user(user.id, referrer_id)
    
    if user_data.get('is_verified'):
        await show_main_menu(update, context)
        return
    
    notice_text = (
        f"📢 **Ofisial Notish!**\n\n"
        f"Assalamu Alaikum {user.first_name}! Amader sokol notun update ebong support pete prothome amader ofisial groupe joyen korun.\n\n"
        f"Nicher batane chap diye groupe joyen korar por **'Verify'** batane chap din."
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 Ofisial Groupe Joyen Korun", url=OFFICIAL_GROUP_LINK)],
        [InlineKeyboardButton("✅ Verify (Jachai Korun)", callback_data="verify_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(notice_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(notice_text, reply_markup=reply_markup, parse_mode="Markdown")

# Function to display Main Menu
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛒 Gmail Kroy (Gmail Buy)", callback_data="menu_buy")],
        [InlineKeyboardButton("📤 Gmail Bikri (Gmail Sell)", callback_data="menu_sell")],
        [InlineKeyboardButton("💰 Deposit", callback_data="menu_deposit")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="menu_withdraw")],
        [InlineKeyboardButton("👥 Amar Team", callback_data="menu_team")],
        [InlineKeyboardButton("👤 Balance o Profile", callback_data="menu_profile"),
         InlineKeyboardButton("📞 Support", url=f"https://t.me/{ADMIN_SUPPORT.replace('@','')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🌟 **Swagotom, {user.first_name}!**\n\n"
        f"Amader digital service shope apnake swagotom. Nicher theke apnar proyojonio option select korun:"
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
    
    if data == "verify_join":
        user_data['pending_action'] = 'waiting_verify'
        await query.message.edit_text(
            "⏳ Apnar verification request admin-er kase pathano hoyeche. Onugra kore anumodon-er jonno opekha korun...",
            parse_mode="Markdown"
        )
        
        admin_text = (
            f"🔔 **Notun Member Verification Request!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"👤 Username: @{query.from_user.username if query.from_user.username else 'N/A'}\n"
            f"📌 Status: 🟡 Pending"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_verify_{user_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_verify_{user_id}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    elif data.startswith("admin_approve_verify_"):
        target_user_id = int(data.split("_")[3])
        target_user = get_user(target_user_id)
        target_user['is_verified'] = True
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **Verified by Admin**")
        try:
            keyboard = [
                [InlineKeyboardButton("🛒 Gmail Kroy (Gmail Buy)", callback_data="menu_buy")],
                [InlineKeyboardButton("📤 Gmail Bikri (Gmail Sell)", callback_data="menu_sell")],
                [InlineKeyboardButton("💰 Deposit", callback_data="menu_deposit")],
                [InlineKeyboardButton("💸 Withdraw", callback_data="menu_withdraw")],
                [InlineKeyboardButton("👥 Amar Team", callback_data="menu_team")],
                [InlineKeyboardButton("👤 Balance o Profile", callback_data="menu_profile"),
                 InlineKeyboardButton("📞 Support", url=f"https://t.me/{ADMIN_SUPPORT.replace('@','')}")]
            ]
            await context.bot.send_message(
                target_user_id, 
                "✅ **Apnar verification safol hoyeche!**\n\nAmader bot babohar korar jonno apnake swagotom. Nicher theke option select korun:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except:
            pass
        return

    elif data.startswith("admin_cancel_verify_"):
        target_user_id = int(data.split("_")[3])
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **Verification Cancelled by Admin**")
        try:
            await context.bot.send_message(target_user_id, "❌ Apnar verification request batil kora hoyeche. Onugra kore niyom mene groupe joyen kore abar chesta korun.")
        except:
            pass
        return

    if data == "main_menu":
        user_data['pending_action'] = None
        user_data['sell_data'] = {}
        await show_main_menu(update, context)
        
    elif data == "menu_buy":
        user_data['pending_action'] = 'buy_gmail'
        text = (
            "🛒 **Gmail Kroy Menu** 🛒\n\n"
            "🟢 **Status:** `Stock Available`\n"
            "💵 **Mulsho:** `Proti pis gmail matro 30 BDT`\n\n"
            "📝 **Apni kothogulo gmail kroy korben niche songkhay like pathan:**"
        )
        keyboard = [[InlineKeyboardButton("🔙 Mulin Menu", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "menu_sell":
        user_data['pending_action'] = 'sell_get_gmail'
        user_data['sell_data'] = {}
        text = (
            "📤 **Gmail Bikri Menu**\n\n"
            "Apnar pochhonder category select korun:"
        )
        cats = [
            ("1", "1. Fresh Gmail (20 Tk)"), 
            ("2", "2. Old Gmail (35 Tk)"), 
            ("3", "3. Recovery Added (25 Tk)"), 
            ("4", "4. 2FA Enabled (30 Tk)"),
            ("5", "5. Facebook created Gmail (15 Tk)")
        ]
        keyboard = [[InlineKeyboardButton(label, callback_data=f"sell_cat_{cat_id}")] for cat_id, label in cats]
        keyboard.append([InlineKeyboardButton("🔙 Mulin Menu", callback_data="main_menu")])
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data.startswith("sell_cat_"):
        cat_id = data.split("_")[2]
        user_data['sell_data']['cat_id'] = cat_id
        user_data['pending_action'] = 'sell_get_gmail'
        
        cat_name = CATEGORY_NAMES.get(cat_id, "Unknown")
        price = SELL_PRICES.get(cat_id, 20.0)
        
        text = (
            f"📤 **Category:** `{cat_name}` (Rate: `{price} BDT`)\n\n"
            "✉️ **Prothome apnar Gmail ti like pathan:**"
        )
        keyboard = [[InlineKeyboardButton("🔙 Fire Jan", callback_data="menu_sell")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_deposit":
        user_data['pending_action'] = 'deposit_amount'
        text = (
            "💰 **Deposit Menu**\n\n"
            "Nicher nombor-e send money korun:\n"
            "📌 **bKash / Nagad (Personal):** `01715914270`\n\n"
            "⚠️ **Somninno deposit 60 taka.**\n\n"
            "📝 **Apni koto taka deposit korechen ta onkke like pathan (Jemon: 100):**"
        )
        keyboard = [[InlineKeyboardButton("🔙 Mulin Menu", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_withdraw":
        user_data['pending_action'] = 'withdraw_method'
        text = (
            "💸 **Withdraw Console**\n\n"
            "Apnar account balance: **" + str(user_data['balance']) + " BDT**\n\n"
            "Doya kore payment method select korun:"
        )
        keyboard = [
            [InlineKeyboardButton("bKash (Personal)", callback_data="wd_bkash")],
            [InlineKeyboardButton("Nagad (Personal)", callback_data="wd_nagad")],
            [InlineKeyboardButton("🔙 Mulin Menu", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data in ["wd_bkash", "wd_nagad"]:
        method = "bKash (Personal)" if data == "wd_bkash" else "Nagad (Personal)"
        user_data['withdraw_data']['method'] = method
        user_data['pending_action'] = 'withdraw_amount'
        
        text = (
            f"💸 **Withdraw - {method}**\n\n"
            "📝 **Apni koto taka withdraw korte chan ta likhun:**\n"
            "⚠️ _Somninno withdraw 110 taka._"
        )
        keyboard = [[InlineKeyboardButton("🔙 Fire Jan", callback_data="menu_withdraw")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_team":
        team_list = user_data['team']
        total_team = len(team_list)
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        text = (
            f"👥 **Amar Team o Referral Report**\n\n"
            f"🔹 **Mot team member:** `{total_team} jon`\n\n"
            f"🔗 **Apnar referral link:**\n`{ref_link}`\n\n"
            f"📋 **Apnar team-er talika:**\n"
        )
        if total_team == 0:
            text += "Ekhono keu apnar link-e joyen koreni."
        else:
            for idx, member_id in enumerate(team_list, 1):
                text += f"{idx}. User ID: `{member_id}`\n"
                
        keyboard = [[InlineKeyboardButton("🔙 Mulin Menu", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_profile":
        text = (
            f"👤 **Apnar Profile**\n\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"💰 **Balance:** `{user_data['balance']} BDT`\n"
            f"👥 **Mot referral:** `{len(user_data['team'])}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Mulin Menu", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("admin_approve_dep_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        target_user = get_user(target_user_id)
        target_user['balance'] += amount
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **Admin কর্তৃক অনুমোদিত (Deposit: {amount} BDT)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ Apnar deposit safol hoyeche! Apnar account-e {amount} BDT jog kora hoyeche.")
        except:
            pass

    elif data.startswith("admin_cancel_dep_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **Admin কর্তৃক বাতিল (Deposit: {amount} BDT)**")
        try:
            await context.bot.send_message(target_user_id, f"❌ Apnar deposit request ({amount} BDT) batil kora hoyeche.")
        except:
            pass

    elif data.startswith("admin_approve_sell_"):
        parts = data.split("_")
        target_user_id = int(parts[3])
        cat_id = parts[4]
        sell_reward = SELL_PRICES.get(cat_id, 20.0)
        
        target_user = get_user(target_user_id)
        target_user['balance'] += sell_reward
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **Gmail bikri onumodito (Balance-e {sell_reward} BDT jog kora hoyeche)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ Apnar gmail bikri safol hoyeche! Admin jachai kore apnar account-e {sell_reward} BDT jog korechen.")
        except:
            pass

    elif data.startswith("admin_cancel_sell_"):
        target_user_id = int(data.split("_")[3])
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **Gmail-er order batil kora hoyeche**")
        try:
            await context.bot.send_message(target_user_id, f"❌ Apnar gmail bikrir request ti batil kora hoyeche.")
        except:
            pass

    elif data.startswith("admin_approve_wd_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        
        await query.message.edit_text(query.message.text + f"\n\n✅ **Safolvabe payment kora hoyeche (Admin)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ Apnar withdraw safol hoyeche! Admin payment somponno করেছেন ({amount} BDT).")
        except:
            pass

    elif data.startswith("admin_reject_wd_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        target_user = get_user(target_user_id)
        target_user['balance'] += amount  
        
        await query.message.edit_text(query.message.text + f"\n\n❌ **Batil kora hoyeche (Balance ferot dewa hoyeche)**")
        try:
            await context.bot.send_message(target_user_id, f"❌ Apnar withdraw request ti batil kora hoyeche ebong {amount} BDT apnar account-e firiye dewa hoyeche.")
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
            await update.message.reply_text("❌ Doya kore sothik songkha likhun.")
            return
        
        quantity = int(text)
        total_cost = quantity * 30
        
        if user_data['balance'] < total_cost:
            await update.message.reply_text("❌ Apnar account-e porjapto balance নেই।")
            return
        
        user_data['balance'] -= total_cost
        user_data['pending_action'] = None
        
        await update.message.reply_text(
            f"✅ Apnar order ti safolvabe grohon kora hoyeche!\n"
            f"🛒 Poriman: {quantity} ti gmail\n"
            f"💵 Mot khoroch: {total_cost} BDT\n"
            f"⏳ Status: **Pending (Admin shigghiri delivery deben)**"
        )
        
        admin_text = (
            f"🔔 **Notun Gmail Kroy Order!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"👤 Username: @{user.username if user.username else 'N/A'}\n"
            f"📦 Quantity: {quantity} Pcs\n"
            f"💵 Total Cost: {total_cost} BDT"
        )
        await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

    elif action == 'sell_get_gmail':
        if 'cat_id' not in user_data['sell_data']:
            user_data['sell_data']['cat_id'] = "1"
            
        user_data['sell_data']['gmail'] = text
        user_data['pending_action'] = 'sell_get_password'
        
        await update.message.reply_text("🔑 **Doya kore password like pathan:**")

    elif action == 'sell_get_password':
        user_data['sell_data']['password'] = text
        
        cat_id = user_data['sell_data'].get('cat_id', '1')
        gmail = user_data['sell_data'].get('gmail', '')
        password = user_data['sell_data'].get('password', '')
        
        user_data['pending_action'] = None
        user_data['sell_data'] = {}
        
        order_counter += 1
        current_order_id = order_counter
        
        cat_name = CATEGORY_NAMES.get(cat_id, "Unknown")
        reward = SELL_PRICES.get(cat_id, 20.0)
        
        await update.message.reply_text(
            f"⏳ **Apnar gmail-er biboron safolvabe grohon kora hoyeche!**\n"
            f"📋 Order Number: `#{current_order_id}`\n"
            f"🔄 Status: `Jachai kora hocche (Pending)`\n\n"
            f"Admin jachai kore apnar balance update kore deben."
        )
        
        admin_text = (
            f"🔔 **Notun Gmail Bikrir Request!**\n\n"
            f"📋 **Order Number:** `#{current_order_id}`\n"
            f"👤 **User ID:** `{user_id}`\n"
            f"👤 **Username:** @{user.username if user.username else 'N/A'}\n"
            f"🏷️ **Category:** {cat_name} (ID: {cat_id})\n"
            f"💵 **Reward:** {reward} BDT\n\n"
            f"📧 **Gmail:**\n`{gmail}`\n\n"
            f"🔑 **Password:**\n`{password}`\n\n"
            f"📌 **Status:** 🟡 Pending"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_sell_{user_id}_{cat_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_sell_{user_id}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif action == 'deposit_amount':
        if not text.replace('.', '', 1).isdigit():
            await update.message.reply_text("❌ Doya kore sothik takar poriman likhun.")
            return
        
        amount = float(text)
        if amount < 60:
            await update.message.reply_text("❌ Somninno deposit 60 taka.")
            return
            
        user_data['deposit_data']['amount'] = amount
        user_data['pending_action'] = 'deposit_trxid'
        
        await update.message.reply_text("📝 **Ekhon apnar bKash/Nagad Transaction ID (TrxID) like pathan:**")

    elif action == 'deposit_trxid':
        trx_info = text
        amount = user_data['deposit_data'].get('amount', 0)
        user_data['pending_action'] = None
        user_data['deposit_data'] = {}
        
        await update.message.reply_text("✅ Apnar deposit request ebong TrxID admin-er kase pathano hoyeche. Onugra kore anumodon-er jonno opekha korun.")
        
        admin_text = (
            f"🔔 **Notun Deposit Request!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💰 Amount: {amount} BDT\n"
            f"📝 TrxID / Info: `{trx_info}`\n"
            f"📌 Status: 🟡 Pending"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_dep_{user_id}_{amount}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_dep_{user_id}_{amount}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif action == 'withdraw_amount':
        if not text.replace('.', '', 1).isdigit():
            await update.message.reply_text("❌ Doya kore sothik takar poriman likhun.")
            return
            
        amount = float(text)
        if amount < 110:
            await update.message.reply_text("❌ Apnar account-e porjapto taka nai (Somninno 110 taka).")
            return
            
        if user_data['balance'] < amount:
            await update.message.reply_text("❌ Apnar account-e porjapto balance নেই।")
            return
            
        user_data['withdraw_data']['amount'] = amount
        user_data['pending_action'] = 'withdraw_number'
        
        await update.message.reply_text(
            "📞 **Receiver account nombor din:**\n\n"
            "⚠️ _Sotorkbarta: Obosshoi sothik nombor input korun. Vul nombor-e payment chole gele kortripokkho dayi thakbe na._"
        )

    elif action == 'withdraw_number':
        number = text
        wd_data = user_data['withdraw_data']
        method = wd_data.get('method')
        amount = wd_data.get('amount')
        
        user_data['balance'] -= amount
        user_data['pending_action'] = None
        user_data['withdraw_data'] = {}
        
        await update.message.reply_text("⏳ Apnar withdraw request ti pending ache. Admin payment korar por safol dekhano hobe.")
        
        admin_text = (
            f"🔔 **Notun Withdraw Request!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💳 Method: {method}\n"
            f"💰 Amount: {amount} BDT\n"
            f"📱 Receiver Number: `{number}`"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Success", callback_data=f"admin_approve_wd_{user_id}_{amount}"),
                InlineKeyboardButton("❌ Cancel (Refund)", callback_data=f"admin_reject_wd_{user_id}_{amount}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Web server handler for Render health check
async def handle_web(request):
    return web.Response(text="Bot is active and running 24/7!")

def main():
    TOKEN = "9197059198:AAF-uRkXSJjGiQF54qsBXKBBfK53H9l5s3Q"
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app = web.Application()
    app.router.add_get("/", handle_web)
    
    port = int(os.environ.get("PORT", 8080))
    
    def run_web():
        web.run_app(app, host="0.0.0.0", port=port, print=None)
        
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    print("Starting Telegram Bot Polling 24/7...")
    application.run_polling()

if __name__ == '__main__':
    main()
