import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your API URL
API_URL = "https://api-momin.vercel.app/api/player-info?id="

# Telegram Bot Token
TOKEN = "7575218993:AAGAke-M1DMuQXMJ7VZixdSA-OOIl2SpqKQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_markdown_v2(
        fr"Hi {user.mention_markdown_v2()}\! "
        "I can fetch Free Fire player information\.\n"
        "Use `/get <uid>` to get player info\n"
        "Example: `/get 2315238174`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Help", callback_data='help')]
        ])
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 *Free Fire Player Info Bot*

*Available Commands:*
/start - Start the bot
/get <uid> - Get player info (e.g. /get 2315238174)
/help - Show this help message

*How to Use:*
1. Find a Free Fire player ID
2. Send command like `/get 2315238174`
3. Get detailed player information

*API Credits:* @MominTip
"""
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown')

async def get_player_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch player info from API and send to user."""
    try:
        # Check if player ID is provided
        if not context.args:
            await update.message.reply_text("Please provide a player ID. Example: /get 2315238174")
            return

        player_id = context.args[0]
        
        # Show "Fetching..." message
        message = await update.message.reply_text("🔄 Fetching player info...")
        
        # Make API request
        response = requests.get(API_URL + player_id)
        data = response.json()
        
        if data.get('status') != 'success':
            await message.edit_text("❌ Error: Could not fetch player info. Please check the player ID.")
            return
            
        player_data = data['account_data']['player_info']
        
        # Format the response with all available details
        text = f"""
🎮 *Player Information* 🎮

👤 *Nickname:* `{player_data.get('player_nickname', 'N/A')}`
🆔 *Player ID:* `{player_data.get('player_id', 'N/A')}`
⭐ *Level:* `{player_data.get('account_level', 0)}`
❤️ *Likes:* `{player_data.get('profile_likes', 0)}`
🌍 *Server:* `{player_data.get('account_server', 'N/A')}`
📜 *Bio:* `{player_data.get('player_bio', 'N/A')}`
🎟️ *Booyah Pass Level:* `{player_data.get('booyah_pass_level', 0)}`
🏆 *CS Rank:* `{player_data.get('cs_rank', 'N/A')}`

🖼️ *Profile:*
   🏳️ *Banner ID:* `{player_data.get('account_banner', 0)}`
   👤 *Avatar ID:* `{player_data.get('account_avtar', 0)}`

⚔️ *BR Stats:*
   🏅 *Max Rank:* `{player_data.get('BR-Max_rank', 0)}`
   📊 *Rank Points:* `{player_data.get('BR-rank_point', 0)}`

🔢 *Other IDs:*
   *BPID:* `{player_data.get('account_BPID', 0)}`
   *Season ID:* `{player_data.get('account_seson_id', 0)}`

📅 *Account Created:* `{player_data.get('account_created', 'N/A')}`
⏱️ *Last Updated:* `{data.get('timestamp', 'N/A')}`

*API Credits:* @MominTip
*🙈 If You Need JWT Token Generator Then Get This Bot:* [@JWTTOKENBOT](https://t.me/JWTTOKENBOT)
"""
        # Add guild info if available
        if data['account_data'].get('Guild'):
            guild = data['account_data']['Guild']
            text += f"""
👥 *Guild Info:*
   🏰 *Name:* `{guild.get('name', 'N/A')}`
   📛 *ID:* `{guild.get('guild id', 'N/A')}`
   � *Level:* `{guild.get('guild level', 0)}`
   👥 *Members:* `{guild.get('members_count', 0)}`
   
👑 *Guild Leader:*
   👤 `{guild['guild_leader_info'].get('nickname', 'N/A')}`
   🆔 `{guild['guild_leader_info'].get('uid', 'N/A')}`
   ⭐ Level `{guild['guild_leader_info'].get('account_level', 0)}`
   🎟️ Booyah Pass `{guild['guild_leader_info'].get('booyah_pass_level', 0)}`
   ❤️ Likes `{guild['guild_leader_info'].get('account_likes', 0)}`
   📅 Created `{guild['guild_leader_info'].get('account_created', 'N/A')}`
"""
        # Edit the original message with the results
        await message.edit_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in get_player_info: {e}")
        await update.message.reply_text("❌ An error occurred while fetching player info. Please try again later.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'help':
        await help_command(update, context)

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("get", get_player_info))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()