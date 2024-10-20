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

    logging.info(f"Authenticating: {telegram_handle}")


    if db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle ):
        await context.bot.send_message(chat_id=user_id, text="Welcome back!")
    else:
        await context.bot.send_message(chat_id=user_id, text="You have not been authenticated to use this Chatbot!")

# Handler for /new command to start a new conversation
async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    nusnet_id = db.get_nusnet_id(user_id=user_id)

    db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
    await context.bot.send_message(chat_id=user_id, text="A new conversation has started")

# Handler for /clear_documents command to clear documents in vectorstores
async def clear_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    nusnet_id = db.get_nusnet_id(user_id=user_id)

    if db.is_admin(user_id=user_id):
        await llm.global_clear_documents()
    else:
        await llm.clear_documents(nusnet_id=nusnet_id)


# Handler for receiving messages and logging chat history
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    nusnet_id = db.get_nusnet_id(user_id=user_id)
    telegram_handle = update.effective_user.username

    # Check if user is authenticated
    if not db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):

        await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
        return
    
    user_message = update.message.text

    logging.info(f"Message received: {user_message}")

    most_recent_convo = db.get_recent_conversation(nusnet_id=nusnet_id)
    conversation_id = most_recent_convo if most_recent_convo  else 1

    response = await llm.response_message(message=user_message, nusnet_id=nusnet_id , conversation_id=conversation_id)
    logging.info(f"Message sent: {response}")
    await context.bot.send_message(chat_id=user_id, text=response)


# Handler for receiving document and logging chat hist
async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    nusnet_id = db.get_nusnet_id(user_id=user_id)
    telegram_handle = update.effective_user.username

    # Check if user is authenticated
    if not db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):

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

        if db.is_admin(user_id=user_id):
            await llm.global_load_document(file_path=file_path)
        else:
            await llm.load_document(file_path=file_path, nusnet_id=nusnet_id)

        await context.bot.send_message(chat_id=user_id, text=f"PDF downloaded: {file_name}")

        if caption:

            most_recent_convo = db.get_recent_conversation(nusnet_id=nusnet_id)
            conversation_id = most_recent_convo if most_recent_convo else 1
            response = await llm.response_message(message=caption, nusnet_id=nusnet_id, conversation_id=conversation_id)
            await context.bot.send_message(chat_id=user_id, text=response)

    else:
        await context.bot.send_message(chat_id=user_id, text="Unsupported file type received.")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    new_convo_handler = CommandHandler('new', new)
    clear_document_handler = CommandHandler("clear_docs", clear_docs)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
    document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), document)

    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(clear_document_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)

    application.run_polling()