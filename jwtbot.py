import os
import json
import requests
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = "7863909636:AAGn9hXb44ZxfK9_v3M0s4kL74fFYftPPeU"
JWT_URL = "https://momin-jwt.vercel.app/token"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to JWT Token Generator Bot!\n\n"
        "Send me a JSON file containing UID and password pairs, "
        "and I will generate JWT tokens for each pair.\n\n"
        "The JSON format should be:\n"
        '[{"uid": "123", "password": "abc"}, ...]\n\n'
        "Bot Owner: @MominTip\n"
        
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document

    if not document.file_name.endswith(".json"):
        await update.message.reply_text("Please upload a JSON file (.json extension)")
        return

    file = await context.bot.get_file(document.file_id)
    temp_file = NamedTemporaryFile(delete=False, suffix=".json")
    await file.download_to_drive(temp_file.name)

    try:
        with open(temp_file.name, "r", encoding="utf-8") as f:
            data = json.load(f)

        tokens = []
        success_count = 0
        failed_count = 0
        duplicate_count = 0
        seen_uids = set()

        await update.message.reply_text(f"⚡ Starting processing for {len(data)} UIDs...")

        for item in data:
            uid = item.get("uid")
            password = item.get("password")
            
            if not uid or not password:
                failed_count += 1
                await update.message.reply_text(f"❌ Missing UID or password in entry")
                continue

            if uid in seen_uids:
                duplicate_count += 1
                await update.message.reply_text(f"⚠️ Duplicate UID skipped: {uid}")
                continue
            
            seen_uids.add(uid)

            try:
                processing_msg = await update.message.reply_text(f"🔄 Processing UID: {uid}...")
                
                res = requests.get(JWT_URL, params={"uid": uid, "password": password})
                api_response = res.json()
                
                # Create response message with all API data
                response_msg = (
                    f"🔹 API Response for UID: {uid}\n"
                    f"Status Code: {res.status_code}\n"
                    "Full Response:\n"
                )
                
                # Add each API response field to the message
                for key, value in api_response.items():
                    response_msg += f"{key}: {value}\n"
                
                # Edit processing message to show complete response
                await context.bot.edit_message_text(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id,
                    text=response_msg
                )

                # If token exists in response, store it
                if res.ok and "token" in api_response:
                    tokens.append({"uid": uid, "token": api_response["token"]})
                    success_count += 1
                    await update.message.reply_text(f"✅ Token stored for UID: {uid}")
                else:
                    failed_count += 1
                    await update.message.reply_text(f"❌ No token received for UID: {uid}")
                    
            except Exception as e:
                failed_count += 1
                await update.message.reply_text(f"❌ Error processing UID: {uid}\n{str(e)}")
                continue

        # Generate final token file
        with NamedTemporaryFile("w+", delete=False, suffix=".json") as output:
            json.dump(tokens, output, indent=2)
            output.seek(0)
            
            # Send summary
            summary = (
                f"📊 Processing Complete!\n\n"
                f"✅ Successful: {success_count}\n"
                f"❌ Failed: {failed_count}\n"
                f"🔁 Duplicates: {duplicate_count}\n\n"
                f"💾 Token file contains {len(tokens)} tokens:"
            )
            
            await update.message.reply_text(summary)
            await update.message.reply_document(
                document=open(output.name, "rb"),
                filename="jwt_tokens.json",
                caption=f"Generated {success_count} JWT tokens"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Bot error: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("An error occurred. Please try again.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()