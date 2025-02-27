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
import re

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from random import randint
from datetime import datetime, timedelta

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
scheduler = AsyncIOScheduler()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB limit

supported_file_types = [
    "pdf", "docx", "json", "html", "htm", "xml", "xlsx", "xls", "ipynb", "pptx",
    "txt", "py", "js", "css", "csv",
    "java", "c", "cpp", "cs", "rb", "php", "swift", "ts", "go", "rs", "sh"
]

start_message = (
    "👋 *Welcome to METABot!*\n\n"
    "I’m here to make your learning journey awesome! Here’s what you can do:\n\n"
    "📜 */start*: Learn more about how to use me—your friendly METABot!\n\n"
    "🆕 */new*: Start a fresh conversation and pick a category to dive in!\n\n"
    "🗑 */clear*: Remove all uploaded documents.\n\n"
    "📊 */analyse*: Gain personalized insights on your learning behaviour!\n\n"
    "📝 */uncover*: Identify any misconceptions to strengthen your knowledge.\n\n"
    "✨ Ready to get started? Press /new and select a category to begin your journey. Let’s go! 🚀\n"
)


unsupported_file_message = (
    "🚫 *Unsupported File Type* 🚫\n\n"
    "This file type is not supported. Please upload a document, text file, or code file in a common format.\n\n"
    "✔ *Supported*: PDFs, Word, Excel, PowerPoint, JSON, HTML, TXT, CSV, Jupyter Notebooks, and popular programming files (Python, Java, C, JS, etc.)\n\n"
    "Try again with a supported format. 😊"
)

ILS_QUESTIONS = [
    {"question": "1. I understand something better after I", "options": ["try it out.", "think it through."]},
    {"question": "2. I would rather be considered", "options": ["realistic.", "innovative."]},
    {"question": "3. When I think about what I did yesterday, I am most likely to get", "options": ["a picture.", "words."]},
    {"question": "4. I tend to", "options": ["understand details of a subject but may be fuzzy about its overall structure.", "understand the overall structure but may be fuzzy about details."]},
    {"question": "5. When I am learning something new, it helps me to", "options": ["talk about it.", "think about it."]},
    {"question": "6. If I were a teacher, I would rather teach a course", "options": ["that deals with facts and real life situations.", "that deals with ideas and theories."]},
    {"question": "7. I prefer to get new information in", "options": ["pictures, diagrams, graphs, or maps.", "written directions or verbal information."]},
    {"question": "8. Once I understand", "options": ["all the parts, I understand the whole thing.", "the whole thing, I see how the parts fit."]},
    {"question": "9. In a study group working on difficult material, I am more likely to", "options": ["jump in and contribute ideas.", "sit back and listen."]},
    {"question": "10. I find it easier", "options": ["to learn facts.", "to learn concepts."]},
    {"question": "11. In a book with lots of pictures and charts, I am likely to", "options": ["look over the pictures and charts carefully.", "focus on the written text."]},
    {"question": "12. When I solve maths problems", "options": ["I usually work my way to the solutions one step at a time.", "I often just see the solutions but then have to struggle to figure out the steps to get to them."]},
    {"question": "13. In classes I have taken", "options": ["I have usually got to know many of the students.", "I have rarely got to know many of the students."]},
    {"question": "14. In reading non-fiction, I prefer", "options": ["something that teaches me new facts or tells me how to do something.", "something that gives me new ideas to think about."]},
    {"question": "15. I like teachers", "options": ["who put a lot of diagrams on the board.", "who spend a lot of time explaining."]},
    {"question": "16. When I'm analysing a story or a novel", "options": ["I think of the incidents and try to put them together to figure out the themes.", "I identify themes first, then revisit the text to find supporting incidents."]},
    {"question": "17. When I start a homework problem, I am more likely to", "options": ["start working on the solution immediately.", "try to fully understand the problem first."]},
    {"question": "18. I prefer the idea of", "options": ["certainty.", "theory."]},
    {"question": "19. I remember best", "options": ["what I see.", "what I hear."]},
    {"question": "20. It is more important to me that an instructor", "options": ["lay out the material in clear sequential steps.", "give me an overall picture and relate the material to other subjects."]},
    {"question": "21. I prefer to study", "options": ["in a group.", "alone."]},
    {"question": "22. I am more likely to be considered", "options": ["careful about the details of my work.", "creative about how to do my work."]},
    {"question": "23. When I get directions to a new place, I prefer", "options": ["a map.", "written instructions."]},
    {"question": "24. I learn", "options": ["at a fairly regular pace. If I study hard, I'll 'get it.'", "in fits and starts. I'll be totally confused and then suddenly it all 'clicks.'"]},
    {"question": "25. I would rather first", "options": ["try things out.", "think about how I'm going to do it."]},
    {"question": "26. When I am reading for enjoyment, I like writers to", "options": ["clearly say what they mean.", "say things in creative, interesting ways."]},
    {"question": "27. When I see a diagram or sketch in class, I am most likely to remember", "options": ["the picture.", "what the instructor said about it."]},
    {"question": "28. When considering a body of information, I am more likely to", "options": ["focus on details and miss the big picture.", "try to understand the big picture before getting into the details."]},
    {"question": "29. I more easily remember", "options": ["something I have done.", "something I have thought a lot about."]},
    {"question": "30. When I have to perform a task, I prefer to", "options": ["master one way of doing it.", "come up with new ways of doing it."]},
    {"question": "31. When someone is showing me data, I prefer", "options": ["charts or graphs.", "text summarizing the results."]},
    {"question": "32. When writing a paper, I am more likely to", "options": ["work on (think about or write) the beginning of the paper and progress forward.", "work on (think about or write) different parts of the paper and then order them."]},
    {"question": "33. When I have to work on a group project, I first want to", "options": ["have a 'group brainstorming' where everyone contributes ideas.", "brainstorm individually and then come together as a group to compare ideas."]},
    {"question": "34. I consider it higher praise to call someone", "options": ["sensible.", "imaginative."]},
    {"question": "35. When I meet people at a party, I am more likely to remember", "options": ["what they looked like.", "what they said about themselves."]},
    {"question": "36. When I am learning a new subject, I prefer to", "options": ["stay focused on that subject, learning as much about it as I can.", "try to make connections between that subject and related subjects."]},
    {"question": "37. I am more likely to be considered", "options": ["outgoing.", "reserved."]},
    {"question": "38. I prefer courses that emphasise", "options": ["concrete material (facts, data).", "abstract material (concepts, theories)."]},
    {"question": "39. For entertainment, I would rather", "options": ["watch television.", "read a book."]},
    {"question": "40. Some teachers start their lectures with an outline of what they will cover. Such outlines are", "options": ["somewhat helpful to me.", "very helpful to me."]},
    {"question": "41. The idea of doing homework in groups, with one grade for the entire group,", "options": ["appeals to me.", "does not appeal to me."]},
    {"question": "42. When I am doing long calculations,", "options": ["I tend to repeat all my steps and check my work carefully.", "I find checking my work tiresome and have to force myself to do it."]},
    {"question": "43. I tend to picture places I have been", "options": ["easily and fairly accurately.", "with difficulty and without much detail."]},
    {"question": "44. When solving problems in a group, I would be more likely to", "options": ["think of the steps in the solution process.", "think of possible consequences or applications of the solution in a wide range of areas."]}
]

def get_next_run_time():
    now = datetime.now()
    # Select a random hour between 8 (8 AM) and 21 (9 PM)
    hour = randint(8, 21)
    minute = randint(0, 59)
    second = randint(0, 59)
    next_run = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
    # If the random time has already passed today, schedule for tomorrow
    if next_run <= now:
        next_run += timedelta(days=1)
    return next_run

# Set command menu
async def set_command_menu(bot):
    commands = [
        BotCommand("start", "Open the information menu"),
        BotCommand("new", "Start a new conversation"),
        BotCommand("clear", "Clear uploaded documents"),
        BotCommand("analyse", "Analyse learning behaviour"),
        BotCommand("uncover", "Uncover any misconceptions during the conversation"),
        BotCommand("clear", "Clear uploaded documents")
    ]

    await bot.set_my_commands(commands)

# Handler for /start command to authenticate users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    telegram_handle = update.effective_user.username

    logging.info(f"User {telegram_handle} (ID {user_id}) invoked /start.")

    # Check if user is already authenticated
    if chat_db.is_user_authenticated(user_id=user_id):
        await context.bot.send_message(chat_id=user_id, text=start_message, parse_mode="Markdown")
    else:
        # New user: start ILS questionnaire
        await context.bot.send_message(
            chat_id=user_id, 
            text = (
                "Welcome! 👋\n\n"
                "Before using the bot, please complete our quick *44-question Learning Styles Questionnaire*.\n\n"
                "🕒 It takes only *3 minutes* and is a *one-time step*.\n"
                "💡 No need to overthink—just go with your *first instinct!*"
            ),
            parse_mode="Markdown"
        )
        # Clear any existing ILS answers and initialize state
        chat_db.clear_ils_answers(user_id)
        context.user_data["ils_index"] = 0  # Start at question 0
        context.user_data["poll_map"] = {}  # To map poll IDs to question indices
        await send_ils_poll(update, context)


# Handler for /new command to start a new conversation
async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    
    context.user_data['documents'] = [] # Clear documents
    # Start a new conversation
    convo_id = chat_db.start_new_conversation(user_id=user_id, message="A new conversation has started.")
    logging.info(f"New conversation started for user {user_id}.")
    # context.user_data['conversation_id'] = convo_id # Storing conversation id

    try:

        # Send a message forcing the user to reply
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="A new conversation has started.",
                parse_mode="Markdown"
        )

    except Exception as start_error:
        logging.error(f"Error starting a new conversation for user_id {user_id}: {start_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while starting a new conversation. Please try again later.")

async def clear_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    # Reset the documents list if it exists
    if 'documents' in context.user_data:
        context.user_data['documents'] = []
        logging.info(f"Cleared processed documents for user {user_id}.")
    else:
        logging.info(f"No documents to clear for user {user_id}.")
    
    await context.bot.send_message(chat_id=user_id, text="All processed documents have been cleared.")

# Handler for /analyse command to analyse learning behaviour
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    user_message = user_id if len(context.args) == 0 else context.args[0]

    if chat_db.is_admin(user_id=user_id) and chat_db.user_exist(user_id=user_id):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(user_id=user_message)

        await reply_to_query(update=update, context=context, user_id=user_id, response=response)

    elif user_id == user_message and chat_db.user_exist(user_id=user_id):

        logging.info(f"Analysing: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Analysing...give me a moment...")

        response = await llm.analyse_message(user_id=user_message)

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

async def reply_to_daily(app, user_id: str, response: str):

    boxs = await telegramify_markdown.telegramify(
        content=response,
        interpreters_use=[BaseInterpreter(), MermaidInterpreter(session=None)],  # Render mermaid diagram
        latex_escape=True,
        normalize_whitespace=True,
        max_word_count=4096  # The maximum number of words in a single message.
    )

    for item in boxs:

        try:
            await app.bot.send_message(chat_id=user_id, text=item.content, parse_mode="MarkdownV2")
            
        except Exception as send_error:
            logging.error(f"Error daily message: {send_error}\n\nMessage : {item}")

    logging.info(f"Message sent to user {user_id}: {response}")



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

    user_message = user_id if len(context.args) == 0 else context.args[0].upper()

    if chat_db.is_admin(user_id=user_id) and chat_db.user_exist(user_id=user_id):

        logging.info(f"Misconception: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Uncovering misconceptions...give me a moment...")

        try:
            response = await llm.misconception_message(user_id=user_message)
        
        except Exception as misconception_error:
            logging.error(f"Error retrieving misconception report for user {user_id}: {misconception_error}")
            await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving smisconception report. Please try again later.")
            return

        
        await reply_to_query(update=update, context=context, user_id=user_id, response=response)

    elif user_id == user_message and chat_db.user_exist(user_id=user_id):

        logging.info(f"Misconception: {user_message}")

        await context.bot.send_message(chat_id=user_id, text="Uncovering misconceptions...give me a moment...")

        try:
            response = await llm.misconception_message(user_id=user_message)
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

    match category:
        
        case "like":
            object_id = metadata_parts[1]
            prompt, response, conversation_id = chat_db.get_callback_data(object_id)
            object_id = chat_db.input_feedback_data(user_id=user_id, prompt=prompt, response=response, 
                                                     conversation_id=conversation_id, sentiment=category)
            await context.bot.send_message(chat_id=user_id, text="Thank you so much for your feedback! 😊")

        case "dislike":
            object_id = metadata_parts[1]
            prompt, response, conversation_id = chat_db.get_callback_data(object_id)
            object_id = chat_db.input_feedback_data(user_id=user_id, prompt=prompt, response=response, 
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
    # Ensure a documents list exists in user_data
    if 'documents' not in context.user_data:
        context.user_data['documents'] = []

    if update.message.document:
        document = update.message.document
        file_name = document.file_name
        file_size = document.file_size

        logging.info(f"Document received: {file_name}, size: {file_size} bytes")

        # 1. Check file size (20MB limit)
        if file_size > MAX_FILE_SIZE:
            await context.bot.send_message(
                chat_id=user_id,
                text="The file size exceeds the Telegram API limit of 20MB."
            )
            return

        # 2. Download the document using download_to_drive (saves file to disk)
        try:
            file = await update.message.effective_attachment.get_file()
            file_path = await file.download_to_drive(custom_path=os.path.join(FILE_DRIVE, file_name))
            logging.info(f"File downloaded to: {file_path}")
        except Exception as e:
            logging.error(f"Error downloading file: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text="Failed to download the document. Please try again."
            )
            return

        # 3. Determine file type from its extension
        try:
            _, file_extension = os.path.splitext(file_path)
            file_type = file_extension.lstrip('.').lower()
        except Exception as e:
            logging.error(f"Error extracting file type: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text="Failed to determine the file type. Please check the file and try again."
            )
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        # 4. Check if file type is supported; if not, inform user and remove file
        if file_type not in supported_file_types:
            await context.bot.send_message(
                chat_id=user_id,
                text=unsupported_file_message,
                parse_mode="Markdown"
            )
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"Removed unsupported file: {file_path}")
                except Exception as e:
                    logging.error(f"Error removing file: {file_path}. {e}")
            return

        # 5. Process the document
        try:
            text = docs_process.load_document(file_path=file_path, file_type=file_type)
            logging.info(f"Processed {file_name}: {text}")
            context.user_data['documents'].append(f'{file_name}:\n{text}\n\n')
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Document successfully processed: {file_name}"
            )
        except Exception as e:
            logging.error(f"Error processing document: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text="Failed to process the document. Please try again later."
            )
        finally:
            # 6. Remove the file from disk
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"Removed file: {file_path}")
                except Exception as e:
                    logging.error(f"Error removing file: {file_path}. {e}")

    # Fallback: if a non-document (like a photo/audio/video) is sent
    elif update.message.photo or update.message.audio or update.message.video:
        await context.bot.send_message(
            chat_id=user_id,
            text=unsupported_file_message,
            parse_mode="Markdown"
        )

# Handler to handle user's messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
      
    user_message = update.message.text
    logging.info(f"from user {user_id}: {user_message}")

    try:
        # Retrieve most recent conversation ID
        conversation_id = chat_db.get_recent_conversation(user_id=user_id)
    except Exception as convo_error:
        logging.error(f"Error retrieving recent conversation for user {user_id}: {convo_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your conversation history. Please try again later.")
        return

    else:

        try:
            # Get response from LLM
            user_context = "".join(context.user_data['documents']) if "documents" in context.user_data else ""

            response = await llm.response_message(message=user_message, user_id=user_id, conversation_id=conversation_id, 
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

async def export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    # Create a filename with a timestamp
    file_path = f"users_collection_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    
    try:
        # Only allow admins to use this command
        if not chat_db.is_admin(user_id=user_id):
            await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
            return

        # Export the users collection to a CSV file using the method added in Chat_DB
        chat_db.export_users_collection_to_csv(file_path)

        # Open and send the file to the admin
        with open(file_path, 'rb') as document:
            await context.bot.send_document(chat_id=user_id, document=document)

    except Exception as e:
        logging.error(f"Error exporting users collection: {e}")
        await context.bot.send_message(chat_id=user_id, text="Failed to export users collection.")
    finally:
        # Remove the file after sending
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as delete_error:
                logging.error(f"Error deleting file {file_path}: {delete_error}")


##########################################################################################################################################
# Define a new state for the quiz upload conversation
POLL_UPLOAD = 1

# Start the poll upload conversation
async def start_poll_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not chat_db.is_admin(user_id=user_id):
        await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
        return ConversationHandler.END
    await context.bot.send_message(
        chat_id=user_id,
        text=("Please upload a CSV file containing your poll questions.\n\n"
            "Expected CSV format per row: *question, option1, option2, option3, option4, option5*\n\n"
            "- If a question has fewer than 5 options, mark the empty ones with a -.\n\n"
            "Example:\n"
            "What is your favorite color?, Red, Blue, Green, Yellow, -"
            ),
        parse_mode="Markdown"
    )
    return POLL_UPLOAD  # (You may also want to rename the state constant to POLL_UPLOAD)

# Handler to process the uploaded CSV file and send quiz polls
async def process_poll_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    document = update.message.document
    file_name = document.file_name

    _, ext = os.path.splitext(file_name)
    if ext.lower() != ".csv":
        await context.bot.send_message(chat_id=user_id, text="Please upload a valid CSV file.")
        return POLL_UPLOAD

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
    poll_number = chat_db.get_latest_poll_number() + 1

    student_ids = chat_db.get_all_students()
    recipients = student_ids + [user_id]

    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            # Skip header row
            next(reader, None)
            for row in reader:
                # Expect at least 2 columns: question and one option
                if len(row) < 2:
                    logging.warning(f"Row skipped (not enough columns): {row}")
                    continue

                question = row[0].strip()
                # Now take 5 options instead of 4
                raw_options = [opt.strip() for opt in row[1:6]]
                valid_options = [opt for opt in raw_options if opt != '-']

                if len(valid_options) < 2:
                    logging.warning(f"Row skipped (not enough valid options): {row}")
                    continue

                for recipient in recipients:
                    try:
                        msg = await context.bot.send_poll(
                            chat_id=recipient,
                            question=question,
                            options=valid_options,
                            is_anonymous=False
                        )
                        polls_sent += 1
                        poll = msg.poll
                        chat_db.store_poll_details(
                            poll_number=poll_number,
                            poll_id=poll.id,
                            question=question,
                            options=valid_options
                        )
                    except Exception as poll_error:
                        logging.error(f"Error sending poll to recipient {recipient}: {poll_error}")
                        continue
    except Exception as csv_error:
        logging.error(f"Error processing CSV file: {csv_error}")
        await context.bot.send_message(chat_id=user_id, text="Failed to process the CSV file.")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Removed CSV file: {file_path}")
            except Exception as remove_error:
                logging.error(f"Error removing CSV file: {remove_error}")

    await context.bot.send_message(
        chat_id=user_id,
        text=f"Poll upload complete. {polls_sent} poll(s) sent to {len(recipients)} recipient(s)."
    )
    return ConversationHandler.END


async def cancel_poll_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    await context.bot.send_message(chat_id=user_id, text="Poll upload cancelled.")
    return ConversationHandler.END

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_answer = update.poll_answer
    user = poll_answer.user
    poll_id = poll_answer.poll_id
    selected_options = poll_answer.option_ids
    user_id = user.id


    # If this poll is part of the ILS questionnaire:
    if "poll_map" in context.user_data and poll_id in context.user_data["poll_map"]:


        question_index = context.user_data["poll_map"][poll_id]
        if not selected_options:
            return  # No answer selected
        # Retrieve the chosen option text from the ILS question list
        chosen_option = ILS_QUESTIONS[question_index]["options"][selected_options[0]]
        chat_db.store_ils_answer(user_id, question_index, chosen_option)

        # Advance to the next ILS question
        context.user_data["ils_index"] = question_index + 1
        del context.user_data["poll_map"][poll_id]



        if context.user_data["ils_index"] < len(ILS_QUESTIONS):
            await send_ils_poll(update, context)
        else:
            await finalize_ils(update, context)

        
    else:
        # Otherwise, handle as a normal poll (for quizzes or other polls)


        poll_details = chat_db.get_poll_details(poll_id)
        if poll_details is None:
            logging.error(f"No poll details found for poll_id {poll_id}")
            return
        poll_number = poll_details.get("poll_number")
        question = poll_details.get("question")
        options = poll_details.get("options")
        if not selected_options:
            return  # No answer selected
        # Get the text corresponding to the selected option
        student_answer = options[selected_options[0]]
        chat_db.store_poll_response(
            poll_number=poll_number,
            poll_id=poll_id,
            user_id=user_id,
            student_answer=student_answer,
            question=question,
            timestamp=datetime.now()
        )
        logging.info(f"Stored normal poll response from user {user_id} for poll {poll_id}: answer={student_answer}")

        # Remove the poll details now that the response is stored
        chat_db.remove_poll_details(poll_id)




async def export_poll_responses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    file_path = f"quiz_responses_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    try:
        # Only allow admins to use this command.
        if not chat_db.is_admin(user_id=user_id):
            await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
            return

        # Export the quiz responses collection to a CSV file.
        chat_db.export_poll_responses_collection_to_csv(file_path)

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

async def send_ils_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id if update.effective_chat is not None else update.effective_user.id

    i = context.user_data["ils_index"]
    if i >= len(ILS_QUESTIONS):
        await finalize_ils(update, context)
        return

    question_data = ILS_QUESTIONS[i]
    question_text = question_data["question"]
    options = question_data["options"]

    msg = await context.bot.send_poll(
        chat_id=user_id,
        question=question_text,
        options=options,
        is_anonymous=False  # so we can track the response
    )
    poll_id = msg.poll.id
    context.user_data["poll_map"][poll_id] = i


async def finalize_ils(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id if update.effective_chat is not None else update.effective_user.id
    answers = chat_db.get_ils_answers(user_id)  # Retrieves a list of answers in order

    # Mapping each question index to a dimension:
    DIMENSION_MAP = {
        0: "AR",  1: "SI",  2: "VV",  3: "SG",  4: "AR",  5: "SI",  6: "VV",  7: "SG",  8: "AR",  9: "SI",
        10: "VV", 11: "SG", 12: "AR", 13: "SI", 14: "VV", 15: "SG", 16: "AR", 17: "SI", 18: "VV", 19: "SG",
        20: "AR", 21: "SI", 22: "VV", 23: "SG", 24: "AR", 25: "SI", 26: "VV", 27: "SG", 28: "AR", 29: "SI",
        30: "VV", 31: "SG", 32: "AR", 33: "SI", 34: "VV", 35: "SG", 36: "AR", 37: "SI", 38: "VV", 39: "SG",
        40: "AR", 41: "SI", 42: "VV", 43: "SG"
    }

    # Initialize scores for each dimension
    scores = {"AR": 0, "SI": 0, "VV": 0, "SG": 0}

    # For each question, compare the answer with the first option (assumed to be the positive side)
    for i, answer in enumerate(answers):
        dim = DIMENSION_MAP.get(i)
        if answer == ILS_QUESTIONS[i]["options"][0]:
            scores[dim] += 1
        else:
            scores[dim] -= 1

    # Define a helper to interpret the score for each dimension
    def interpret(dim, score):
        if dim == "AR":
            return "Active" if score > 0 else "Reflective"
        elif dim == "SI":
            return "Sensing" if score > 0 else "Intuitive"
        elif dim == "VV":
            return "Visual" if score > 0 else "Verbal"
        elif dim == "SG":
            return "Sequential" if score > 0 else "Global"

    # Build a result dictionary with a more descriptive result per dimension
    results = {
        "Active/Reflective": interpret("AR", scores["AR"]),
        "Sensing/Intuitive": interpret("SI", scores["SI"]),
        "Visual/Verbal": interpret("VV", scores["VV"]),
        "Sequential/Global": interpret("SG", scores["SG"])
    }

    # Create a summary text for the user
    result_text = "\n".join([
        f"• Active/Reflective: {results['Active/Reflective']} (score: {scores['AR']})",
        f"• Sensing/Intuitive: {results['Sensing/Intuitive']} (score: {scores['SI']})",
        f"• Visual/Verbal: {results['Visual/Verbal']} (score: {scores['VV']})",
        f"• Sequential/Global: {results['Sequential/Global']} (score: {scores['SG']})"
    ])

    final_message = (
        "✅ *Learning Styles Questionnaire Complete!*\n\n"
        "Your results:\n" + result_text +
        "\n\nYou are now authenticated to use the chatbot. Type /new to begin chatting!"
    )

    # Mark the user as authenticated
    chat_db.authenticate_user(user_id)

    # Build a merged analysis dictionary
    ils_analysis = {
    "Active/Reflective": {"style": results["Active/Reflective"], "score": scores["AR"]},
    "Sensing/Intuitive": {"style": results["Sensing/Intuitive"], "score": scores["SI"]},
    "Visual/Verbal": {"style": results["Visual/Verbal"], "score": scores["VV"]},
    "Sequential/Global": {"style": results["Sequential/Global"], "score": scores["SG"]}
    }

    # Update the user's record in the users collection with the merged analysis
    chat_db.users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"start_ils_analysis": ils_analysis}}
    )

    await context.bot.send_message(chat_id=user_id, text=final_message, parse_mode="Markdown")

    # Clean up ILS-related state
    chat_db.clear_ils_answers(user_id)
    context.user_data.pop("ils_index", None)
    context.user_data.pop("poll_map", None)

async def daily_initiation_task():
    student_ids = chat_db.get_all_users()  # Retrieves list of user_ids for non-admin users
    for user_id in student_ids:
        try:
            # Generate a conversation starter for the user based on their latest 10 messages
            starter = await llm.starter_message(user_id=user_id)
            # Send the generated message to the user; 'app' is your Application instance

            chat_db.add_ai_message(message=starter, user_id=user_id)

            await reply_to_daily(app=app,user_id=user_id, response=starter)
        except Exception as e:
            logging.error(f"Error sending daily conversation starter to user {user_id}: {e}")

    # Schedule the next run at a random time between 8:00 AM and 9:00 PM
    next_run = get_next_run_time()
    scheduler.add_job(daily_initiation_task, 'date', run_date=next_run, id='daily_initiation_task')
    logging.info(f"Next daily initiation scheduled for {next_run}")

    # Notify admins about the next scheduled run
    await notify_admins(next_run)

async def notify_admins(next_run):
    # Get all admin user IDs from the database
    admin_ids = chat_db.get_all_admins()  # Assuming this function exists as shown
    for admin_id in admin_ids:
        try:
            await app.bot.send_message(
                chat_id=admin_id,
                text=f"Daily interaction scheduled for: {next_run}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error sending schedule info to admin {admin_id}: {e}")

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_chat.id
    
    # Check if the user is an admin
    if not chat_db.is_admin(user_id=admin_id):
        await context.bot.send_message(chat_id=admin_id, text="Unauthorized: This command is for admins only.")
        return

    # Ensure an announcement message was provided
    if not context.args:
        await context.bot.send_message(chat_id=admin_id, text="Usage: /announce <announcement message>")
        return

    # Combine the arguments to form the announcement message
    announcement = "*[Announcement]*\n"
    announcement += " ".join(context.args)

    
    # Retrieve all users from the database
    all_users = chat_db.get_all_users()
    sent_count = 0

    # Loop over each user and send the announcement
    for user in all_users:
        try:
            await context.bot.send_message(chat_id=user, text=announcement, parse_mode="Markdown")
            sent_count += 1
        except Exception as e:
            logging.error(f"Failed to send announcement to user {user}: {e}")
    
    # Confirm to the admin that the announcement was sent
    await context.bot.send_message(chat_id=admin_id, text=f"Announcement sent to {sent_count} users.")

async def analyse_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_chat.id
    if not chat_db.is_admin(user_id=admin_id):
        await context.bot.send_message(chat_id=admin_id, text="Unauthorized: Only admins can use this command.")
        return

    await context.bot.send_message(chat_id=admin_id, text="Starting comprehensive analysis for all users...")
    user_ids = chat_db.get_all_users()


    # Regular expression to parse the expected report format.
    pattern = (
        r"Active/Reflective:\s*(.+?)\s+\(score:\s*(\d+)\).*?"
        r"Sensing/Intuitive:\s*(.+?)\s+\(score:\s*(\d+)\).*?"
        r"Visual/Verbal:\s*(.+?)\s+\(score:\s*(\d+)\).*?"
        r"Sequential/Global:\s*(.+?)\s+\(score:\s*(\d+)\)"
    )

    for uid in user_ids:
        messages = chat_db.get_all_conversation(user_id=uid)
        if not messages:
            await context.bot.send_message(chat_id=admin_id, text=f"User {uid}: No chat history available.")
            continue
        try:
            report = await llm.analyse_all_message(user_id=uid)

            if "No chat history available" in report:
                await context.bot.send_message(chat_id=admin_id, text=f"User {uid}: Skipped (no chat history).")
                continue
            
            match = re.search(pattern, report, re.DOTALL)
            if match:
                # Parse out each dimension's style and score
                ar_analysis = {"style": match.group(1).strip(), "score": int(match.group(2))}
                si_analysis = {"style": match.group(3).strip(), "score": int(match.group(4))}
                vv_analysis = {"style": match.group(5).strip(), "score": int(match.group(6))}
                sg_analysis = {"style": match.group(7).strip(), "score": int(match.group(8))}
                
                # Merge into one dictionary
                ils_analysis = {
                    "Active/Reflective": ar_analysis,
                    "Sensing/Intuitive": si_analysis,
                    "Visual/Verbal": vv_analysis,
                    "Sequential/Global": sg_analysis
                }
                
                # Update the user's record with the merged analysis
                chat_db.users_collection.update_one(
                    {"user_id": uid},
                    {"$set": {"chat_ils_analysis": ils_analysis}}
                )
                await context.bot.send_message(chat_id=admin_id, text=f"User {uid}: Updated analysis.")
            else:
                await context.bot.send_message(chat_id=admin_id, text=f"User {uid}: Failed to parse analysis report.")
        except Exception as e:
            await context.bot.send_message(chat_id=admin_id, text=f"User {uid}: Analysis failed with error: {e}")

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
    export_users_handler = CommandHandler("export_users", export_users)
    announce_handler = CommandHandler("announce", announce)
    analyse_all_handler = CommandHandler("analyse_all", analyse_all)
    clear_docs_handler = CommandHandler('clear', clear_documents)

    poll_upload_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('upload_poll', start_poll_upload)],
        states={
            POLL_UPLOAD: [MessageHandler(filters.Document.ALL, process_poll_csv)]
        },
        fallbacks=[CommandHandler('cancel', cancel_poll_upload)]
    )
    application.add_handler(poll_upload_conv_handler)

    # Poll answer handler remains similar
    poll_answer_handler = PollAnswerHandler(handle_poll_answer)
    application.add_handler(poll_answer_handler)
    
    # Replace the export quiz command with export poll command
    export_poll_handler = CommandHandler("export_poll", export_poll_responses)
    application.add_handler(export_poll_handler)
    
    application.add_handler(query_handler)
    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(analyse_handler)
    application.add_handler(misconception_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)
    application.add_handler(export_chat_handler)
    application.add_handler(export_feedback_handler)
    application.add_handler(export_users_handler)
    application.add_error_handler(error_handler)
    application.add_handler(announce_handler)
    application.add_handler(analyse_all_handler)
    application.add_handler(clear_docs_handler)

    # Set menu commands
    await set_command_menu(application.bot)

    # Assign the Application instance to a global variable 'app'
    global app
    app = application

    # Schedule the first daily initiation at a random time between 8 AM and 9 PM
    first_run = get_next_run_time()
    scheduler.add_job(daily_initiation_task, 'date', run_date=first_run, id='daily_initiation_task')
    scheduler.start()
    logging.info(f"First daily initiation scheduled for {first_run}")
    await notify_admins(first_run)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
