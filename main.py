# main.py – Kombi aus VendorBot (Text) + ProduktjägerBot

import os
import openai
import telebot
from flask import Flask, request
import random

# === API-Zugänge ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === Produktjäger-Daten (Platzhalter) ===
produkte = {
    "beauty": [
        {
            "name": "Elektrischer Porensauger",
            "beschreibung": "Mit 5 Aufsätzen & EU-Lager – Tiefenreinigung für dein Gesicht.",
            "ek": "6,79 €", "vk": "29,95 €", "marge": "+23,16 €",
            "lager": "✅ EU (Polen)", "trend": "Hoch",
            "link": "https://example.com/porensauger"
        }
    ],
    "haushalt": [
        {
            "name": "Mini Heat Sealer",
            "beschreibung": "Wiederverwendbarer Beutelversiegler für Snacks & Küche.",
            "ek": "4,22 €", "vk": "24,95 €", "marge": "+20,73 €",
            "lager": "✅ EU (Niederlande)", "trend": "Mittel",
            "link": "https://example.com/heater"
        }
    ],
    "viral": [
        {
            "name": "LED Galaxy Projektor",
            "beschreibung": "360° Sternenhimmel mit Bluetooth-Sound & Fernbedienung.",
            "ek": "11,10 €", "vk": "39,95 €", "marge": "+28,85 €",
            "lager": "✅ EU (Deutschland)", "trend": "Hoch",
            "link": "https://example.com/galaxy"
        }
    ]
}

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=["GET"])
def home():
    return "Doneo24 VendorBot & Produktjäger aktiv!", 200

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "✅ Vendor-Bot ist online.\n\nSchick mir einen englischen Produkttitel + Beschreibung für deutschen Verkaufstext.\nOder starte die Produktsuche mit: /jagd beauty | haushalt | viral | all")

@bot.message_handler(commands=["jagd"])
def jagd(message):
    args = message.text.split(" ")
    if len(args) < 2:
        bot.send_message(message.chat.id, "Bitte gib eine Kategorie an: /jagd beauty | haushalt | viral | all")
        return

    kategorie = args[1].lower()
    if kategorie == "all":
        alle = sum(produkte.values(), [])
        produkt = random.choice(alle)
    elif kategorie in produkte:
        produkt = random.choice(produkte[kategorie])
    else:
        bot.send_message(message.chat.id, "Ungültige Kategorie. Wähle: beauty | haushalt | viral | all")
        return

    text = f"**Produktvorschlag: {produkt['name']}**\n"
    text += f"{produkt['beschreibung']}\n"
    text += f"EK: {produkt['ek']}   VK: {produkt['vk']}   Marge: {produkt['marge']}\n"
    text += f"Lager: {produkt['lager']}\n"
    text += f"TikTok-Trend: {produkt['trend']}\n"
    text += f"Link: {produkt['link']}"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

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

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://doneo24-vendorbotshopify.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
