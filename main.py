import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Tokens
HF_TOKEN = "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"
TG_TOKEN = "8774327296:AAHfzzOTEh0eShFmCLH78fTHR3XVNgk5qFM"
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Simple Server for Render Port Binding
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def query_ai(text):
    payload = {"inputs": f"<s>[INST] {text} [/INST]"}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()
        if isinstance(result, list):
            return result[0]['generated_text'].split('[/INST]')[-1].strip()
        return "AI is processing..."
    except:
        return "Error."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    ai_response = query_ai(user_text)
    await update.message.reply_text(ai_response)

if __name__ == '__main__':
    # Start health check server in a separate thread
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Start Telegram Bot
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is starting...")
    app.run_polling()
