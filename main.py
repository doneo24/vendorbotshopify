import os
import openai
import telebot
from flask import Flask, request

# === API-Zugänge ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(BOT_TOKEN)

# === Flask-App für Webhook ===
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=["GET"])
def home():
    return "Doneo24 VendorBot läuft!", 200

# === Start-Nachricht ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "✅ Vendor-Bot ist online. Sende mir einen englischen Produkttitel + Beschreibung.")

# === Verarbeitung der Produkttexte ===
@bot.message_handler(func=lambda m: True)
def handle_product(message):
    prompt = f"""
Du bist ein Shopify-Texter für einen deutschen Onlineshop.
Erstelle aus folgendem Produkttext:

{message.text}

Folgendes auf Deutsch:
1. Produkttitel
2. Kurze Vorschau-Beschreibung
3. Produktbeschreibung (HTML)
4. Bulletpoints (5)
5. Meta Title & Meta Description

Antworte strukturiert mit:
### Title:
### Preview:
### Body:
### Bullets:
### Meta:
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        bot.send_message(message.chat.id, result[:4000])
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Fehler: {str(e)}")
        print(f"[FEHLER] {str(e)}")

# === Start der App ===
if __name__ == "__main__":
    # Setze Webhook für Telegram
    bot.remove_webhook()
    bot.set_webhook(url=f"https://doneo24-vendorbotshopify.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
