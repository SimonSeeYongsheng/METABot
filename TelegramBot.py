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
from telegram.ext import CallbackQueryHandler

import llm_module # module for the LLM

import chat_database # module for the chat database
import prompts_database # module for the doc database
import docs_processor # module for processing docs

from datetime import datetime

import telegramify_markdown # module to convert markdown to markdownV2 response
from telegramify_markdown.customize import markdown_symbol
from telegramify_markdown.interpreters import BaseInterpreter, MermaidInterpreter
from telegramify_markdown.type import ContentTypes

load_dotenv() # Load environment variables from .env file

TELE_BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')
FILE_DRIVE = os.environ.get("FILE_DRIVE")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

chat_db = chat_database.Chat_DB()
prompts_db = prompts_database.Prompts_DB(chat_db = chat_db)
llm = llm_module.LLM(Chat_Database=chat_db)
docs_process = docs_processor.Docs_processor()

supported_file_types = ["pdf", "txt", "py", "html", "js", "css", "htm"]

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

new_message = (
    "Click on your query category 👇🏼\n"
    "Press /cancel if you don't want to *make a new query*"
)

unsupported_file_message = (
    "🚫 *Unsupported File Type* 🚫"
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
    "📄 PDF (e.g., `.pdf`)\n"
    "📜 Text (e.g., `.txt` or `plain text` in this chat)\n"
    "🐍 Python Code (e.g., `.py` files)\n\n"
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
    "🔄 A new conversation has started! How can I assist you with your assignments today?\n\n"
    "Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the assignment requirements?\n"
    "📝 Are you unsure about how to approach or structure the assignment?\n"
    "💻 Are you facing issues with your code or logic?\n\n"
    "Please type your query below by *replying to this message*, and I'll do my best to help!"
)

guidance_query_message = (
    "🔄 A new conversation has started! How can I assist you with your assignments today?\n\n"
    "Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the assignment requirements?\n"
    "📝 Are you unsure about how to approach or structure the assignment?\n"
    "💻 Are you facing issues with your code or logic?\n\n"
    "Please type your query below by replying to this message, and I'll do my best to help!"
)

teach_contextual_info_message_bold = (
    "Please send any relevant information about the lecture materials, concepts, or topic by *replying to this message*.\n\n"
    "You can upload a file in one of the following formats:\n"
    "📄 PDF (e.g., `.pdf`)\n"
    "📜 Text (e.g., `.txt` or `plain text` in this chat)\n"
    "🐍 Python Code (e.g., `.py` files, if applicable)\n\n"
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
    "🔄 *A new conversation has started!* How can I assist you today?\n\n"
    "Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the lecture materials or concepts?\n"
    "🔍 Do you need clarification on a specific topic covered in the lecture?\n"
    "💡 Are there any knowledge gaps you'd like to address?\n\n"
    "Please type your query below by *replying to this message*, and I'll do my best to help!"
)


teach_query_message = (
    "🔄 A new conversation has started! How can I assist you today?\n\n"
    "Feel free to ask anything specific so I can assist you effectively.\n\nFor example:\n"
    "❓ Do you have questions about the lecture materials or concepts?\n"
    "🔍 Do you need clarification on a specific topic covered in the lecture?\n"
    "💡 Are there any knowledge gaps you'd like to address?\n\n"
    "Please type your query below by replying to this message, and I'll do my best to help!"
)

first_feedback_message = (
    "This response has never been *given feedback* before.\n\n"
    "If it was helpful, *click 👍*. If not, *click 👎*.\n\n"
    "Your feedback helps us improve!"
)

second_feedback_message = (
    "This response was *generated for a query similar to yours* made by another user.\n\n"
    "It currently has *{likes} 👍 and {dislikes} 👎*.\n\n"
    "If you find this response helpful, please *click 👍*. If not, please *click 👎*.\n\n"
    "Your feedback helps us improve!"
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

    try:

        keyboard = [
            [InlineKeyboardButton("Teach 📚", callback_data="category_teach")],
            [InlineKeyboardButton("Guide 🧭", callback_data="category_guide")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user_id, text=new_message, reply_markup=reply_markup, parse_mode="Markdown")
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

async def feedback_with_callback_new(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id : str, user_message : str, response : str, feedback_message : str):

    if context.user_data['category'] == "guide":
        object_id = chat_db.input_callback_data(
                            prompt=user_message,
                            response=response,
                            assignment=context.user_data['assignment'],
                            conversation_id=context.user_data['conversation_id']

                            )

    else:
        object_id = chat_db.input_callback_data(
                            prompt=user_message,
                            response=response,
                            assignment=context.user_data['category'],
                            conversation_id=context.user_data['conversation_id']
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
            chat_id=user_id,
            text=feedback_message,
            reply_markup=reply_markup,  # Forces the reply
            parse_mode="Markdown"
        )
    
async def feedback_with_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id : str, response_object_id: str,
                                feedback_message : str, user_message : str, response : str):
    
    if context.user_data['category'] == "guide":
        object_id = chat_db.input_callback_data(
                            prompt=user_message,
                            response=response,
                            assignment=context.user_data['assignment'],
                            conversation_id=context.user_data['conversation_id']
                            )

    else:
        object_id = chat_db.input_callback_data(
                            prompt=user_message,
                            response=response,
                            assignment=context.user_data['category'],
                            conversation_id=context.user_data['conversation_id']
                            )

    metadata = f"{{sentiment}}|{context.user_data['category'][0]}|{object_id}|{response_object_id}"

    keyboard = [
        [
        InlineKeyboardButton("👍", callback_data=metadata.format(sentiment='like')),
        InlineKeyboardButton("👎", callback_data=metadata.format(sentiment = 'dislike')),
        ]
    ]
            
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a message forcing the user to reply
    await context.bot.send_message(
            chat_id=user_id,
            text=feedback_message,
            reply_markup=reply_markup,  # Forces the reply
            parse_mode="Markdown"
        )

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

            context.user_data['documents'] = [] # Clear documents

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

            context.user_data['documents'] = [] # Clear documents

            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=guidance_message_bold,
                reply_markup=ForceReply(selective=True),  # Forces the reply
                parse_mode="Markdown"
            )
            return
        
        case "query_teach":
            # Start a new conversation
            convo_id = chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
            logging.info(f"New conversation started for user {user_id} (NUSNET ID: {nusnet_id}).")

            context.user_data['category'] = 'teach' # Storing metadata of user's intention
            context.user_data['conversation_id'] = convo_id # Storing conversation id
            
            # Send a message forcing the user to reply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=teach_query_message_bold ,
                reply_markup=ForceReply(selective=True),  # Forces the reply
                parse_mode="Markdown"
                )
            return

        case "query_guide":
            # Start a new conversation
            convo_id = chat_db.start_new_conversation(nusnet_id=nusnet_id, message="A new conversation has started")
            logging.info(f"New conversation started for user {user_id} (NUSNET ID: {nusnet_id}).")

            context.user_data['category'] = 'guide' # Storing metadata of user's intention
            context.user_data['conversation_id'] = convo_id # Storing conversation id

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
                    prompt, response, conversation_id = chat_db.get_callback_data_teach(object_id)
                    object_id = chat_db.input_feedback_teach(nusnet_id=nusnet_id, prompt=prompt, response=response, sentiment=sentiment)
                    prompts_db.store_prompts(prompt=prompt, assignment="teach", object_id=object_id)
                    await context.bot.send_message(chat_id=user_id, text="Thank you so much for your feedback! 😊")
                    return

                case "guide":
                    prompt, response, assignment, conversation_id = chat_db.get_callback_data_guide(object_id)
                    object_id = chat_db.input_feedback_guide(nusnet_id=nusnet_id, prompt=prompt, response=response, assignment=assignment, sentiment=sentiment)
                    prompts_db.store_prompts(prompt=prompt, assignment=assignment, object_id=object_id)
                    await context.bot.send_message(chat_id=user_id, text="Thank you so much for your feedback! 😊")
                    return
                
                case "t":
                    response_object_id = metadata_parts[3]
                    prompt, response, conversation_id = chat_db.get_callback_data_teach(object_id)
                    chat_db.update_feedback_teach(nusnet_id=nusnet_id, sentiment=sentiment, object_id=response_object_id)
                    await context.bot.send_message(chat_id=user_id, text="Thank you so much for your feedback! 😊")

                    if sentiment == "like":
                        return
                    
                    elif "conversation_id" in context.user_data:


                        if context.user_data['conversation_id'] == conversation_id:

                            try:
                            # Get response from LLM
                                await context.bot.send_message(chat_id=user_id, text="Generating new response for user...")
                                user_context = "".join(context.user_data['documents']) if "documents" in context.user_data else ""
                                response = await llm.response_message(message=prompt, nusnet_id=nusnet_id, conversation_id=conversation_id, 
                                                                intention = context.user_data['category'], user_context = user_context)
                            except Exception as llm_error:
                                logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
                                await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
                                return
                            
                            await reply_to_query(update=update, context=context, user_id=user_id, response=response)
                            await feedback_with_callback_new(update=update, context=context, user_id=user_id, user_message=prompt, 
                                                            response=response, feedback_message=first_feedback_message)

                        else:
                            await context.bot.send_message(chat_id=user_id, text="Unable to generate response to the previous conversation. Please start a new conversation by sending /new.")
                    
                    else:
                        await context.bot.send_message(chat_id=user_id, text="Unable respond to the previous conversation. Please start a new conversation by sending /new.")

                    return


                case "g":
                    response_object_id = metadata_parts[3]
                    prompt, response, assignment, conversation_id = chat_db.get_callback_data_guide(object_id)
                    chat_db.update_feedback_guide(nusnet_id=nusnet_id, sentiment=sentiment, object_id=response_object_id)
                    await context.bot.send_message(chat_id=user_id, text="Thank you so much for your feedback! 😊")

                    if sentiment == "like":
                        return

                    elif "conversation_id" in context.user_data:
                        if context.user_data['conversation_id'] == conversation_id:

                            try:
                            # Get response from LLM
                                await context.bot.send_message(chat_id=user_id, text="Generating new response for user...")
                                user_context = "".join(context.user_data['documents']) if "documents" in context.user_data else ""
                                response = await llm.response_message(message=prompt, nusnet_id=nusnet_id, conversation_id=conversation_id, 
                                                                intention = context.user_data['category'], user_context = user_context)
                            except Exception as llm_error:
                                logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
                                await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
                                return
                            
                            await reply_to_query(update=update, context=context, user_id=user_id, response=response)
                            await feedback_with_callback_new(update=update, context=context, user_id=user_id, user_message=prompt, 
                                                            response=response, feedback_message=first_feedback_message)
                        
                        else:
                            await context.bot.send_message(chat_id=user_id, text="Unable respond to the previous conversation. Please start a new conversation by sending /new.")
                    else:
                        await context.bot.send_message(chat_id=user_id, text="Unable respond to the previous conversation. Please start a new conversation by sending /new.")
                    return

# Handler for handling teach feedback export
async def export_teach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command to export the teach feedback collection."""
    user_id = update.effective_chat.id
    file_path = f"feedback_teach_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    try:
        # Check if the user is an admin
        if not chat_db.is_admin(user_id=user_id):
            await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
            return

        # Export the teach feedback collection to a CSV file
        chat_db.export_teach_collection_to_csv(file_path)

        # Send the file to the admin
        with open(file_path, 'rb') as document:
            await context.bot.send_document(chat_id=user_id, document=document)
    except Exception as e:
        logging.error(f"Error exporting teach feedback collection: {e}")
        await context.bot.send_message(chat_id=user_id, text="Failed to export teach feedback collection.")
    finally:
        # Ensure the file is deleted after being sent
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as delete_error:
                logging.error(f"Error deleting file {file_path}: {delete_error}")

# Handler for handling guide feedback export
async def export_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export_guide command to export the guide feedback collection."""
    user_id = update.effective_chat.id
    file_path = f"feedback_guide_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    try:
        # Check if the user is an admin
        if not chat_db.is_admin(user_id=user_id):
            await context.bot.send_message(chat_id=user_id, text="Unauthorized access. This command is for admins only.")
            return

        # Export the guide feedback collection to a CSV file
        chat_db.export_guide_collection_to_csv(file_path)

        # Send the file to the admin
        with open(file_path, 'rb') as document:
            await context.bot.send_document(chat_id=user_id, document=document)
    except Exception as e:
        logging.error(f"Error exporting guide feedback collection: {e}")
        await context.bot.send_message(chat_id=user_id, text="Failed to export guide feedback collection.")
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
                await context.bot.send_message(chat_id=user_id, text="Your plain text has been successfully processed.")

            if update.message.caption:
                logging.info(f"User reply: {update.message.caption}")
                context.user_data['documents'].append(f"User Context:\n{update.message.caption}\n\n")
                await context.bot.send_message(chat_id=user_id, text="Your plain text has been successfully processed.")

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

        case original_question if original_question == guidance_query_message or original_question == teach_query_message:

            user_id = update.effective_chat.id
            # telegram_handle = update.effective_user.username

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
            
            if context.user_data['category'] == "guide":
                result = prompts_db.query_prompts(user_query=user_message, assignment_filter=context.user_data["assignment"])
            else:
                result = prompts_db.query_prompts(user_query=user_message, assignment_filter=context.user_data["category"])
            
            if result:
                
                if context.user_data["category"] == "teach":
                    best_object_id, best_response, best_like, best_dislike = chat_db.get_saved_response_teach_list(result)

                elif context.user_data["category"] == "guide":
                    print("RESULT", result)
                    best_object_id, best_response, best_like, best_dislike = chat_db.get_saved_response_guide_list(result)

                await reply_to_query(update=update, context=context, user_id=user_id, response=best_response)
                chat_db.add_human_message(message=user_message, nusnet_id=nusnet_id)
                chat_db.add_ai_message(message=best_response, nusnet_id=nusnet_id)
                await feedback_with_callback(update=update, context=context, user_id=user_id, response_object_id=best_object_id, 
                                 feedback_message=second_feedback_message.format(likes=best_like, dislikes=best_dislike),
                                 user_message=user_message, response=best_response)
            else:

                try:
                    # Get response from LLM
                    user_context = "".join(context.user_data['documents']) if "documents" in context.user_data else ""
                    response = await llm.response_message(message=user_message, nusnet_id=nusnet_id, conversation_id=conversation_id, 
                                                        intention = context.user_data['category'], user_context = user_context)
                    

                except Exception as llm_error:
                    logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
                    await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
                    return
                
                await reply_to_query(update=update, context=context, user_id=user_id, response=response)

                await feedback_with_callback_new(update=update, context=context, user_id=user_id, user_message=user_message, response=response, feedback_message=first_feedback_message)

# Handler to capture the user's attachments
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    await context.bot.send_message(chat_id=user_id, text="Please attach the documents *by replying to* the instructional message.", parse_mode="Markdown")

# Handler to handle user's messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if "category" not in context.user_data:
        await context.bot.send_message(chat_id=user_id, text="Please start a new conversation by sending /new.")
        return
    
    user_message = update.message.text
    logging.info(f"Message received from user {user_id}: {user_message}")

    try:
        # Retrieve most recent conversation ID
        conversation_id = chat_db.get_recent_conversation(nusnet_id=nusnet_id)
    except Exception as convo_error:
        logging.error(f"Error retrieving recent conversation for NUSNET ID {nusnet_id}: {convo_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while retrieving your conversation history. Please try again later.")
        return

    try:
        # Get response from LLM
        response = await llm.response_message(message=user_message, nusnet_id=nusnet_id, conversation_id=conversation_id, 
                                                        intention = context.user_data['category'], user_context = "")
    except Exception as llm_error:
        logging.error(f"Error generating LLM response for user {user_id}: {llm_error}")
        await context.bot.send_message(chat_id=user_id, text="An error occurred while processing your message. Please try again later.")
        return
    
    await reply_to_query(update=update, context=context, user_id=user_id, response=response)
    await feedback_with_callback_new(update=update, context=context, user_id=user_id, user_message=user_message, response=response, feedback_message=first_feedback_message)
    
# Handler for cancel
async def cancel(update: object, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    await context.bot.send_message(chat_id=user_id, text="No worries 😅. Please use /new to *make a new query*", parse_mode="Markdown")


# Error handler for all general errors
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
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



async def main():

    # Build the bot application
    application = ApplicationBuilder().token(TELE_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    new_convo_handler = CommandHandler('new', new)
    analyse_handler = CommandHandler("analyse", analyse)
    misconception_handler = CommandHandler("uncover", misconception)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    document_handler = MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), handle_document)
    reaction_handler = CallbackQueryHandler(handle_reactions)
    export_chat_handler = CommandHandler("export_chat", export_chat)
    export_teach_handler = CommandHandler("export_teach", export_teach)
    export_guide_handler = CommandHandler("export_guide", export_guide)

    application.add_handler(MessageHandler(filters.REPLY & (~filters.COMMAND), capture_reply))  # Handles ForceReply responses

    application.add_handler(reaction_handler)
    application.add_handler(start_handler)
    application.add_handler(new_convo_handler)
    application.add_handler(analyse_handler)
    application.add_handler(misconception_handler)
    application.add_handler(message_handler)
    application.add_handler(document_handler)
    application.add_handler(reaction_handler)
    application.add_handler(export_chat_handler)
    application.add_handler(export_teach_handler)
    application.add_handler(export_guide_handler)


    application.add_error_handler(error_handler)

    # Set menu commands
    await set_command_menu(application.bot)

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
