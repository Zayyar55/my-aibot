import os
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Tokens
HF_TOKEN = "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"
TG_TOKEN = "8774327296:AAHfzzOTEh0eShFmCLH78fTHR3XVNgk5qFM"
# ပိုမိုမြန်ဆန်ပြီး Error နည်းတဲ့ Model ကို သုံးထားပါတယ်
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Render အတွက် Port Binding လုပ်ပေးတဲ့အပိုင်း
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
    payload = {
        "inputs": f"<s>[INST] {text} [/INST]",
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        result = response.json()
        
        if isinstance(result, list):
            return result[0].get('generated_text', '').strip()
        elif isinstance(result, dict) and "error" in result:
            if "loading" in result.get("error", "").lower():
                return "Model is loading. Please try again in 30 seconds."
            return f"AI Error: {result.get('error')}"
        return "I couldn't process that. Please try again."
    except Exception as e:
        return f"Connection Error: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # စာပို့လိုက်ရင် Bot အလုပ်လုပ်နေမှန်းသိအောင် status ပြမယ်
    status_msg = await update.message.reply_text("Thinking... ⏳")
    
    ai_response = query_ai(user_text)
    
    # ရလာတဲ့ အဖြေကို status စာသားနေရာမှာ အစားထိုးမယ်
    await status_msg.edit_text(ai_response)

if __name__ == '__main__':
    # Start health check server
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Start Telegram Bot
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting on Render...")
    app.run_polling()
