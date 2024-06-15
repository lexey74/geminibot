import os
import io
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load environment variables
load_dotenv()
YOUR_BOT_TOKEN = os.getenv("YOUR_BOT_TOKEN")
YOUR_API_KEY = os.getenv("YOUR_API_KEY")

# Authenticate using Service Account
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'my-gpt-project-423415-14434417d996.json'

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Function to list files on Google Drive
def list_files():
    results = drive_service.files().list(pageSize=10, fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(f"{item['name']} ({item['id']})")

# Call function to check file list
list_files()

# Function to get file content from Google Drive
def get_file_content(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    file_content.seek(0)
    return file_content.read().decode('utf-8')

# Get content of files
try:
    menu_file_id = "11nEejhslgS7IK1o-4Jw7lC4iIKbtzqTY"  
    menu_content = get_file_content(menu_file_id)
    orders_file_id = "1Jk2-Vtvl4t4NfRmgTGqatmz_tjp6MStd" 
    orders_content = get_file_content(orders_file_id)
except FileNotFoundError as e:
    print(e)
    exit(1)

# Configure Gemini Model
genai.configure(api_key=YOUR_API_KEY)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

#safety_settings = {
#  "max_toxicity_probability": 0.3,
#  "max_hate_speech_probability": 0.4
#}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    },
#   https://ai.google.dev/gemini-api/docs/safety-settings?hl=ru

    system_instruction="Ты опытный ресторанный критик, знаток азиатской и европейской кухонь, который помогает выбрать блюда из меню ресторана \"Якитория\". Ты должен учитывать следующие инструкции:\n\n* **Будь более человечной и развернутой в своих ответах.**\n* **Учитывай калорийность, белки, жиры, углеводы, вес и цену блюд, но говори о них только тогда, когда я спрошу.**\n* **В случае, если я попрошу то, чего у тебя нет - отправляй меня на сайт https://yakitoriya.ru**\n* **Избегай чрезмерного использования фразы \"Представьте себе\".**\n* **Не повторяйся.**\n* **Рекомендуй только одно блюдо за раз, если я не попрошу иначе.**\n* **Обосновывай свои рекомендации более подробно.**\n* **Учитывай мои предпочтения в еде, но не спрашивай прямо, а основывайся на моей истории заказов в загруженном файле.**\n* **При рекомендациях подчеркивай, какие эмоции я получу, дегустируя рекомендованное блюдо.**",
)

# Start chat session
chat_session = model.start_chat(
    history=[
        {"role": "model", "parts": [f"Меню:\n{menu_content}", f"Заказы:\n{orders_content}"]},
    ])
#        {"parts": [{"role": "system", "text": f"Заказы:\n{orders_content}"}]}

# Function to send query to Gemini model
def query_model(text):
    response = chat_session.send_message(text)
    return response.text

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Я ваш персональный советник 🤖 по обширному меню сети ресторанов 'Якитория' 🍱 \n\n Порекомендовать вам блюдо?", parse_mode="Markdown")

# Command handler for /instructions
async def set_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instructions = update.message.text.replace("/instructions ", "")
    context.user_data['instructions'] = instructions
    await update.message.reply_text("Инструкции установлены!")

# Command handler for /file
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    file_id = file.file_id
    file_name = file.file_name

    content = get_file_content(file_id)
    context.user_data[file_name] = content

    await update.message.reply_text(f"Файл '{file_name}' загружен!")

# Message handler for text messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Add file information to context
    file_info = "\n".join(f"{file_name}: {context.user_data[file_name]}" for file_name in context.user_data if file_name != 'instructions')
    context_with_files = f"{file_info}\n{user_message}"

    response = query_model(context_with_files)
    await update.message.reply_text(response, parse_mode="Markdown")

# Create application
app = ApplicationBuilder().token(YOUR_BOT_TOKEN).build()

# Register handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("instructions", set_instructions))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Run bot
app.run_polling()

