import time
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = '8150096244:AAFPsLFYaA9PsOesrE5TiyvaeBHhBwPU7s4'
GROUP_USERNAME = "momin_46"
OWNER_HANDLE = "@momintip"
GROUP_LINK = f"https://t.me/{GROUP_USERNAME}"

user_last_used = {}

async def is_user_verified(bot, user_id):
    try:
        # Try both with and without @ symbol for better compatibility
        try:
            member = await bot.get_chat_member(chat_id=f"@{GROUP_USERNAME}", user_id=user_id)
            return member.status in ["member", "administrator", "creator"]
        except:
            member = await bot.get_chat_member(chat_id=GROUP_USERNAME, user_id=user_id)
            return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Verification error: {e}")
        return False

def verification_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Join Group", url=GROUP_LINK),
            InlineKeyboardButton("🔁 Verify", callback_data='verify')
        ]
    ])

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not update.message or not update.message.text:
        await update.message.reply_text("❌ Invalid command format!")
        return
        
    message = update.message.text.split()

    if len(message) < 2:
        await update.message.reply_text("❌ Format: /like <server> <uid> or /spam bd <uid>")
        return

    # Show processing message
    processing_msg = await update.message.reply_text("⏳ Processing your request, please wait...")

    if message[0].lower() == "/spam" and len(message) == 3 and message[1].lower() == "bd":
        cmd = "spam"
        uid = message[2]
        api_url = f"https://momin-spam-api.vercel.app/send_requests?uid={uid}"
    elif message[0].lower() == "/like" and len(message) >= 3:
        cmd = "like"
        region = message[1].lower()
        uid = message[2]
        api_url = f"https://momin-api.vercel.app/like?uid={uid}&server_name={region}"
    else:
        await processing_msg.delete()
        await update.message.reply_text("❌ Invalid command or format! Use /like <server> <uid> or /spam bd <uid>")
        return

    # Cooldown check
    current_time = time.time()
    if user.id in user_last_used and current_time - user_last_used[user.id] < 30:
        remaining = int(30 - (current_time - user_last_used[user.id]))
        await processing_msg.delete()
        await update.message.reply_text(f"⏳ Please wait {remaining}s before next command.")
        return

    # Group verification with retry
    is_verified = await is_user_verified(context.bot, user.id)
    if not is_verified:
        await asyncio.sleep(2)
        is_verified = await is_user_verified(context.bot, user.id)
        
    if not is_verified:
        await processing_msg.delete()
        await update.message.reply_text(
            f"⚠️ {user.first_name}, please join our group first to use this bot!\n\n"
            f"If you've already joined, try clicking verify again after a few seconds.",
            reply_markup=verification_markup()
        )
        return

    user_last_used[user.id] = current_time

    try:
        # Make API request
        response = requests.get(api_url, timeout=25)
        response.raise_for_status()
        data = response.json()
        print(f"API Response: {data}")  # Debug logging

        # Delete processing message
        await processing_msg.delete()

        if cmd == "like":
            reply = (
                f"╭━❤️ LIKE REPORT ❤️━╮\n"
                f"👤 User: {user.first_name}\n"
                f"🎮 Nick: {data.get('PlayerNickname','N/A')}\n"
                f"🆔 UID: {data.get('UID','N/A')}\n"
                f"👍 Before: {data.get('LikesbeforeCommand',0)}\n"
                f"🔥 After: {data.get('LikesafterCommand',0)}\n"
                f"💖 Given By Owner: {data.get('LikesGivenBy@MominTip',0)}\n"
                f"🔗 Group: {GROUP_LINK}\n"
                f"👑 Owner: {OWNER_HANDLE}\n"
                f"╰━━━━━━━━━━━━╯"
            )
        elif cmd == "spam":
            # Get counts with proper fallback values
            success = data.get('success_count', data.get('success', 0))
            failed = data.get('failed_count', data.get('failed', 0))
            status = data.get('status', 0)
            
            # Convert to integers
            success = int(success) if str(success).isdigit() else 0
            failed = int(failed) if str(failed).isdigit() else 0
            
            # Status mapping
            status_messages = {
                0: "Pending",
                1: "Completed",
                2: "Processing",
                3: "Failed"
            }
            status_text = status_messages.get(status, f"Unknown ({status})")
            
            reply = (
                f"╭━ SPAM REPORT━╮\n"
                f"👤 User: {user.first_name}\n"
                f"🌎 Server: BD\n"
                f"🆔 UID: {uid}\n"
                f"✅ Success: {success}\n"
                f"❌ Failed: {failed}\n"
                f"📊 Total: {success + failed}\n"
                f"💬 Status: {status_text}\n"
                f"🔗 Group: {GROUP_LINK}\n"
                f"👑 Owner: {OWNER_HANDLE}\n"
                f"╰━━━━━━━━━━━━╯"
            )

        await update.message.reply_text(reply)

    except requests.exceptions.Timeout:
        await processing_msg.delete()
        await update.message.reply_text("⌛ Request timed out. The server is taking too long to respond.")
    except Exception as e:
        await processing_msg.delete()
        error_msg = (
            "😢 Service Temporary Unavailable\n\n"
            "Our servers are busy! Please try after some time.\n\n"
            f"For urgent help contact {OWNER_HANDLE}"
        )
        await update.message.reply_text(error_msg)
        print(f"API Error: {str(e)}")

async def verify_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # Double check with delay
        is_verified = await is_user_verified(context.bot, query.from_user.id)
        if not is_verified:
            await asyncio.sleep(2)
            is_verified = await is_user_verified(context.bot, query.from_user.id)

        if is_verified:
            await query.edit_message_text("✅ Verification successful! You can now use the bot commands.")
        else:
            await query.edit_message_text(
                "❌ Verification failed! Please ensure:\n"
                "1. You've properly joined the group\n"
                "2. You're not restricting the bot in privacy settings\n"
                "3. You wait a few seconds after joining\n\n"
                "Then try verifying again.",
                reply_markup=verification_markup()
            )
    except Exception as e:
        print(f"Verify button error: {e}")
        await query.edit_message_text(
            "⚠️ Verification failed due to technical error! Please try again later.",
            reply_markup=verification_markup()
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(["like", "spam"], handle_command))
    app.add_handler(CallbackQueryHandler(verify_button))
    print("🔥 Bot is running with corrected spam reporting...")
    app.run_polling()