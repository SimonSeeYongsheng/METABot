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
FILE_DRIVE = os.environ.get("FILE_DRIVE")

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
    telegram_handle = update.effective_user.username

    # Check if user is authenticated
    if not db.is_user_authenticated(user_id):

        await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
        return
    
    user_message = update.message.text

    logging.info(f"Message received: {user_message}")

    response = await llm.response_message(message=user_message, user_id=user_id)
    await context.bot.send_message(chat_id=user_id, text=response)


# Handler for receiving document and logging chat hist
async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    # Check if user is authenticated
    if not db.is_user_authenticated(user_id):

        await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
        return
    
    document = update.message.document
    caption = update.message.caption

    file_name = document.file_name
    file_size = document.file_size


    logging.info(f"Document received: {file_name}, size: {file_size} bytes")

    # Process the document (e.g., download and respond)
    if file_name.endswith('.pdf'):
        file = await update.message.effective_attachment.get_file()
        file_path = await file.download_to_drive(custom_path=os.path.join(FILE_DRIVE, file_name))
        logging.info(f"File downloaded: {file_path}")
        await llm.load_document(file_path=file_path)
        await context.bot.send_message(chat_id=user_id, text=f"PDF downloaded: {file_name}")

        if caption:
            response = await llm.response_message(message=caption, user_id=user_id)
            await context.bot.send_message(chat_id=user_id, text=response)

    else:
        await context.bot.send_message(chat_id=user_id, text="Unsupported file type received.")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
    document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), document)

    application.add_handler(start_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)

    application.run_polling()