import os
import requests
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- API TOKENS ---
HF_TOKEN = "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"
TG_TOKEN = "8774327296:AAHfzzOTEh0eShFmCLH78fTHR3XVNgk5qFM"

# Stable models to rotate (Free tier backup)
MODELS = [
    "mistralai/Mistral-7B-Instruct-v0.2",
    "HuggingFaceH4/zephyr-7b-beta",
    "google/gemma-1.1-7b-it"
]

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- RENDER PORT BINDING ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Status: Online")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- AI QUERY LOGIC ---
def query_ai(text):
    for model_id in MODELS:
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        payload = {
            "inputs": f"User: {text}\nAssistant:",
            "parameters": {"max_new_tokens": 400, "return_full_text": False}
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].strip()
            continue
        except:
            continue
            
    return "All AI models are currently warming up. Please send your message again in 20 seconds."

# --- TELEGRAM BOT LOGIC ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    status_msg = await update.message.reply_text("Thinking... 🔍")
    ai_response = query_ai(user_text)
    await status_msg.edit_text(ai_response)

if __name__ == '__main__':
    threading.Thread(target=run_health_check, daemon=True).start()
    print("Bot is launching...")
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
