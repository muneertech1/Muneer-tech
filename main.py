import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import sqlite3

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your bot token
TOKEN = '8528177960:AAH2SQEPxHR2CVG-TbhXkhGQDjjht3Vl9ZU'
ADMIN_ID = 7447997014  # Admin ID

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        joined_channels TEXT,
                        referral_confirmed INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
                        channel_id INTEGER PRIMARY KEY,
                        channel_name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ref_bots (
                        ref_id INTEGER PRIMARY KEY,
                        ref_link TEXT)''')
    conn.commit()
    conn.close()

# Add a new channel to the database
def add_channel_to_db(channel_name):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO channels (channel_name) VALUES (?)', (channel_name,))
    conn.commit()
    conn.close()

# Add a new referral bot link
def add_ref_bot(ref_link):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ref_bots (ref_link) VALUES (?)', (ref_link,))
    conn.commit()
    conn.close()

# Get all required channels
def get_required_channels():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels')
    channels = cursor.fetchall()
    conn.close()
    return [channel[1] for channel in channels]

# Check if a user has joined all required channels
def check_channels(user_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user and user[1] == '1' and user[2] == 1:
        return True
    return False

# Handle the /start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Welcome to the Telegram File Distribution Bot! Join the required channels and confirm the referral link to receive files."
    )

# Handle the /files command
def files(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if check_channels(user_id):
        update.message.reply_text("You have completed the requirements! Here are your files:")
        # Send files (replace with actual file path)
        update.message.reply_document("path/to/your/file")
    else:
        required_channels = get_required_channels()
        keyboard = [[InlineKeyboardButton(f"Join {channel}", url=f"t.me/{channel}") for channel in required_channels]]
        keyboard.append([InlineKeyboardButton("Confirm Referral", callback_data='confirm_referral')])
        update.message.reply_text(
            "Please join the following channels and confirm your referral:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Handle referral confirmation
def confirm_referral(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        cursor.execute('UPDATE users SET referral_confirmed = 1 WHERE user_id = ?', (user_id,))
    else:
        cursor.execute('INSERT INTO users (user_id, joined_channels, referral_confirmed) VALUES (?, ?, ?)',
                       (user_id, '1', 1))  # Assuming channels joined and referral confirmed
    conn.commit()
    conn.close()
    
    update.callback_query.answer()
    update.callback_query.edit_message_text("Referral confirmed! You can now request files using /files.")

# Admin commands to add/remove channels
def add_channel(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == ADMIN_ID:
        if context.args:
            channel_name = context.args[0]
            add_channel_to_db(channel_name)
            update.message.reply_text(f"Channel {channel_name} added to the required channels list.")
        else:
            update.message.reply_text("Please provide the channel name.")
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Admin command to add a referral bot link
def add_refbot(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == ADMIN_ID:
        if context.args:
            ref_link = context.args[0]
            add_ref_bot(ref_link)
            update.message.reply_text(f"Referral bot link {ref_link} added.")
        else:
            update.message.reply_text("Please provide the referral bot link.")
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Main function to run the bot
def main():
    # Initialize database
    init_db()

    # Create an Updater object and pass the bot token
    updater = Updater(TOKEN)

    # Get the dispatcher
    dispatcher = updater.dispatcher

    # Command Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("files", files))
    dispatcher.add_handler(CommandHandler("addchannel", add_channel))
    dispatcher.add_handler(CommandHandler("addrefbot", add_refbot))

    # Callback query handler for referral confirmation
    dispatcher.add_handler(CallbackQueryHandler(confirm_referral, pattern='^confirm_referral$'))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
