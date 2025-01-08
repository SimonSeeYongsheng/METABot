# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
import asyncio
import nest_asyncio
nest_asyncio.apply()

import schedule
import time
import threading

import logging
from telegram import Update, BotCommand
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

import llm_module # module for the LLM

import chat_database # module for the chat database
import docs_database # module for the doc database

load_dotenv() # Load environment variables from .env file

TELE_BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')
FILE_DRIVE = os.environ.get("FILE_DRIVE")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

chat_db = chat_database.Chat_DB()
doc_db = docs_database.Docs_DB(Chat_Database=chat_db)
llm = llm_module.LLM(Chat_Database=chat_db, Docs_Database=doc_db)

scheduled_clear_time = "04:00"



start_message = (
    "👋 *Welcome to METABot!*\n\n"
    "Here’s what you can do:\n\n"
    "📜 */start*: Open the information menu to learn more about how to use the bot.\n"
    "🆕 */new*: Start a new conversation.\n"
    "🗑️ */clear_docs*: Clear any uploaded documents.\n"
    "📊 */analyse*: For students, this analyses your learning behaviour and provides personalized insights.\n"
    "🧑‍🏫 */analyse [nusnet_id]* to view your student’s learning behaviour *(for teachers only)*.\n"
    "📝 */rollcall*: Get updates about the lab group *(for teachers only)*.\n\n"
    "You can upload your learning materials, then start chatting to:\n"
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
        BotCommand("rollcall", "Get updates about the lab group (for teachers only)"),
    ]
    await bot.set_my_commands(commands)

# Handler for /start command to authenticate users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    logging.info(f"Authenticating: {telegram_handle}")


    if chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle ):

        #await context.bot.send_message(chat_id=user_id, text="Absolutely\\!", parse_mode="MarkdownV2")
        await context.bot.send_message(chat_id=user_id, text=start_message, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=user_id, text="You have not been authenticated to use this Chatbot!")

# Handler for /new command to start a new conversation
async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    nusnet_id = chat_db.get_nusnet_id(user_id=user_id)

    chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
    await context.bot.send_message(chat_id=user_id, text="A new conversation has started")

# Handler for /clear_documents command to clear documents in vectorstores
async def clear_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
    telegram_handle = update.effective_user.username

    # Check if user is authenticated
    if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):

        await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
        return

    llm.clear_documents(nusnet_id=nusnet_id)
    await context.bot.send_message(chat_id=user_id, text="Documents cleared!")

# Handler for /analyse command to analyse learning behaviour
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    user_nusnet_id = chat_db.get_nusnet_id(user_id)

    user_message = user_nusnet_id if len(context.args) == 0 else context.args[0].upper()

    if chat_db.is_admin(user_id=user_id) and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await context.bot.send_message(chat_id=user_id, text=response)

    elif user_nusnet_id == user_message and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await context.bot.send_message(chat_id=user_id, text=response)
    
    else:

        await context.bot.send_message(chat_id=user_id, text="User is unauthorised")



# Handler for receiving messages and logging chat history
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
    telegram_handle = update.effective_user.username

    keyboard = [
        [
            InlineKeyboardButton("👎", callback_data='dislike'),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if user is authenticated
    if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):

        await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
        return
    
    user_message = update.message.text

    logging.info(f"Message received: {user_message}")

    most_recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
    conversation_id = most_recent_convo if most_recent_convo  else 1

    response = await llm.response_message(message=user_message, nusnet_id=nusnet_id , conversation_id=conversation_id)
    logging.info(f"Message sent: {response}")
    await context.bot.send_message(chat_id=user_id, text=response, reply_markup=reply_markup)


# Handler for receiving document and logging chat hist
async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_chat.id
        nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
        telegram_handle = update.effective_user.username

        keyboard = [
            [
                InlineKeyboardButton("👎", callback_data='dislike'),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Check if user is authenticated
        if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
            await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
            return

        document = update.message.document

        if not document:
            await context.bot.send_message(chat_id=user_id, text="No document found in the message.")
            return

        caption = update.message.caption

        file_name = document.file_name
        file_size = document.file_size

        # Log the received document details
        logging.info(f"Document received: {file_name}, size: {file_size} bytes")

        # Download the document
        try:
            file = await update.message.effective_attachment.get_file()
            file_path = await file.download_to_drive(custom_path=os.path.join(FILE_DRIVE, file_name))
            logging.info(f"File downloaded: {file_path}")
        except Exception as e:
            logging.error(f"Error downloading file: {e}")
            await context.bot.send_message(chat_id=user_id, text="Failed to download the document. Please try again.")
            return

        # Extract file type
        try:
            _, file_extension = os.path.splitext(file_path)
            file_type = file_extension.lstrip(".").upper()
        except Exception as e:
            logging.error(f"Error extracting file type: {e}")
            await context.bot.send_message(chat_id=user_id, text="Failed to determine the file type. Please check the file and try again.")
            return

        # Process the document
        try:
            await llm.load_document(file_path=file_path, nusnet_id=nusnet_id, file_type=file_type)
            await context.bot.send_message(chat_id=user_id, text=f"{file_type} document successfully processed: {file_name}")
        except Exception as e:
            logging.error(f"Error processing document: {e}")
            await context.bot.send_message(chat_id=user_id, text="Failed to process the document. Please try again later.")
            return

        # Handle caption if provided
        if caption:
            try:
                most_recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
                conversation_id = most_recent_convo if most_recent_convo else 1
                response = await llm.response_message(message=caption, nusnet_id=nusnet_id, conversation_id=conversation_id)
                await context.bot.send_message(chat_id=user_id, text=response, reply_markup=reply_markup)
            except Exception as e:
                logging.error(f"Error handling caption response: {e}")
                await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your caption. Please try again.")

    except Exception as e:
        logging.error(f"Unexpected error in document handler: {e}")
        await context.bot.send_message(chat_id=user_id, text="An unexpected error occurred. Please try again later.")

# async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):

#     user_id = update.effective_chat.id
#     nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
#     telegram_handle = update.effective_user.username

#     keyboard = [
#         [
#             InlineKeyboardButton("👎", callback_data='dislike'),
#         ]
#     ]

#     reply_markup = InlineKeyboardMarkup(keyboard)

#     # Check if user is authenticated
#     if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):

#         await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
#         return
    
#     document = update.message.document
#     caption = update.message.caption

#     file_name = document.file_name
#     file_size = document.file_size

#     file = await update.message.effective_attachment.get_file()
#     file_path = await file.download_to_drive(custom_path=os.path.join(FILE_DRIVE, file_name))
#     logging.info(f"File downloaded: {file_path}")
#     logging.info(f"Document received: {file_name}, size: {file_size} bytes")

#     _, file_extension = os.path.splitext(file_path)
#     # Extract file type (without the leading dot)
#     file_type = file_extension.lstrip(".").upper()


#     # Process the document (e.g., download and respond)
#     await llm.load_document(file_path=file_path, nusnet_id=nusnet_id, file_type=file_type)

#     await context.bot.send_message(chat_id=user_id, text=f"{file_type} downloaded: {file_name}")

#     if caption:

#         most_recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
#         conversation_id = most_recent_convo if most_recent_convo else 1
#         response = await llm.response_message(message=caption, nusnet_id=nusnet_id, conversation_id=conversation_id)
#         await context.bot.send_message(chat_id=user_id, text=response, reply_markup=reply_markup)

# Handler for rollcall of lab group
async def rollcall(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    if chat_db.is_admin(user_id=user_id):

        lab_group = chat_db.get_lab_group(user_id=user_id)
        students = chat_db.get_lab_students(lab_group=lab_group)

        logging.info(f"Rollcall: {lab_group}")

        await context.bot.send_message(chat_id=user_id, text="Rollcall...give me a moment...")

        for student in students:

            student_nusnet_id = student["nusnet_id"]

            response = await llm.rollcall_message(nusnet_id=student_nusnet_id)

            await context.bot.send_message(chat_id=user_id, text=response)

    else:

        await context.bot.send_message(chat_id=user_id, text="User is unauthorised")


async def handle_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat.id  # Fetch user ID from the query
    nusnet_id = chat_db.get_nusnet_id(user_id=user_id)  # Get user's NUSNET ID from the database
   
    # Acknowledge the callback query
    await query.answer()

    await context.bot.send_message(chat_id=user_id, text="We apologise for the error. The recent conversation will be forwarded to the TA for review. 🙏")

    instructors = chat_db.get_instructors(user_id=user_id)
    message_id = query.message.message_id

    for instructor_user_id in instructors:

        await context.bot.forward_message(
            chat_id=instructor_user_id,
            from_chat_id=user_id,
            message_id=(message_id - 1)
            )

        await context.bot.forward_message(
            chat_id=instructor_user_id,
            from_chat_id=user_id,
            message_id=message_id
            )
        
    await context.bot.send_message(chat_id=user_id, text="We are saving the conversation for review and starting a new conversation... 📝")
    recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
    chat_db.input_feedback(nusnet_id=nusnet_id, conversation_id=recent_convo,message=query.message.text)

    chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
    await context.bot.send_message(chat_id=user_id, text="A new conversation has started")

def clear_all_docs():

    logging.info(f"Scheduled documents clearance")
    doc_db.clear_all_docs()


def run_scheduler():
    # Schedule the async task
    schedule.every().day.at(scheduled_clear_time).do(clear_all_docs)
    print("Scheduler started. Waiting for tasks to execute...")
    while True:
        schedule.run_pending()
        time.sleep(1)







async def main():

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Build the bot application
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    new_convo_handler = CommandHandler('new', new)
    clear_document_handler = CommandHandler("clear_docs", clear_docs)
    analyse_handler = CommandHandler("analyse", analyse)
    rollcall_handler = CommandHandler("rollcall", rollcall)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
    document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), document)
    reaction_handler = CallbackQueryHandler(handle_reactions)

    application.add_handler(reaction_handler)
    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(clear_document_handler)
    application.add_handler(analyse_handler)
    application.add_handler(rollcall_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)
    application.add_handler(reaction_handler)

    # Set menu commands
    await set_command_menu(application.bot)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())