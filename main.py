# main.py – VendorBot mit Jagd, Button & 60s-Timer für Text-Generierung

import os
import openai
import telebot
from flask import Flask, request
import random
import threading
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

produkte = {
    "beauty": [
        {
            "name": "Elektrischer Porensauger",
            "beschreibung": "Mit 5 Aufsätzen & EU-Lager – Tiefenreinigung für dein Gesicht.",
            "ek": "6,79 €", "vk": "29,95 €", "marge": "+23,16 €",
            "lager": "✅ EU (Polen)", "trend": "Hoch",
            "link": "https://www.bigbuy.eu/de/elektrischer-porenreiniger-sauger.html"
        }
    ],
    "haushalt": [
        {
            "name": "Mini Heat Sealer",
            "beschreibung": "Wiederverwendbarer Beutelversiegler für Snacks & Küche.",
            "ek": "4,22 €", "vk": "24,95 €", "marge": "+20,73 €",
            "lager": "✅ EU (Niederlande)", "trend": "Mittel",
            "link": "https://www.dropshippingxl.com/de/versiegler-mini.html"
        }
    ],
    "viral": [
        {
            "name": "LED Galaxy Projektor",
            "beschreibung": "360° Sternenhimmel mit Bluetooth-Sound & Fernbedienung.",
            "ek": "11,10 €", "vk": "39,95 €", "marge": "+28,85 €",
            "lager": "✅ EU (Deutschland)", "trend": "Hoch",
            "link": "https://www.verkaufsplattform.de/led-galaxy-projektor-sternenhimmel"
        }
    ]
}

letztes_produkt = {}
letztes_produkt_timestamp = 0

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=["GET"])
def home():
    return "VendorBot & Produktjäger aktiv", 200

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "✅ Vendor-Bot ist aktiv!\n\nNutze /jagd [beauty|haushalt|viral|all]\nKlicke dann auf 'Text erstellen', um einen deutschen Shopify-Text zu generieren.")

@bot.message_handler(commands=["jagd"])
def jagd(message):
    global letztes_produkt, letztes_produkt_timestamp
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

    letztes_produkt = produkt
    letztes_produkt_timestamp = time.time()

    text = f"**Produktvorschlag: {produkt['name']}**\n"
    text += f"{produkt['beschreibung']}\n"
    text += f"EK: {produkt['ek']}   VK: {produkt['vk']}   Marge: {produkt['marge']}\n"
    text += f"Lager: {produkt['lager']}\n"
    text += f"TikTok-Trend: {produkt['trend']}\n"
    text += f"Link: {produkt['link']}"

    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("Text erstellen", callback_data="text_erstellen")
    markup.add(button)

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

    def reset_letztes():
        global letztes_produkt, letztes_produkt_timestamp
        time.sleep(60)
        letztes_produkt = {}
        letztes_produkt_timestamp = 0

    threading.Thread(target=reset_letztes).start()

@bot.callback_query_handler(func=lambda call: call.data == "text_erstellen")
def text_from_button(call):
    global letztes_produkt, letztes_produkt_timestamp
    if not letztes_produkt or (time.time() - letztes_produkt_timestamp > 60):
        bot.send_message(call.message.chat.id, "❌ Zeit abgelaufen. Bitte erneut mit /jagd starten.")
        return

    prompt = f"""
Du bist ein Shopify-Texter für einen deutschen Onlineshop.
Hier sind Name und Kurzbeschreibung eines Produkts:

Name: {letztes_produkt['name']}
Beschreibung: {letztes_produkt['beschreibung']}

Erstelle folgende Inhalte auf Deutsch:
1. Produkttitel
2. Kurze Vorschau-Beschreibung
3. Produktbeschreibung (HTML)
4. Bulletpoints (5)
5. Meta Title & Meta Description

Antwortformat:
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
        bot.send_message(call.message.chat.id, result[:4000])
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Fehler bei der Texterstellung: {str(e)}")

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

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://doneo24-vendorbotshopify.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
