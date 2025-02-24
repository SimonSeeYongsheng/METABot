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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import CallbackQueryHandler, ConversationHandler, PollAnswerHandler

import llm_module # module for the LLM

import chat_database # module for the chat database
import docs_processor # module for processing docs

from datetime import datetime

import telegramify_markdown # module to convert markdown to markdownV2 response
from telegramify_markdown.customize import markdown_symbol
from telegramify_markdown.interpreters import BaseInterpreter, MermaidInterpreter
from telegramify_markdown.type import ContentTypes
import csv
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

supported_file_types = ["pdf", "txt", "py", "html", "js", "css", "htm", "csv"]

start_message = (
    "👋 *Welcome to METABot!*\n\n"
    "I’m here to make your learning journey awesome! Here’s what you can do:\n\n"
    "📜 */start*: Learn more about how to use me—your friendly METABot!\n\n"
    "🆕 */new*: Start a fresh conversation and pick a category to dive in!\n\n"
    "📊 */analyse*: Students, get personalized insights on your learning behaviour!\n\n"
    "🧑‍🏫 */analyse [nusnet_id]*: Instructors, view your student’s learning behaviour.\n\n"
    "📝 */uncover*: Students, uncover any misconceptions about the course content.\n\n"
    "📝 */uncover [nusnet_id]*: Instructors, see your student’s misconceptions.\n\n"
    # "📁 */export_chat*: Save the chat history to a file *(instructors only)*.\n\n"
    # "📂 */export_teach*: Export *Teach* category feedback to a file *(instructors only)*.\n\n"
    # "📂 */export_guide*: Export *Guide* category feedback to a file *(instructors only)*.\n\n"
    "✨ Ready to get started? Press /new and select a category to begin your journey. Let’s go! 🚀\n"
)


unsupported_file_message = (
    "🚫 *Unsupported File Type* 🚫"
)


# Set command menu
async def set_command_menu(bot):
    commands = [
        BotCommand("start", "Open the information menu"),
        BotCommand("new", "Start a new conversation"),
        BotCommand("analyse", "Analyse learning behaviour (/analyse [nusnet_id] for instructors only)"),
        BotCommand("uncover", "Uncover any misconceptions about the course content (/uncover [nusnet_id] for instructors only)"),
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
    
    context.user_data['documents'] = [] # Clear documents
    # Start a new conversation
    convo_id = chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started.")
    logging.info(f"New conversation started for user {user_id} (NUSNET ID: {nusnet_id}).")
    # context.user_data['conversation_id'] = convo_id # Storing conversation id

    try:

        # Send a message forcing the user to reply
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="A new conversation has started.",
                parse_mode="Markdown"
        )

    except Exception as start_error:
        logging.error(f"Error starting a new conversation for NUSNET ID {nusnet_id}: {start_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while starting a new conversation. Please try again later.")

# Handler for /analyse command to analyse learning behaviour
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    user_nusnet_id = chat_db.get_nusnet_id(user_id)

    user_message = user_nusnet_id if len(context.args) == 0 else context.args[0].upper()

    if chat_db.is_admin(user_id=user_id) and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await reply_to_query(update=update, context=context, user_id=user_id, response=response)

    elif user_nusnet_id == user_message and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(nusnet_id=user_message)

        await reply_to_query(update=update, context=context, user_id=user_id, response=response)
    
    else:

        await context.bot.send_message(chat_id=user_id, text="User is unauthorised")

async def reply_to_query_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id : str, response : str,
                         prompt : str, conversation_id : int):

    boxs = await telegramify_markdown.telegramify(
        content=response,
        interpreters_use=[BaseInterpreter(), MermaidInterpreter(session=None)],  # Render mermaid diagram
        latex_escape=True,
        normalize_whitespace=True,
        max_word_count=4096  # The maximum number of words in a single message.
    )

    for item in boxs:

        try:
            if item != boxs[-1]:
            
                await context.bot.send_message(chat_id=user_id, text=item.content, parse_mode="MarkdownV2")
            
            else:

                object_id = chat_db.input_callback_data(
                            prompt=prompt,
                            response=response,
                            conversation_id=conversation_id,
                            )
                
                metadata = f"{{sentiment}}|{object_id}"

                keyboard = [
                                [
                                InlineKeyboardButton("👍", callback_data=metadata.format(sentiment='like')),
                                InlineKeyboardButton("👎", callback_data=metadata.format(sentiment = 'dislike')),
                                ]
                            ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(chat_id=user_id, text=item.content, parse_mode="MarkdownV2", reply_markup=reply_markup)
                

            
        except Exception as send_error:
            logging.error(f"Error sending part of the message: {send_error}\n\nMessage : {item}")
            await context.bot.send_message(chat_id=user_id, text="Error: Sending Message")

async def reply_to_query(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id : str, response : str):

    boxs = await telegramify_markdown.telegramify(
        content=response,
        interpreters_use=[BaseInterpreter(), MermaidInterpreter(session=None)],  # Render mermaid diagram
        latex_escape=True,
        normalize_whitespace=True,
        max_word_count=4096  # The maximum number of words in a single message.
    )

    for item in boxs:

        try:
            
                await context.bot.send_message(chat_id=user_id, text=item.content, parse_mode="MarkdownV2")
            
        except Exception as send_error:
            logging.error(f"Error sending part of the message: {send_error}\n\nMessage : {item}")
            await context.bot.send_message(chat_id=user_id, text="Error: Sending Message")

    logging.info(f"Message sent to user {user_id}: {response}")

# Handler for uncovering misconceptions
async def misconception(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    user_nusnet_id = chat_db.get_nusnet_id(user_id)

    user_message = user_nusnet_id if len(context.args) == 0 else context.args[0].upper()

    if chat_db.is_admin(user_id=user_id) and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Misconception: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Generating misconception report...give me a moment...")

        try:
            response = await llm.misconception_message(nusnet_id=user_message)
        
        except Exception as misconception_error:
            logging.error(f"Error retrieving misconception report for user {user_id}: {misconception_error}")
            await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving smisconception report. Please try again later.")
            return

        
        await reply_to_query(update=update, context=context, user_id=user_id, response=response)

    elif user_nusnet_id == user_message and chat_db.user_exist(nusnet_id=user_message):

        logging.info(f"Misconception: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Generating misconception report...give me a moment...")

        try:
            response = await llm.misconception_message(nusnet_id=user_message)
        except Exception as misconception_error:
            logging.error(f"Error retrieving misconception report for user {user_id}: {misconception_error}")
            await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving misconception report. Please try again later.")
            return

        await reply_to_query(update=update, context=context, user_id=user_id, response=response)
    
    else:

        await context.bot.send_message(chat_id=user_id, text="User is unauthorised")

# Handler for handling reactions to chatbot response
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        case "like":
            object_id = metadata_parts[1]
            prompt, response, conversation_id = chat_db.get_callback_data(object_id)
            object_id = chat_db.input_feedback_data(nusnet_id=nusnet_id, prompt=prompt, response=response, 
                                                     conversation_id=conversation_id, sentiment=category)
            await context.bot.send_message(chat_id=user_id, text="Thank you so much for your feedback! 😊")

        case "dislike":
            object_id = metadata_parts[1]
            prompt, response, conversation_id = chat_db.get_callback_data(object_id)
            object_id = chat_db.input_feedback_data(nusnet_id=nusnet_id, prompt=prompt, response=response, 
                                                     conversation_id=conversation_id, sentiment=category)
            await context.bot.send_message(chat_id=user_id, text="Thank you so much for your feedback! 😊")

# Handler for handling teach feedback export
async def export_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command to export the feedback collection."""
    user_id = update.effective_chat.id
    file_path = f"feedback_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    try:
        # Check if the user is an admin
        if not chat_db.is_admin(user_id=user_id):
            await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
            return

        # Export the teach feedback collection to a CSV file
        chat_db.export_feedback_collection_to_csv(file_path)

        # Send the file to the admin
        with open(file_path, 'rb') as document:
            await context.bot.send_document(chat_id=user_id, document=document)
    except Exception as e:
        logging.error(f"Error exporting feedback collection: {e}")
        await context.bot.send_message(chat_id=user_id, text="Failed to export feedback collection.")
    finally:
        # Ensure the file is deleted after being sent
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as delete_error:
                logging.error(f"Error deleting file {file_path}: {delete_error}")

# Handler for handling chat history export
async def export_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export_chat command to export the chat collection."""
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

# Handler to capture the user's attachments
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    # Initialize a list in context.user_data to store file metadata
    if 'documents' not in context.user_data:
        context.user_data['documents'] = []

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
                
        # Check if file type is supported
        if file_type not in supported_file_types:
            await context.bot.send_message(chat_id=user_id, text=unsupported_file_message, parse_mode="Markdown")

        # Process the document
        else:

            try:
                text = docs_process.load_document(file_path=file_path, file_type=file_type)
                logging.info(f"{file_name}: {text}")
                context.user_data['documents'].append(f'{file_name}:\n{text}\n\n')
                await context.bot.send_message(chat_id=user_id, text=f"Document successfully processed: {file_name}")
            except Exception as e:
                logging.error(f"Error processing document: {e}")
                await context.bot.send_message(chat_id=user_id, text="Failed to process the document. Please try again later.")

        # Ensure file is removed even if an error occurs
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Removed file: {file_path}")
            except Exception as e:
                logging.error(f"Error removing file: {file_path}. {e}")

        if update.message.photo or update.message.audio or update.message.video:
            await context.bot.send_message(chat_id=user_id, text=unsupported_file_message, parse_mode="Markdown")

# Handler to handle user's messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id


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

    else:

        try:
            # Get response from LLM
            user_context = "".join(context.user_data['documents']) if "documents" in context.user_data else ""

            response = await llm.response_message(message=user_message, nusnet_id=nusnet_id, conversation_id=conversation_id, 
                                                         user_context = user_context)
                    

        except Exception as llm_error:
            logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
            await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
            return
                
        await reply_to_query_feedback(update=update, context=context, user_id=user_id, response=response, 
                                              prompt=user_message, conversation_id=conversation_id)
        
        context.user_data['documents'] = []



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    await context.bot.send_message(chat_id=user_id, text="No worries 😅. Please use /new to *make a new query*", parse_mode="Markdown")


# Error handler for all general errors
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to the user."""
    # Log the error (optional: log to a file or monitoring system)
    logging.error(f"Update {update} caused error {context.error}")

    # Notify the user if an update is available
    if isinstance(update, Update):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="An unexpected error occurred. Please try again later."
            )
        except Exception as e:
            logging.error(f"Failed to send error notification: {e}")

##########################################################################################################################################
# Define a new state for the quiz upload conversation
QUIZ_UPLOAD = 1

# Handler to start the quiz upload conversation
async def start_quiz_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    # Check if user is a teacher/admin (adjust as needed)
    if not chat_db.is_admin(user_id=user_id):
        await context.bot.send_message(chat_id=user_id, text="Unauthorized: Only teachers can upload quiz questions.")
        return ConversationHandler.END
    await context.bot.send_message(
        chat_id=user_id,
        text="Please upload a CSV file containing your quiz questions.\n\n"
             "Expected CSV format per row: *question, option1, option2, option3, option4, correct_option_index, explanation*\n\n"
             "(The correct option index should be 0-indexed.)\n\n"
             "type /cancel to cancel the upload process.",
        parse_mode="Markdown"
    )
    return QUIZ_UPLOAD

# Handler to process the uploaded CSV file and send quiz polls
async def process_quiz_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    document = update.message.document
    file_name = document.file_name

    # Ensure the file has a .csv extension
    _, ext = os.path.splitext(file_name)
    if ext.lower() != ".csv":
        await context.bot.send_message(chat_id=user_id, text="Please upload a valid CSV file.")
        return QUIZ_UPLOAD  # Stay in the state for a correct file

    # Download the CSV file
    try:
        file = await document.get_file()
        file_path = os.path.join(FILE_DRIVE, file_name)
        await file.download_to_drive(custom_path=file_path)
        logging.info(f"CSV file downloaded: {file_path}")
    except Exception as e:
        logging.error(f"Error downloading CSV file: {e}")
        await context.bot.send_message(chat_id=user_id, text="Failed to download the CSV file. Please try again.")
        return ConversationHandler.END

    polls_sent = 0

    # Get latest quiz id
    quiz_id = chat_db.get_latest_quiz_id() + 1

    # Retrieve the list of all students (non-admin users)
    student_ids = chat_db.get_all_students()  # Expects a list of user_id values

    # Also include the teacher who uploaded the CSV if desired
    recipients = student_ids + [user_id] # if you wish to include the teacher

    # Process the CSV file
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                # Expecting at least 7 columns: question, option1, option2, option3, option4, correct_option_index, explanation
                if len(row) < 7:
                    logging.warning(f"Row skipped (not enough columns): {row}")
                    continue

                question = row[0].strip()
                raw_options = [opt.strip() for opt in row[1:5]]
                # Filter out options marked as '-' (treat as non-existent)
                valid_options = [opt for opt in raw_options if opt != '-']

                # Log if there are less than 4 valid options
                if len(valid_options) < 4:
                    logging.info(f"Question has less than 4 valid options: '{question}'. Only {len(valid_options)} valid option(s) found.")

                # Ensure there are at least 2 options for a poll
                if len(valid_options) < 2:
                    logging.warning(f"Row skipped (not enough valid options): {row}")
                    continue

                # Parse the correct option index from the CSV (assumed 0-indexed)
                try:
                    correct_raw_index = int(row[5])
                except ValueError:
                    logging.warning(f"Invalid correct option index in row: {row}")
                    continue

                # Check that the designated correct option is not marked as '-'
                if raw_options[correct_raw_index] == '-':
                    logging.warning(f"Correct option marked as '-' in row: {row}")
                    continue

                # Map the CSV correct index (based on raw_options) to the new index in valid_options.
                # Count how many valid options appear before (and including) the correct option.
                new_correct_index = sum(1 for i in range(correct_raw_index + 1) if raw_options[i] != '-') - 1

                explanation = row[6].strip()

                # Send the poll to every recipient
                for recipient in recipients:
                    try:
                        msg = await context.bot.send_poll(
                            chat_id=recipient,
                            question=question,
                            options=valid_options,
                            type='quiz',
                            correct_option_id=new_correct_index,
                            is_anonymous=False,  # Must be False to get answer details
                            explanation=explanation,
                            explanation_parse_mode="Markdown"
                        )
                        polls_sent += 1
                        # Store the poll details in the database for later retrieval.
                        poll = msg.poll  # Extract the Poll object
                        chat_db.store_poll_details(
                            quiz_id=quiz_id,
                            poll_id=poll.id,
                            question=question,
                            correct_option_id=new_correct_index,
                            options=valid_options,
                            explanation=explanation
                        )
                    except Exception as poll_error:
                        logging.error(f"Error sending poll to recipient {recipient}: {poll_error}")
                        continue
    except Exception as csv_error:
        logging.error(f"Error processing CSV file: {csv_error}")
        await context.bot.send_message(chat_id=user_id, text="Failed to process the CSV file.")
    finally:
        # Remove the CSV file after processing
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Removed CSV file: {file_path}")
            except Exception as remove_error:
                logging.error(f"Error removing CSV file: {remove_error}")

    await context.bot.send_message(
        chat_id=user_id,
        text=f"Quiz upload complete. {polls_sent} poll(s) sent to {len(recipients)} recipient(s)."
    )
    return ConversationHandler.END




# (Optional) Handler to cancel the quiz upload conversation
async def cancel_quiz_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    await context.bot.send_message(chat_id=user_id, text="Quiz upload cancelled.")
    return ConversationHandler.END

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_answer = update.poll_answer
    user = poll_answer.user
    poll_id = poll_answer.poll_id
    selected_options = poll_answer.option_ids  # List of selected option indices.
    user_id = user.id

    # Retrieve the student's NUSNET id.
    nusnet_id = chat_db.get_nusnet_id(user_id)

    # Get the quiz details for this poll.
    poll_details = chat_db.get_poll_details(poll_id)
    if poll_details is None:
        logging.error(f"No poll details found for poll_id {poll_id}")
        return
    quiz_id = poll_details.get("quiz_id")
    question = poll_details.get("question")
    correct_option_id = poll_details.get("correct_option_id")
    options = poll_details.get("options")
    explanation = poll_details.get("explanation")
    # Assuming single-answer quiz polls.
    student_answer = selected_options[0] if selected_options else None
    is_correct = (student_answer == correct_option_id)

    # Store the quiz response with all the required details.
    chat_db.store_quiz_response(
         quiz_id=quiz_id,
         poll_id=poll_id,
         user_id=user_id,
         nusnet_id=nusnet_id,
         student_answer=student_answer,
         question=question,
         correct_option_id=correct_option_id,
         options=options,
         explanation=explanation,
         is_correct=is_correct,
         timestamp=datetime.now()
    )

    logging.info(f"Stored quiz response from user {user_id} for poll {poll_id}: student_answer={student_answer}, is_correct={is_correct}")

# Add this new command handler somewhere in your TelegramBot.py file
async def remediate_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teacher_id = update.effective_chat.id

    # Verify that the user is a teacher/admin.
    if not chat_db.is_admin(user_id=teacher_id):
        await context.bot.send_message(chat_id=teacher_id, text="Unauthorized: Only teachers can initiate remediation.")
        return

    # Retrieve all student user IDs (non-admin users)
    student_ids = chat_db.get_all_students()
    if not student_ids:
        await context.bot.send_message(chat_id=teacher_id, text="No students found.")
        return

    for student_user_id in student_ids:
        # Retrieve the student's NUSNET ID.
        student_nusnet = chat_db.get_nusnet_id(student_user_id)
        if not student_nusnet:
            continue

        # Get only the latest mistakes for the student.
        latest_mistakes = chat_db.get_latest_mistakes_by_student(student_nusnet)
        if not latest_mistakes:
            continue  # Skip students with no mistakes in the latest quiz

        # Compile a summary of the mistakes
        mistakes_summary = []
        for mistake in latest_mistakes:
            mistakes_summary.append(
                f"*Question:* {mistake.get('question')}\n"
                f"*Your Answer:* {mistake.get('student_answer')}\n"
                f"*Correct Answer:* {mistake.get('correct_option_id')}\n"
                f"*Explanation:* {mistake.get('explanation')}"
            )

        # Create a remediation message
        summary_text = "\n\n".join(mistakes_summary)
        remediation_message = await llm.mistake_message(summary_text)

        # Start a new conversation for the student
        conversation_id = chat_db.start_new_conversation(message=remediation_message, nusnet_id=student_nusnet)

        # Send the remediation message to the student
        try:
            await reply_to_query(update=update, context=context, user_id=student_user_id, response=remediation_message)
        except Exception as e:
            logging.error(f"Failed to send remediation message to student {student_user_id}: {e}")

    # Inform the teacher that remediation messages have been sent
    await context.bot.send_message(chat_id=teacher_id, text="Remediation messages have been sent to students based on the latest quiz results.")

async def export_quiz_responses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    file_path = f"quiz_responses_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    try:
        # Only allow admins to use this command.
        if not chat_db.is_admin(user_id=user_id):
            await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
            return

        # Export the quiz responses collection to a CSV file.
        chat_db.export_quiz_responses_collection_to_csv(file_path)

        # Send the file to the admin.
        with open(file_path, 'rb') as document:
            await context.bot.send_document(chat_id=user_id, document=document)
    except Exception as e:
        logging.error(f"Error exporting quiz responses: {e}")
        await context.bot.send_message(chat_id=user_id, text="Failed to export quiz responses.")
    finally:
        # Delete the file after sending.
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as delete_error:
                logging.error(f"Error deleting file {file_path}: {delete_error}")



async def main():

    # Build the bot application
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    new_convo_handler = CommandHandler('new', new)
    analyse_handler = CommandHandler("analyse", analyse)
    misconception_handler = CommandHandler("uncover", misconception)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), handle_document)
    query_handler = CallbackQueryHandler(handle_query)
    export_chat_handler = CommandHandler("export_chat", export_chat)
    export_feedback_handler = CommandHandler("export_feedback", export_feedback)

    quiz_upload_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('upload_quiz', start_quiz_upload)],
    states={
        QUIZ_UPLOAD: [MessageHandler(filters.Document.ALL, process_quiz_csv)]
    },
    fallbacks=[CommandHandler('cancel', cancel_quiz_upload)]
    )
    
    application.add_handler(quiz_upload_conv_handler)
    poll_answer_handler = PollAnswerHandler(handle_poll_answer)
    application.add_handler(poll_answer_handler)

    remediate_handler = CommandHandler("remediate", remediate_students)
    application.add_handler(remediate_handler)

    export_quiz_handler = CommandHandler("export_quiz", export_quiz_responses)
    application.add_handler(export_quiz_handler)

    application.add_handler(query_handler)
    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(analyse_handler)
    application.add_handler(misconception_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)
    application.add_handler(export_chat_handler)
    application.add_handler(export_feedback_handler)
    application.add_error_handler(error_handler)

    # Set menu commands
    await set_command_menu(application.bot)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
