# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

import llm_module # module for the LLM

import database_module # module for the database

load_dotenv() # Load environment variables from .env file

TELE_BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

llm = llm_module.LLM()
db = database_module.DB()

# Handler for /start command to authenticate users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    if db.is_user_authenticated(user_id):
        await context.bot.send_message(chat_id=user_id, text="Welcome back!")
    else:
        db.authenticate_user(user_id, telegram_handle)
        await context.bot.send_message(chat_id=user_id, text="You have been authenticated successfully!")


# Handler for receiving messages and logging chat history
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_message = update.message.text
    telegram_handle = update.effective_user.username

    # Check if user is authenticated before responding
    if not db.is_user_authenticated(user_id):
        await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
        return

    # Get LLM response and log the chat history
    response = llm.response(user_message)
    db.log_chat(user_id, telegram_handle, user_message, response)

    await context.bot.send_message(chat_id=user_id, text=response)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()