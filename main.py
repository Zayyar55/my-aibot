import os
import requests
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Tokens
HF_TOKEN = "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"
TG_TOKEN = "8774327296:AAHfzzOTEh0eShFmCLH78fTHR3XVNgk5qFM"
# Using a more stable model
API_URL = "https://api-inference.huggingface.co/models/google/gemma-1.1-7b-it"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Port Binding for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def query_ai(text):
    payload = {"inputs": text, "parameters": {"max_new_tokens": 500}}
    
    # Simple retry logic for stability
    for _ in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].strip()
            time.sleep(2)
        except:
            continue
            
    return "The AI is busy or loading. Please try again in 30 seconds."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # Initial response to show the bot is working
    status_msg = await update.message.reply_text("Thinking... ⏳")
    
    ai_response = query_ai(user_text)
    
    # Update with the final AI response
    await status_msg.edit_text(ai_response)

if __name__ == '__main__':
    # Start the server to keep Render alive
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Start Telegram Polling
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting...")
    app.run_polling()
