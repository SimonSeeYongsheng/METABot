# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
import asyncio
import nest_asyncio
nest_asyncio.apply()
import logging
from telegram import Update, BotCommand
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


start_message = (
    "👋 *Welcome to METABot!*\n\n"
    "Here’s what you can do:\n\n"
    "📜 */start*: Open the information menu to learn more about how to use the bot.\n"
    "🆕 */new*: Start a new conversation.\n"
    "🗑️ */clear_docs*: Clear any uploaded documents.\n"
    "📊 */analyse*: For students, this analyses your learning behaviour and provides personalized insights.\n"
    "🧑‍🏫 */analyse [nusnet_id]* to view your student’s learning behaviour (for teachers only).\n"
    "📝 */rollcall*: Get updates about the lab group (for teachers only).\n\n"
    "You can upload your learning materials (PDF format only), then start chatting to:\n"
    "📚 *Teach content*: Dive into the material and learn interactively.\n"
    "💡 *Ask for guidance*: Get help understanding concepts or solving problems.\n\n"
    "I’m here to assist you in your learning journey! 😊"
)

# Set command menu
async def set_command_menu(bot):
    commands = [
        BotCommand("start", "Open the information menu"),
        BotCommand("new", "Start a new conversation"),
        BotCommand("clear_docs", "Clear uploaded documents"),
        BotCommand("analyse", "Analyse learning behaviour (/analyse [nusnet_id] for teachers only)"),
        BotCommand("rollcall", "Get updates about the lab group for teachers only"),
    ]
    await bot.set_my_commands(commands)

# Handler for /start command to authenticate users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    logging.info(f"Authenticating: {telegram_handle}")


    if db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle ):
        await context.bot.send_message(chat_id=user_id, text=start_message)
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

# Handler for /analyse command to analyse learning behaviour
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    user_nusnet_id = db.get_nusnet_id(user_id)

    user_message = user_nusnet_id if len(context.args) == 0 else context.args[0].upper()

    if db.is_admin(user_id=user_id) and db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await context.bot.send_message(chat_id=user_id, text=response)

    elif user_nusnet_id == user_message and db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await context.bot.send_message(chat_id=user_id, text=response)
    
    else:

        await context.bot.send_message(chat_id=user_id, text="User is unauthorised")



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

# Handler for rollcall of lab group
async def rollcall(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    if db.is_admin(user_id=user_id):

        lab_group = db.get_lab_group(user_id=user_id)
        students = db.get_lab_students(lab_group=lab_group)

        logging.info(f"Rollcall: {lab_group}")

        await context.bot.send_message(chat_id=user_id, text="Rollcall...give me a moment...")

        for student in students:

            student_nusnet_id = student["nusnet_id"]

            response = await llm.rollcall_message(nusnet_id=student_nusnet_id)

            await context.bot.send_message(chat_id=user_id, text=response)

    else:

        await context.bot.send_message(chat_id=user_id, text="User is unauthorised")








async def main():
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    new_convo_handler = CommandHandler('new', new)
    clear_document_handler = CommandHandler("clear_docs", clear_docs)
    analyse_handler = CommandHandler("analyse", analyse)
    rollcall_handler = CommandHandler("rollcall", rollcall)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
    document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), document)

    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(clear_document_handler)
    application.add_handler(analyse_handler)
    application.add_handler(rollcall_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)

    # Set menu commands
    await set_command_menu(application.bot)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())