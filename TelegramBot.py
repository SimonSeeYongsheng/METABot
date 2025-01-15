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

from datetime import datetime

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
    "📝 */sitrep*: Get updates about the lab group *(for teachers only)*.\n"
    "📁 */export*: Export the chat history to a file *(for teachers only)*.\n\n"
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
        BotCommand("sitrep", "Get updates about the lab group (for teachers only)"),
        BotCommand("export", "Export chat history (for teachers only)"),
    ]
    await bot.set_my_commands(commands)

# Handler for /start command to authenticate users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    logging.info(f"Authenticating user: {telegram_handle} (User ID: {user_id})")

    try:
        # Check if the user is authenticated
        if chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
            logging.info(f"User {telegram_handle} (User ID: {user_id}) authenticated successfully.")
            try:
                await context.bot.send_message(chat_id=user_id, text=start_message, parse_mode="Markdown")
            except Exception as send_error:
                logging.error(f"Error sending authentication success message to user {user_id}: {send_error}")
                await context.bot.send_message(chat_id=user_id, text="An error occurred while sending the welcome message. Please try again later.")
        else:
            logging.warning(f"User {telegram_handle} (User ID: {user_id}) failed authentication.")
            try:
                await context.bot.send_message(chat_id=user_id, text="You have not been authenticated to use this Chatbot!")
            except Exception as send_error:
                logging.error(f"Error sending authentication failure message to user {user_id}: {send_error}")
    except Exception as auth_error:
        logging.error(f"Error during authentication process for user {user_id}: {auth_error}")
        try:
            await context.bot.send_message(chat_id=user_id, text="An error occurred during authentication. Please try again later.")
        except Exception as send_error:
            logging.error(f"Error sending fallback error message to user {user_id}: {send_error}")


# Handler for /new command to start a new conversation
async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    try:
        # Retrieve user's NUSNET ID
        nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
    except Exception as db_error:
        logging.error(f"Error retrieving NUSNET ID for user {user_id}: {db_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while starting a new conversation. Please try again later.")
        return

    try:
        # Start a new conversation
        chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
        await context.bot.send_message(chat_id=user_id, text="A new conversation has started.")
        logging.info(f"New conversation started for user {user_id} (NUSNET ID: {nusnet_id}).")
    except Exception as start_error:
        logging.error(f"Error starting a new conversation for NUSNET ID {nusnet_id}: {start_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while starting a new conversation. Please try again later.")


# Handler for /clear_documents command to clear documents in vectorstores
async def clear_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    try:
        # Retrieve user's NUSNET ID
        nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
    except Exception as db_error:
        logging.error(f"Error retrieving NUSNET ID for user {user_id}: {db_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred. Please try again later.")
        return

    # Check if user is authenticated
    try:
        if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
            await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
            return
    except Exception as auth_error:
        logging.error(f"Authentication error for user {user_id}: {auth_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred during authentication. Please try again later.")
        return

    # Attempt to clear documents
    try:
        llm.clear_documents(nusnet_id=nusnet_id)
        await context.bot.send_message(chat_id=user_id, text="Documents cleared!")
        logging.info(f"Documents cleared successfully for user {user_id} (NUSNET ID: {nusnet_id}).")
    except Exception as clear_error:
        logging.error(f"Error clearing documents for NUSNET ID {nusnet_id}: {clear_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while clearing documents. Please try again later.")


# Handler for /analyse command to analyse learning behaviour
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    user_nusnet_id = chat_db.get_nusnet_id(user_id)

    user_message = user_nusnet_id if len(context.args) == 0 else context.args[0].upper()

    if chat_db.is_admin(user_id=user_id) and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await context.bot.send_message(chat_id=user_id, text=response, parse_mode="Markdown")

    elif user_nusnet_id == user_message and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await context.bot.send_message(chat_id=user_id, text=response, parse_mode="Markdown")
    
    else:

        await context.bot.send_message(chat_id=user_id, text="User is unauthorised")



# Handler for receiving messages and logging chat history
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    try:
        # Retrieve user's NUSNET ID
        nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
    except Exception as db_error:
        logging.error(f"Error retrieving NUSNET ID for user {user_id}: {db_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred. Please try again later.")
        return

    # Check if user is authenticated
    try:
        if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
            await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
            return
    except Exception as auth_error:
        logging.error(f"Authentication error for user {user_id}: {auth_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred during authentication. Please try again later.")
        return
    
    recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
    metadata = f"{recent_convo}|{{message_count}}"
    user_message = update.message.text
    logging.info(f"Message received from user {user_id}: {user_message}")

    try:
        # Retrieve most recent conversation ID
        most_recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
        conversation_id = most_recent_convo if most_recent_convo else 1
    except Exception as convo_error:
        logging.error(f"Error retrieving recent conversation for NUSNET ID {nusnet_id}: {convo_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your conversation history. Please try again later.")
        return

    try:
        # Get response from LLM
        response = await llm.response_message(message=user_message, nusnet_id=nusnet_id, conversation_id=conversation_id)
    except Exception as llm_error:
        logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
        return

    # Split the string into parts using triple backticks
    parts = response.split("```")

    for i, part in enumerate(parts):

        text = part.strip()

        if i % 2 == 0:  # Even index: plain text
            keyboard = [
                [
            InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 1)),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
            except Exception as send_error:
                logging.error(f"Error sending part of the message: {send_error}")
                await context.bot.send_message(chat_id=user_id, text="Error: Message is too long", reply_markup=reply_markup)

        else:  # Odd index: code block

            keyboard = [
                [
            InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 1)),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(chat_id=user_id, text=f"```{text}```", reply_markup=reply_markup, parse_mode="Markdown")
            except Exception as send_error:
                logging.error(f"Error sending part of the message: {send_error}")
                await context.bot.send_message(chat_id=user_id, text="Error: Code block is too long", reply_markup=reply_markup)
                
    logging.info(f"Message sent to user {user_id}: {response}")


# Handler for receiving document and logging chat hist
async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_chat.id
        nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
        telegram_handle = update.effective_user.username

        # Check if user is authenticated
        if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
            await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
            return

        document = update.message.document
        recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
        metadata = f"{recent_convo}|{{message_count}}"

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

                # Split the string into parts using triple backticks
                parts = response.split("```")

                for i, part in enumerate(parts):

                    text = part.strip()

                    if i % 2 == 0:  # Even index: plain text

                        keyboard = [
                            [
                        InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 2)),
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        try:
                            await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
                        except Exception as send_error:
                            logging.error(f"Error sending part of the message: {send_error}")
                            await context.bot.send_message(chat_id=user_id, text="Error: Message is too long", reply_markup=reply_markup)

                    else:  # Odd index: code block

                        keyboard = [
                            [
                        InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 2)),
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        try:
                            await context.bot.send_message(chat_id=user_id, text=f"```{text}```", reply_markup=reply_markup, parse_mode="Markdown")
                        except Exception as send_error:
                            logging.error(f"Error sending part of the message: {send_error}")
                            await context.bot.send_message(chat_id=user_id, text="Error: Code block is too long", reply_markup=reply_markup)

            except Exception as e:
                logging.error(f"Error handling caption response: {e}")
                await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your caption. Please try again.")

    except Exception as e:
        logging.error(f"Unexpected error in document handler: {e}")
        await context.bot.send_message(chat_id=user_id, text="An unexpected error occurred. Please try again later.")

# Handler for sitrep of lab group
async def sitrep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    try:
        # Check if the user is an admin
        if not chat_db.is_admin(user_id=user_id):
            logging.warning(f"Unauthorized sitrep attempt by user {user_id}.")
            await context.bot.send_message(chat_id=user_id, text="User is unauthorised.")
            return
    except Exception as admin_check_error:
        logging.error(f"Error checking admin status for user {user_id}: {admin_check_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while checking authorization. Please try again later.")
        return

    try:
        # Get the lab group associated with the user
        lab_group = chat_db.get_lab_group(user_id=user_id)
    except Exception as lab_group_error:
        logging.error(f"Error retrieving lab group for user {user_id}: {lab_group_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your lab group. Please try again later.")
        return

    try:
        # Get the list of students in the lab group
        students = chat_db.get_lab_students(lab_group=lab_group)
        logging.info(f"Sitrep initiated for lab group {lab_group} by user {user_id}.")
        await context.bot.send_message(chat_id=user_id, text="Sitrep...give me a moment...")
    except Exception as student_fetch_error:
        logging.error(f"Error retrieving students for lab group {lab_group}: {student_fetch_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving student data. Please try again later.")
        return

    # Process each student in the lab group
    for student in students:
        student_nusnet_id = student["nusnet_id"]
        try:
            # Get sitrep response for each student
            response = await llm.sitrep_message(nusnet_id=student_nusnet_id)
            try:
                await context.bot.send_message(chat_id=user_id, text=response, parse_mode="Markdown")
            except Exception as message_send_error:
                logging.error(f"Error sending sitrep message for student {student_nusnet_id}: {message_send_error}")
                await context.bot.send_message(chat_id=user_id, text=f"Error: Unable to send sitrep message for student {student_nusnet_id}.")
        except Exception as sitrep_error:
            logging.error(f"Error generating sitrep message for student {student_nusnet_id}: {sitrep_error}")
            await context.bot.send_message(chat_id=user_id, text=f"Error: Unable to process sitrep for student {student_nusnet_id}.")

    logging.info(f"Sitrep completed for lab group {lab_group}.")


# Handler for handling reactions to chatbot response
async def handle_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat.id  # Fetch user ID from the query
    callback_data = query.data  # Retrieve the callback data

    # Acknowledge the callback query
    try:
        await query.answer()
        metadata_parts = callback_data.split("|")
        convo_id = int(metadata_parts[0])
        user_message = int(metadata_parts[1])
    except Exception as query_error:
        logging.error(f"Error acknowledging callback query for user {user_id}: {query_error}")

    # Retrieve user's NUSNET ID
    try:
        nusnet_id = chat_db.get_nusnet_id(user_id=user_id)  # Get user's NUSNET ID from the database
    except Exception as db_error:
        logging.error(f"Error retrieving NUSNET ID for user {user_id}: {db_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your data. Please try again later.")
        return
    

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="We apologise for the error. The recent conversation will be forwarded to the TA for review. 🙏"
        )
    except Exception as send_error:
        logging.error(f"Error sending apology message to user {user_id}: {send_error}")

    try:
        instructors = chat_db.get_instructors(user_id=user_id)
    except Exception as db_error:
        logging.error(f"Error retrieving instructors for user {user_id}: {db_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while fetching instructor information. Please try again later.")
        return

    message_id = query.message.message_id

    for instructor_user_id in instructors:
        try:
            # Forward the most recent messages to instructors
            forwarded_message = await context.bot.forward_message(
                chat_id=instructor_user_id,
                from_chat_id=user_id,
                message_id=(message_id - user_message)
            )
            await context.bot.forward_message(
                chat_id=instructor_user_id,
                from_chat_id=user_id,
                message_id=message_id
            )
        except Exception as forward_error:
            logging.error(f"Error forwarding message to instructor {instructor_user_id} from user {user_id}: {forward_error}")
        
    try:
        prompt = forwarded_message.text if forwarded_message.text else forwarded_message.caption
        chat_db.input_feedback(nusnet_id=nusnet_id, conversation_id=convo_id,message=query.message.text,prompt=prompt)
        
        await context.bot.send_message(chat_id=user_id, text="Conversation has been saved for review. 📝")

    except Exception as send_error:
        logging.error(f"Error sending review and restart message to user {user_id}: {send_error}")

# Handler for handling chat history export
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command to export the chat collection."""
    user_id = update.effective_chat.id
    file_path = f"chat_history_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    try:
        # Check if the user is an admin
        if not chat_db.is_admin(user_id=user_id):
            await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
            return

        # Export the chat collection to a CSV file
        chat_db.export_chat_collection_to_csv(file_path)

        # Send the file to the admin
        with open(file_path, 'rb') as document:
            await context.bot.send_document(chat_id=user_id, document=document)
    except Exception as e:
        logging.error(f"Error exporting chat collection: {e}")
        await context.bot.send_message(chat_id=user_id, text="Failed to export chat collection.")
    finally:
        # Ensure the file is deleted after being sent
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as delete_error:
                logging.error(f"Error deleting file {file_path}: {delete_error}")




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
    sitrep_handler = CommandHandler("sitrep", sitrep)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
    document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), document)
    reaction_handler = CallbackQueryHandler(handle_reactions)
    export_handler = CommandHandler("export", export)

    application.add_handler(reaction_handler)
    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(clear_document_handler)
    application.add_handler(analyse_handler)
    application.add_handler(sitrep_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)
    application.add_handler(reaction_handler)
    application.add_handler(export_handler)

    # Set menu commands
    await set_command_menu(application.bot)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())