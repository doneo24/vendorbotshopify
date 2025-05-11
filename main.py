
import os
import telebot
import openai

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Vendor-Bot ist online. Sende mir einen englischen Produkttitel + Beschreibung.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
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

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content
    bot.send_message(message.chat.id, result[:4000])  # max. Telegram limit

bot.infinity_polling()
