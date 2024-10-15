import telegram
from telegram.ext import Application
import asyncio

# Token API del tuo bot
bot_token = '7033631161:AAHEHy8r0bdNXAvaYNW-k-vMFjq68XG0A5Q'

async def send_telegram_message(chat_id, message):
    """
    Invia un messaggio a un chat_id specifico su Telegram.

    :param chat_id: ID della chat su cui inviare il messaggio
    :param message: Testo del messaggio da inviare
    """
    # Inizializza l'applicazione Telegram
    application = Application.builder().token(bot_token).build()

    # Invia il messaggio asincrono
    await application.bot.send_message(chat_id=chat_id, text=message)

def invia_risultati_via_telegram(chat_id, risultati_stringa):
    """
    Funzione che invia una stringa contenente i risultati via Telegram.

    :param chat_id: ID della chat Telegram
    :param risultati_stringa: Stringa con i risultati da inviare
    """
    asyncio.run(send_telegram_message(chat_id, risultati_stringa))

async def get_chat_id():
    # Inizializza l'applicazione
    application = Application.builder().token(bot_token).build()

    # Ottieni gli aggiornamenti asincroni
    updates = await application.bot.get_updates(timeout=10)

    # Stampa il chat ID di ogni messaggio ricevuto
    for update in updates:
        if update.message is not None:
            print(update.message.chat.id)

# # Per prendere i chatID
# asyncio.run(get_chat_id())

