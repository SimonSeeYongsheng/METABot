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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import CallbackQueryHandler

import llm_module # module for the LLM

import chat_database # module for the chat database
import docs_database # module for the doc database
import docs_processor # module for processing docs

from datetime import datetime

load_dotenv() # Load environment variables from .env file

TELE_BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')
FILE_DRIVE = os.environ.get("FILE_DRIVE")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

chat_db = chat_database.Chat_DB()

llm = llm_module.LLM(Chat_Database=chat_db)
docs_process = docs_processor.Docs_processor()

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

new_message = (
    "Click on your conversation category 👇🏼\n"
    "Press /cancel if you don't want to make any confession"
)

guidance_message_bold = (
    "Please specify the assignment you need guidance on by *replying to this message*.\n\nHere are some examples:\n"
    "📘 Lecture 3\n"
    "📗 Tutorial 5\n"
    "🎯 Mission 10\n"
    "🗺️ Sidequest 5.2\n"
    "📙 Recitation 4\n\n"
    "Feel free to type the exact name or number of your assignment!"
)

guidance_message = (
    "Please specify the assignment you need guidance on by replying to this message.\n\nHere are some examples:\n"
    "📘 Lecture 3\n"
    "📗 Tutorial 5\n"
    "🎯 Mission 10\n"
    "🗺️ Sidequest 5.2\n"
    "📙 Recitation 4\n\n"
    "Feel free to type the exact name or number of your assignment!"
)

guidance_contextual_info_message_bold = (
    "Please send any relevant information about the assignment by *replying to this message*.\n\nYou can upload a file in one of the following formats:\n"
    "📄 PDF (e.g., .pdf)\n"
    "📜 Text (e.g., .txt or plain text in this chat)\n"
    "🐍 Python Code (e.g., .py files)\n\n"
    "Once your documents have been *processed* or if you have no documents to upload, press the *🔍 Query* button below to proceed with your questions or requests."
)

guidance_contextual_info_message = (
    "Please send any relevant information about the assignment by replying to this message.\n\nYou can upload a file in one of the following formats:\n"
    "📄 PDF (e.g., .pdf)\n"
    "📜 Text (e.g., .txt or plain text in this chat)\n"
    "🐍 Python Code (e.g., .py files)\n\n"
    "Once your documents have been processed or if you have no documents to upload, press the 🔍 Query button below to proceed with your questions or requests."
)

guidance_query_message_bold = (
    "What queries do you have? Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the assignment requirements?\n"
    "📝 Are you unsure about how to approach or structure the assignment?\n"
    "💻 Are you facing issues with your code or logic?\n\n"
    "Please type your query below by *replying to this message*, and I'll do my best to help!"
)

guidance_query_message = (
    "What queries do you have? Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the assignment requirements?\n"
    "📝 Are you unsure about how to approach or structure the assignment?\n"
    "💻 Are you facing issues with your code or logic?\n\n"
    "Please type your query below by replying to this message, and I'll do my best to help!"
)

teach_contextual_info_message_bold = (
    "Please send any relevant information about the lecture materials, concepts, or topic by *replying to this message*.\n\n"
    "You can upload a file in one of the following formats:\n"
    "📄 PDF (e.g., .pdf)\n"
    "📜 Text (e.g., .txt or plain text in this chat)\n"
    "🐍 Python Code (e.g., .py files, if applicable)\n\n"
    "Once your documents have been *processed* or if you have no materials to upload, press the *🔍 Query* button below to proceed with your questions or requests."
)

teach_contextual_info_message = (
    "Please send any relevant information about the lecture materials, concepts, or topic by replying to this message.\n\n"
    "You can upload a file in one of the following formats:\n"
    "📄 PDF (e.g., .pdf)\n"
    "📜 Text (e.g., .txt or plain text in this chat)\n"
    "🐍 Python Code (e.g., .py files, if applicable)\n\n"
    "Once your documents have been processed or if you have no materials to upload, press the 🔍 Query button below to proceed with your questions or requests."
)

teach_query_message_bold = (
    "What queries do you have? Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the lecture materials or concepts?\n"
    "🔍 Do you need clarification on a specific topic covered in the lecture?\n"
    "💡 Are there any knowledge gaps you'd like to address?\n\n"
    "Please type your query below by *replying to this message*, and I'll do my best to help!"
)

teach_query_message = (
    "What queries do you have? Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the lecture materials or concepts?\n"
    "🔍 Do you need clarification on a specific topic covered in the lecture?\n"
    "💡 Are there any knowledge gaps you'd like to address?\n\n"
    "Please type your query below by replying to this message, and I'll do my best to help!"
)

first_feedback_message = (
    "This response has never been *seen/generated by a user* before. "
    "If it was helpful, *click 👍*. If not, *click 👎*. "
    "Your feedback helps us improve!"
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
        # chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")

        keyboard = [
            [InlineKeyboardButton("Teach 📚", callback_data="category_teach")],
            [InlineKeyboardButton("Guide 🧭", callback_data="category_guide")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user_id, text=new_message, reply_markup=reply_markup)
        # logging.info(f"New conversation started for user {user_id} (NUSNET ID: {nusnet_id}).")
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



# # Handler for receiving messages and logging chat history
# async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

#     user_id = update.effective_chat.id
#     telegram_handle = update.effective_user.username

#     try:
#         # Retrieve user's NUSNET ID
#         nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
#     except Exception as db_error:
#         logging.error(f"Error retrieving NUSNET ID for user {user_id}: {db_error}")
#         await context.bot.send_message(chat_id=user_id, text="An error occurred. Please try again later.")
#         return

#     # Check if user is authenticated
#     try:
#         if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
#             await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
#             return
#     except Exception as auth_error:
#         logging.error(f"Authentication error for user {user_id}: {auth_error}")
#         await context.bot.send_message(chat_id=user_id, text="An error occurred during authentication. Please try again later.")
#         return
    
#     recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
#     metadata = f"{recent_convo}|{{message_count}}"
#     user_message = update.message.text
#     logging.info(f"Message received from user {user_id}: {user_message}")

#     try:
#         # Retrieve most recent conversation ID
#         most_recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
#         conversation_id = most_recent_convo if most_recent_convo else 1
#     except Exception as convo_error:
#         logging.error(f"Error retrieving recent conversation for NUSNET ID {nusnet_id}: {convo_error}")
#         await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your conversation history. Please try again later.")
#         return

#     try:
#         # Get response from LLM
#         response = await llm.response_message(message=user_message, nusnet_id=nusnet_id, conversation_id=conversation_id)
#     except Exception as llm_error:
#         logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
#         await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
#         return

#     # Split the string into parts using triple backticks
#     parts = response.split("```")

#     for i, part in enumerate(parts):

#         text = part.strip()

#         if i % 2 == 0:  # Even index: plain text
#             keyboard = [
#                 [
#             InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 1)),
#                 ]
#             ]
#             reply_markup = InlineKeyboardMarkup(keyboard)

#             try:
#                 await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
#             except Exception as send_error:
#                 logging.error(f"Error sending part of the message: {send_error}")
#                 await context.bot.send_message(chat_id=user_id, text="Error: Message is too long", reply_markup=reply_markup)

#         else:  # Odd index: code block

#             keyboard = [
#                 [
#             InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 1)),
#                 ]
#             ]
#             reply_markup = InlineKeyboardMarkup(keyboard)

#             try:
#                 await context.bot.send_message(chat_id=user_id, text=f"```{text}```", reply_markup=reply_markup, parse_mode="Markdown")
#             except Exception as send_error:
#                 logging.error(f"Error sending part of the message: {send_error}")
#                 await context.bot.send_message(chat_id=user_id, text="Error: Code block is too long", reply_markup=reply_markup)
                
#     logging.info(f"Message sent to user {user_id}: {response}")


# # Handler for receiving document and logging chat hist
# async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         user_id = update.effective_chat.id
#         nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
#         telegram_handle = update.effective_user.username

#         # Check if user is authenticated
#         if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
#             await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
#             return

#         document = update.message.document
#         recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
#         metadata = f"{recent_convo}|{{message_count}}"

#         if not document:
#             await context.bot.send_message(chat_id=user_id, text="No document found in the message.")
#             return

#         caption = update.message.caption

#         file_name = document.file_name
#         file_size = document.file_size

#         # Log the received document details
#         logging.info(f"Document received: {file_name}, size: {file_size} bytes")

#         # Download the document
#         try:
#             file = await update.message.effective_attachment.get_file()
#             file_path = await file.download_to_drive(custom_path=os.path.join(FILE_DRIVE, file_name))
#             logging.info(f"File downloaded: {file_path}")
#         except Exception as e:
#             logging.error(f"Error downloading file: {e}")
#             await context.bot.send_message(chat_id=user_id, text="Failed to download the document. Please try again.")
#             return

#         # Extract file type
#         try:
#             _, file_extension = os.path.splitext(file_path)
#             file_type = file_extension.lstrip(".").upper()
#         except Exception as e:
#             logging.error(f"Error extracting file type: {e}")
#             await context.bot.send_message(chat_id=user_id, text="Failed to determine the file type. Please check the file and try again.")
#             return

#         # Process the document
#         try:
#             await llm.load_document(file_path=file_path, nusnet_id=nusnet_id, file_type=file_type)
#             await context.bot.send_message(chat_id=user_id, text=f"{file_type} document successfully processed: {file_name}")
#         except Exception as e:
#             logging.error(f"Error processing document: {e}")
#             await context.bot.send_message(chat_id=user_id, text="Failed to process the document. Please try again later.")
#             return

#         # Handle caption if provided
#         if caption:
#             try:
#                 most_recent_convo = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
#                 conversation_id = most_recent_convo if most_recent_convo else 1
#                 response = await llm.response_message(message=caption, nusnet_id=nusnet_id, conversation_id=conversation_id)

#                 # Split the string into parts using triple backticks
#                 parts = response.split("```")

#                 for i, part in enumerate(parts):

#                     text = part.strip()

#                     if i % 2 == 0:  # Even index: plain text

#                         keyboard = [
#                             [
#                         InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 2)),
#                             ]
#                         ]
#                         reply_markup = InlineKeyboardMarkup(keyboard)

#                         try:
#                             await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
#                         except Exception as send_error:
#                             logging.error(f"Error sending part of the message: {send_error}")
#                             await context.bot.send_message(chat_id=user_id, text="Error: Message is too long", reply_markup=reply_markup)

#                     else:  # Odd index: code block

#                         keyboard = [
#                             [
#                         InlineKeyboardButton("👎", callback_data=metadata.format(message_count = i + 2)),
#                             ]
#                         ]
#                         reply_markup = InlineKeyboardMarkup(keyboard)

#                         try:
#                             await context.bot.send_message(chat_id=user_id, text=f"```{text}```", reply_markup=reply_markup, parse_mode="Markdown")
#                         except Exception as send_error:
#                             logging.error(f"Error sending part of the message: {send_error}")
#                             await context.bot.send_message(chat_id=user_id, text="Error: Code block is too long", reply_markup=reply_markup)

#             except Exception as e:
#                 logging.error(f"Error handling caption response: {e}")
#                 await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your caption. Please try again.")

#     except Exception as e:
#         logging.error(f"Unexpected error in document handler: {e}")
#         await context.bot.send_message(chat_id=user_id, text="An unexpected error occurred. Please try again later.")

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
        category = metadata_parts[0]
    except Exception as query_error:
        logging.error(f"Error acknowledging callback query for user {user_id}: {query_error}")

    # Retrieve user's NUSNET ID
    try:
        nusnet_id = chat_db.get_nusnet_id(user_id=user_id)  # Get user's NUSNET ID from the database
    except Exception as db_error:
        logging.error(f"Error retrieving NUSNET ID for user {user_id}: {db_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your data. Please try again later.")
        return

    match category:

        case "category_teach":
            # Start a new conversation
            chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
            logging.info(f"New conversation started for user {user_id} (NUSNET ID: {nusnet_id}).")

            context.user_data.clear()
            context.user_data['category'] = 'teach' # Storing metadata of user's intention

            keyboard = [
                    [
                    InlineKeyboardButton("🔍 Query", callback_data="query_teach"),
                    ]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=teach_contextual_info_message_bold,
                reply_markup=reply_markup, # ForceReply(selective=True),  # Forces the reply
                parse_mode="Markdown"
            )
            return

        
        case "category_guide":
            # Start a new conversation
            chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
            logging.info(f"New conversation started for user {user_id} (NUSNET ID: {nusnet_id}).")

            context.user_data.clear()
            context.user_data['category'] = 'guide' # Storing metadata of user's intention

            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=guidance_message_bold,
                reply_markup=ForceReply(selective=True),  # Forces the reply
                parse_mode="Markdown"
            )
            return
        
        case "query_teach":
            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=teach_query_message_bold ,
                reply_markup=ForceReply(selective=True),  # Forces the reply
                parse_mode="Markdown"
                )
            return

        case "query_guide":
            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=guidance_query_message_bold ,
                reply_markup=ForceReply(selective=True),  # Forces the reply
                parse_mode="Markdown"
                )
            return
        
        case _:
            
            sentiment = metadata_parts[0]
            cat = metadata_parts[1]
            object_id = metadata_parts[2]

            match cat:

                case "teach":
                    prompt, response = chat_db.get_callback_data_teach(object_id)
                    chat_db.input_feedback_teach(nusnet_id=nusnet_id, prompt=prompt, response=response, sentiment=sentiment)
                    return

                case "guide":
                    prompt, response, assignment = chat_db.get_callback_data_guide(object_id)
                    chat_db.input_feedback_guide(nusnet_id=nusnet_id, prompt=prompt, response=response, assignment=assignment, sentiment=sentiment)
                    return
                
            return


    # convo_id = int(metadata_parts[0])
    # user_message = int(metadata_parts[1])
    

    # try:
    #     await context.bot.send_message(
    #         chat_id=user_id,
    #         text="We apologise for the error. The recent conversation will be forwarded to the TA for review. 🙏"
    #     )
    # except Exception as send_error:
    #     logging.error(f"Error sending apology message to user {user_id}: {send_error}")

    # try:
    #     instructors = chat_db.get_instructors(user_id=user_id)
    # except Exception as db_error:
    #     logging.error(f"Error retrieving instructors for user {user_id}: {db_error}")
    #     await context.bot.send_message(chat_id=user_id, text="An error occurred while fetching instructor information. Please try again later.")
    #     return

    # message_id = query.message.message_id

    # for instructor_user_id in instructors:
    #     try:
    #         # Forward the most recent messages to instructors
    #         forwarded_message = await context.bot.forward_message(
    #             chat_id=instructor_user_id,
    #             from_chat_id=user_id,
    #             message_id=(message_id - user_message)
    #         )docum
    #         await context.bot.forward_message(
    #             chat_id=instructor_user_id,
    #             from_chat_id=user_id,
    #             message_id=message_id
    #         )
    #     except Exception as forward_error:
    #         logging.error(f"Error forwarding message to instructor {instructor_user_id} from user {user_id}: {forward_error}")
        
    # try:
    #     prompt = forwarded_message.text if forwarded_message.text else forwarded_message.caption
    #     chat_db.input_feedback(nusnet_id=nusnet_id, conversation_id=convo_id,message=query.message.text,prompt=prompt)
        
    #     await context.bot.send_message(chat_id=user_id, text="Conversation has been saved for review. 📝")

    # except Exception as send_error:
    #     logging.error(f"Error sending review and restart message to user {user_id}: {send_error}")

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




# def clear_all_docs():

#     logging.info(f"Scheduled documents clearance")
#     doc_db.clear_all_docs()


# def run_scheduler():
#     # Schedule the async task
#     schedule.every().day.at(scheduled_clear_time).do(clear_all_docs)
#     print("Scheduler started. Waiting for tasks to execute...")
#     while True:
#         schedule.run_pending()
#         time.sleep(1)





# Handler to capture the user's reply
async def capture_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    # Get the reply text and respond to the user
    user_reply = update.message.text  # The text the user replied with
    original_question = update.message.reply_to_message.text  # The bot's original question

    logging.info(f"Reply to: {original_question}")

    match original_question:

        case original_question if original_question == guidance_message:

            assignment_name = await llm.assignment_message(user_reply)

            context.user_data['assignment'] = assignment_name

            keyboard = [
                    [
                    InlineKeyboardButton("🔍 Query", callback_data="query_guide"),
                    ]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=guidance_contextual_info_message_bold,
                reply_markup=reply_markup,# ForceReply(selective=True),
                parse_mode="Markdown"
            )

        case original_question if original_question == guidance_contextual_info_message or original_question == teach_contextual_info_message:

            # Initialize a list in context.user_data to store file metadata
            if 'documents' not in context.user_data:
                context.user_data['documents'] = []

            if user_reply:
                logging.info(f"User reply: {user_reply}")
                context.user_data['documents'].append(f"User Context:\n{user_reply}\n\n")
                await context.bot.send_message(chat_id=user_id, text="Relevant information processed.")

            if update.message.caption:
                logging.info(f"User reply: {update.message.caption}")
                context.user_data['documents'].append(f"User Context:\n{update.message.caption}\n\n")
                await context.bot.send_message(chat_id=user_id, text="Relevant information processed.")

            if update.message.document:

                document = update.message.document

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
                    file_type = file_extension.lstrip(".").lower()
                except Exception as e:
                    logging.error(f"Error extracting file type: {e}")
                    await context.bot.send_message(chat_id=user_id, text="Failed to determine the file type. Please check the file and try again.")
                    return

                # Process the document
                try:
                    text = docs_process.load_document(file_path=file_path, file_type=file_type)
                    logging.info(f"{file_name}: {text}")
                    context.user_data['documents'].append(f'{file_name}:\n{text}\n\n')
                    await context.bot.send_message(chat_id=user_id, text=f"Document successfully processed: {file_name}")
                except Exception as e:
                    logging.error(f"Error processing document: {e}")
                    await context.bot.send_message(chat_id=user_id, text="Failed to process the document. Please try again later.")
                finally:
                        # Ensure file is removed even if an error occurs
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logging.info(f"Removed file: {file_path}")
                            except Exception as e:
                                logging.error(f"Error removing file: {file_path}. {e}")

        case original_question if original_question == guidance_query_message or original_question == teach_query_message:

            user_id = update.effective_chat.id
            telegram_handle = update.effective_user.username

            try:
                # Retrieve user's NUSNET ID
                nusnet_id = chat_db.get_nusnet_id(user_id=user_id)
            except Exception as db_error:
                logging.error(f"Error retrieving NUSNET ID for user {user_id}: {db_error}")
                await context.bot.send_message(chat_id=user_id, text="An error occurred. Please try again later.")
                return
            
            user_message = update.message.text
            logging.info(f"from user {user_id}: {user_message}")

            try:
                # Retrieve most recent conversation ID
                conversation_id = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
            except Exception as convo_error:
                logging.error(f"Error retrieving recent conversation for NUSNET ID {nusnet_id}: {convo_error}")
                await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your conversation history. Please try again later.")
                return

            try:
                # Get response from LLM
                user_context = "".join(context.user_data['documents']) if "documents" in context.user_data else ""
                response = await llm.response_message(message=user_message, nusnet_id=nusnet_id, conversation_id=conversation_id, 
                                                      intention = context.user_data['category'], user_context = user_context)
                

            except Exception as llm_error:
                logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
                await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
                return

            # Split the string into parts using triple backticks
            parts = response.split("```")

            for i, part in enumerate(parts):

                text = part.strip()

                if i % 2 == 0:  # Even index: plain text

                    try:
                        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
                    except Exception as send_error:
                        logging.error(f"Error sending part of the message: {send_error}")
                        await context.bot.send_message(chat_id=user_id, text="Error: Message is too long")

                else:  # Odd index: code block

                    try:
                        await context.bot.send_message(chat_id=user_id, text=f"```{text}```", parse_mode="Markdown")
                    except Exception as send_error:
                        logging.error(f"Error sending part of the message: {send_error}")
                        await context.bot.send_message(chat_id=user_id, text="Error: Code block is too long")
                        
            logging.info(f"Message sent to user {user_id}: {response}")

            if "assignment" in context.user_data:
                object_id = chat_db.input_callback_data(
                                                        prompt=user_message,
                                                        response=response,
                                                        assignment=context.user_data['assignment']
                                                        )

            else:
                object_id = chat_db.input_callback_data(
                                                        prompt=user_message,
                                                        response=response,
                                                        )
                
            metadata = f"{{sentiment}}|{context.user_data['category']}|{object_id}"

            keyboard = [
                    [
                    InlineKeyboardButton("👍", callback_data=metadata.format(sentiment='like')),
                    InlineKeyboardButton("👎", callback_data=metadata.format(sentiment = 'dislike')),
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=first_feedback_message,
                reply_markup=reply_markup,  # Forces the reply
                parse_mode="Markdown"
            )



# Define the /query command handler
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    # Check if user is authenticated
    try:
        if not chat_db.is_user_authenticated(user_id=user_id, telegram_handle=telegram_handle):
            await context.bot.send_message(chat_id=user_id, text="Please use /start to authenticate.")
            return
    except Exception as auth_error:
        logging.error(f"Authentication error for user {user_id}: {auth_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred during authentication. Please try again later.")
        return
    
    
    if 'category' not in context.user_data:
        # Send a message to tell user to /new
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry I cannot assist you, please send /new to start a new query." ,
            parse_mode="Markdown"
        )
        return
    
    elif context.user_data['category'] == 'guide':
        # Send a message forcing the user to reply
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=guidance_query_message_bold ,
            reply_markup=ForceReply(selective=True),  # Forces the reply
            parse_mode="Markdown"
            )
        return
        

    elif context.user_data['category'] == 'teach':
        # Send a message forcing the user to reply
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=teach_query_message_bold ,
            reply_markup=ForceReply(selective=True),  # Forces the reply
            parse_mode="Markdown"
            )
        return







async def main():

    # Start the scheduler in a separate thread
    # scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    # scheduler_thread.start()

    # Build the bot application
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    new_convo_handler = CommandHandler('new', new)
    clear_document_handler = CommandHandler("clear_docs", clear_docs)
    analyse_handler = CommandHandler("analyse", analyse)
    sitrep_handler = CommandHandler("sitrep", sitrep)
    # message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message)
    # document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), handle_documents)
    # query_handler = CommandHandler("query", handle_query)
    reaction_handler = CallbackQueryHandler(handle_reactions)
    export_handler = CommandHandler("export", export)

    application.add_handler(MessageHandler(filters.REPLY & (~filters.COMMAND), capture_reply))  # Handles ForceReply responses

    application.add_handler(reaction_handler)
    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(clear_document_handler)
    application.add_handler(analyse_handler)
    application.add_handler(sitrep_handler)
    # application.add_handler(message_handler)
    # application.add_handler(document_handler)
    application.add_handler(reaction_handler)
    application.add_handler(export_handler)
    #application.add_handler(query_handler)

    # Set menu commands
    await set_command_menu(application.bot)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
