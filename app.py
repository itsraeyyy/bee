import os
import telegram
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import openai

# Set up OpenAI API key
openai.api_key = "YOUR_API_KEY_HERE"

# Set up Telegram bot
bot = telegram.Bot(token="YOUR_BOT_TOKEN_HERE")
updater = Updater(token="YOUR_BOT_TOKEN_HERE")
dispatcher = updater.dispatcher

# Define function to handle /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Studybee🐝! Upload a file or image to get started.")

# Define function to handle file/image uploads
def file_upload(update, context):
    file_id = None
    file_name = None
    file_extension = None

    if update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name
        file_extension = os.path.splitext(file_name)[1].lower()
    elif update.message.photo:
        # Get the largest available photo size
        photo = max(update.message.photo, key=lambda x: x.width)
        file_id = photo.file_id
        file_name = f"{photo.file_id}.jpg"
        file_extension = ".jpg"

    file = bot.get_file(file_id)
    file.download(file_name)

    # Convert file to text if possible using OpenAI API
    if file_extension in [".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".gif"]:
        with open(file_name, "rb") as f:
            file_bytes = f.read()

        response = openai.Completion.create(
            engine="davinci",
            prompt=f"Convert this file to text:\n{file_bytes}",
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=0.5,
        )
        text = response.choices[0].text.strip()
    else:
        text = f"File type {file_extension} not supported for text conversion."

    context.user_data["file_name"] = file_name
    context.user_data["text"] = text
    context.user_data["response"] = None
    context.bot.send_message(chat_id=update.effective_chat.id, text="File uploaded successfully! What would you like to do next?")

# Define function to handle chat requests
def chat(update, context):
    user_input = update.message.text
    text = context.user_data["text"]
    if context.user_data["response"] is not None:
        response = context.user_data["response"]
        prompt = f"{text}\n\nUser: {user_input}\nStudybee🐝: {response}"
    else:
        prompt = f"{text}\n\nUser: {user_input}\nStudybee🐝:"
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.5,
    )
    context.user_data["response"] = response.choices[0].text.strip()
    context.bot.send_message(chat_id=update.effective_chat.id, text=context.user_data["response"])

# Define function to handle quiz requests
def quiz(update, context):
    text = context.user_data["text"]
    response = context.user_data["response"]
    quiz_text = text if response is None else f"{text}\n\n{response}"

    # Generate quiz using OpenAI API
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Generate a quiz based on this text:\n{quiz_text}",
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.5,
    )
    quiz = response.choices[0].text.strip()

    context.bot.send_message(chat_id=update.effective_chat.id, text=quiz)

# Define function to handle summary requests
def summary(update, context):
    text = context.user_data["text"]
    response = context.user_data["response"]
    summary_text = text if response is None else f"{text}\n\n{response}"
    
    # Generate summary using OpenAI API
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Generate a summary of this text:\n{summary_text}",
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.5,
    )
    summary = response.choices[0].text.strip()
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=summary)

# Define function to handle about requests
def about(update, context):
    about_text = "Studybee🐝 is a Telegram bot powered byOpenAI that can convert your uploaded PDF, DOCX, TXT files, as well as images, into text for easy studying. It can also chat with you about the text, generate quizzes based on the text, and summarize the text for you. Give it a try!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=about_text)

# Set up handlers for different commands
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

file_upload_handler = MessageHandler(Filters.document | Filters.photo, file_upload)
dispatcher.add_handler(file_upload_handler)

chat_handler = MessageHandler(Filters.text, chat)
dispatcher.add_handler(chat_handler)

quiz_handler = CommandHandler('quiz', quiz)
dispatcher.add_handler(quiz_handler)

summary_handler = CommandHandler('summary', summary)
dispatcher.add_handler(summary_handler)

about_handler = CommandHandler('about', about)
dispatcher.add_handler(about_handler)

# Start the bot
updater.start_polling()