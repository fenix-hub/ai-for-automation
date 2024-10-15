import telegram
from telegram.ext import Application
import asyncio

# Token API del bot
bot_token = '7033631161:AAHEHy8r0bdNXAvaYNW-k-vMFjq68XG0A5Q'
# Bot Link: https://t.me/AIxAut_training_bot

async def send_telegram_message(chat_id, message):
    """
    Invia un messaggio a un chat_id specifico su Telegram.

    :param chat_id: ID della chat su cui inviare il messaggio
    :param message: Testo del messaggio da inviare
    """
    application = Application.builder().token(bot_token).build()

    # Invia messaggio asincrono
    await application.bot.send_message(chat_id=chat_id, text=message)

async def send_telegram_file(chat_id, file_path):
    # Inizializza l'applicazione Telegram
    application = Application.builder().token(bot_token).build()

    # Invia il file CSV
    await application.bot.send_document(chat_id=chat_id, document=open(file_path, 'rb'))

def invia_risultati_via_telegram(chat_id, risultati_stringa):
    asyncio.run(send_telegram_message(chat_id, risultati_stringa))

def invia_file_csv_via_telegram(chat_id, file_path):
    asyncio.run(send_telegram_file(chat_id, file_path))

async def get_chat_id():

    application = Application.builder().token(bot_token).build()

    # Aggiornamenti asincroni
    updates = await application.bot.get_updates(timeout=10)

    # Stampa il chat ID di ogni messaggio ricevuto
    for update in updates:
        if update.message is not None:
            print(update.message.chat.id)

# # Per prendere i chatID
# asyncio.run(get_chat_id())
