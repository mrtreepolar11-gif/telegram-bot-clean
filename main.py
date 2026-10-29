import logging
from flask import Flask
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

USER_BALANCES = {}
PENDING_TRANSACTIONS = {}
ADMIN_ID = 745868523

# ফ্লাস্কের একটি ছোট ডামি সার্ভার, যাতে রেন্ডার একে ২৪/৭ লাইভ রাখে
web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Bot is running 24/7 successfully!"


def run_flask():
    web_app.run(host="0.0.0.0", port=10000)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in USER_BALANCES:
        USER_BALANCES[user.id] = 0.0

    keyboard = [
        [InlineKeyboardButton("🛒 Gmail Buy", callback_data="gmail_buy_menu")],
        [InlineKeyboardButton("📤 Gmail Sell", callback_data="gmail_sell_menu")],
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit_menu")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_menu")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile_menu")],
        [InlineKeyboardButton("🆘 Admin Support", callback_data="admin_support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "স্বাগতম! Digital Service Shop-এ আপনাকে স্বাগতম።\nনিচের মেনু থেকে একটি অপশন বেছে নিন:",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # --- Gmail Buy Menu ---
    if data == "gmail_buy_menu":
        text = "📩 **Gmail Buy Menu**\n\n• প্রতি পিস জিমেইলের মূল্য: ৩০ টাকা\n\nআপনি কতগুলো জিমেইল কিনতে চান? নিচের অপশন থেকে সিলেক্ট করুন:"
        keyboard = [
            [
                InlineKeyboardButton("১টা (৩০ Tk)", callback_data="buy_1"),
                InlineKeyboardButton("৫টা (150 Tk)", callback_data="buy_5"),
            ],
            [
                InlineKeyboardButton("১০টা (300 Tk)", callback_data="buy_10"),
                InlineKeyboardButton("২০টা (600 Tk)", callback_data="buy_20"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data.startswith("buy_"):
        quantity = int(data.split("_")[1])
        price = quantity * 30

        if USER_BALANCES.get(user_id, 0.0) >= price:
            USER_BALANCES[user_id] -= price
            admin_text = f"📩 **New Gmail Order!**\n\nUser ID: {user_id}\nQuantity: {quantity}\nPrice: {price} Tk"
            await context.bot.send_message(
                chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown"
            )
            await query.edit_message_text(
                f"✅ আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে। {quantity}টি জিমেইল কেনার জন্য {price} টাকা কেটে নেওয়া হয়েছে। এটি Pending অবস্থায় আছে."
            )
        else:
            await query.edit_message_text(
                "❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই। দয়া করে ডিপোজিট করুন."
            )

    # --- Gmail Sell Menu ---
    elif data == "gmail_sell_menu":
        text = (
            "📤 **Gmail Sell Menu**\n\n"
            "• প্রতি পিস জিমেইলের দাম ২০ টাকা করে\n\n"
            "দয়া করে আপনার জিমেইল অ্যাকাউন্ট, পাসওয়ার্ড এবং রিকভারি মেইল লিখে পাঠান."
        )
        context.user_data["waiting_for"] = "sell_info"
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "deposit_menu":
        text = "💰 **Deposit**\n\nপেমেন্ট মেথড সিলেক্ট করুন:"
        keyboard = [
            [
                InlineKeyboardButton("বিকাশ (Bkash)", callback_data="dep_bkash"),
                InlineKeyboardButton("নগদ (Nagad)", callback_data="dep_nagad"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data in ["dep_bkash", "dep_nagad"]:
        method = "বিকাশ" if data == "dep_bkash" else "নগদ"
        context.user_data["deposit_method"] = method
        text = (
            f"আপনি **{method}** সিলেক্ট করেছেন।\n\n"
            f"আমাদের মার্চেন্ট নাম্বার: `01715914270`\n"
            f"সর্বনিম্ন ডিপোজিট: ৬০ টাকা\n\n"
            f"দয়া করে সেন্ড মানি (Send Money) করার পর আপনার ট্রানজেকশন আইডি (TrxID) লিখে পাঠান."
        )
        context.user_data["waiting_for"] = "deposit_trx"
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="deposit_menu")]
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "withdraw_menu":
        text = "💸 **Withdraw**\n\nপেমেন্ট মেথড সিলেক্ট করুন:"
        keyboard = [
            [
                InlineKeyboardButton("বিকাশ (Bkash)", callback_data="wd_bkash"),
                InlineKeyboardButton("নগদ (Nagad)", callback_data="wd_nagad"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data in ["wd_bkash", "wd_nagad"]:
        method = "বিকাশ" if data == "wd_bkash" else "নগদ"
        context.user_data["withdraw_method"] = method
        text = (
            f"আপনি **{method}** সিলেক্ট করেছেন।\n\n"
            f"সর্বনিম্ন উইথড্র: ১১০ টাকা থেকে শুরু (১১০ টাকা, ২২০ টাকা ইত্যাদি)\n\n"
            f"দয়া করে আপনার উইথড্র করার পরিমাণ এবং নাম্বার লিখে পাঠান (যেমন: `110 017XXXXXXXX`)."
        )
        context.user_data["waiting_for"] = "withdraw_info"
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="withdraw_menu")]
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "admin_support":
        text = "🆘 **Admin Support**\n\nকোন ধরনের সার্ভিস বা সহায়তা চান, তা লিখুন।\n\n⚠️ **সতর্কতা:** Gmail পাসওয়ার্ড পাঠাবেন না."
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        context.user_data["waiting_for"] = "admin_query"

    elif data == "profile_menu":
        user = query.from_user
        balance = USER_BALANCES.get(user.id, 0.0)
        text = (
            "👤 **User Profile**\n\n"
            f"🆔 User ID: `{user.id}`\n"
            f"💰 Balance: {balance} BDT\n"
            f"🔗 Referral Link: `https://t.me/YourBotName?start={user.id}`"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("🛒 Gmail Buy", callback_data="gmail_buy_menu")],
            [InlineKeyboardButton("📤 Gmail Sell", callback_data="gmail_sell_menu")],
            [InlineKeyboardButton("💰 Deposit", callback_data="deposit_menu")],
            [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_menu")],
            [InlineKeyboardButton("👤 Profile", callback_data="profile_menu")],
            [InlineKeyboardButton("🆘 Admin Support", callback_data="admin_support")],
        ]
        await query.edit_message_text(
            "আপনার পছন্দের অপশনটি বেছে নিন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # --- Admin Approval Handlers ---
    elif data.startswith("app_sell_") or data.startswith("rej_sell_") or \
         data.startswith("app_dep_") or data.startswith("rej_dep_") or \
         data.startswith("app_wd_") or data.startswith("rej_wd_"):
        
        parts = data.split("_")
        action = parts[0]
        req_type = parts[1]
        target_user_id = int(parts[2])

        if action == "app":
            if req_type == "dep":
                USER_BALANCES[target_user_id] = USER_BALANCES.get(target_user_id, 0.0) + 60.0
                await context.bot.send_message(chat_id=target_user_id, text="✅ আপনার ডিপোজিট সফলভাবে অ্যাপ্রুভ করা হয়েছে এবং অ্যাকাউন্টে ব্যালেন্স যোগ হয়েছে!")
            elif req_type == "sell":
                USER_BALANCES[target_user_id] = USER_BALANCES.get(target_user_id, 0.0) + 20.0
                await context.bot.send_message(chat_id=target_user_id, text="✅ আপনার জিমেইল সেল রিকোয়েস্ট অ্যাপ্রুভ করা হয়েছে!")
            elif req_type == "wd":
                await context.bot.send_message(chat_id=target_user_id, text="✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে পেমেন্ট করা হয়েছে!")
            
            await query.edit_message_text(f"{query.message.text}\n\n👉 **Status: Approved ✅**")
        else:
            if req_type == "dep":
                await context.bot.send_message(chat_id=target_user_id, text="❌ আপনার ডিপোজিট রিকোয়েস্টটি রিজেক্ট করা হয়েছে।")
            elif req_type == "sell":
                await context.bot.send_message(chat_id=target_user_id, text="❌ আপনার জিমেইল সেল রিকোয়েস্টটি রিজেক্ট করা হয়েছে।")
            elif req_type == "wd":
                await context.bot.send_message(chat_id=target_user_id, text="❌ আপনার উইথড্র রিকোয়েস্টটি রিজেক্ট করা হয়েছে।")
            
            await query.edit_message_text(f"{query.message.text}\n\n👉 **Status: Rejected ❌**")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    waiting_for = context.user_data.get("waiting_for")

    if waiting_for == "sell_info":
        admin_text = f"📤 **New Gmail Sell Request!**\n\nUser ID: {user.id}\nDetails:\n{text}"
        keyboard = [
            [
                InlineKeyboardButton("Approve", callback_data=f"app_sell_{user.id}"),
                InlineKeyboardButton("Reject", callback_data=f"rej_sell_{user.id}"),
            ]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            "✅ আপনার অনুরোধটি সফলভাবে গ্রহণ করা হয়েছে এবং এটি Pending অবস্থায় আছে."
        )
        context.user_data["waiting_for"] = None

    elif waiting_for == "deposit_trx":
        method = context.user_data.get("deposit_method")
        admin_text = f"📥 **New Deposit Request!**\n\nUser ID: {user.id}\nMethod: {method}\nTrxID: {text}"
        keyboard = [
            [
                InlineKeyboardButton("Approve", callback_data=f"app_dep_{user.id}"),
                InlineKeyboardButton("Reject", callback_data=f"rej_dep_{user.id}"),
            ]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            "📥 আপনার ডিপোজিট রিকোয়েস্টটি পেন্ডিং আছে। অ্যাডমিন যাচাই করার পর সাকসেসফুল করা হবে."
        )
        context.user_data["waiting_for"] = None

    elif waiting_for == "withdraw_info":
        method = context.user_data.get("withdraw_method")
        admin_text = f"📤 **New Withdraw Request!**\n\nUser ID: {user.id}\nMethod: {method}\nDetails:\n{text}"
        keyboard = [
            [
                InlineKeyboardButton("Approve", callback_data=f"app_wd_{user.id}"),
                InlineKeyboardButton("Reject", callback_data=f"rej_wd_{user.id}"),
            ]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            "📤 আপনার উইথড্র রিকোয়েস্টটি পেন্ডিং রয়েছে। অ্যাডমিন পেমেন্ট করার পর সাকসেসফুল করা হবে."
        )
        context.user_data["waiting_for"] = None

    elif waiting_for == "admin_query":
        admin_text = (
            f"🆘 **New Support Request!**\n\nUser ID: {user.id}\nQuery:\n{text}"
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown"
        )
        await update.message.reply_text(
            "✅ আপনার মেসেজটি অ্যাডমিনের কাছে পাঠানো হয়েছে। শীঘ্রই আপনাকে রিপ্লাই দেওয়া হবে."
        )
        context.user_data["waiting_for"] = None


def main():
    # ব্যাকগ্রাউন্ডে ফ্লাস্ক সার্ভার চালু করা যাতে রেন্ডার একে লাইভ রাখে
    t = threading.Thread(target=run_flask)
    t.start()

    app = (
        ApplicationBuilder()
        .token("9202301606:AAHwht3TKt7fzvtmnR3vrF9rk04zoW5Haj4")
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
