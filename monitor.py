import os
from telethon import TelegramClient, events
import requests

# --- CREDENCIAIS SEGURAS (pegas do Railway) ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")

# --- LISTA DE GRUPOS (do Railway, separados por vírgula) ---
# Exemplo no Railway: -1001904527261,-1001892859078,-1001622757657
grupos_monitorados = [int(g.strip()) for g in os.getenv("GRUPOS").split(",")]

# --- PALAVRAS-CHAVE (do Railway ou definidas no código) ---
palavras_chave = os.getenv("KEYWORDS", "ar-condicionado,bug,oferta,promoção").split(",")

# --- CLIENTE TELETHON ---
client = TelegramClient('monitor', api_id, api_hash)

@client.on(events.NewMessage(chats=tuple(grupos_monitorados)))
async def handler(event):
    mensagem = event.raw_text.lower()
    if any(p.lower() in mensagem for p in palavras_chave):
        alerta = f"🔥 Oferta encontrada no grupo {event.chat.title}:\n\n{event.raw_text[:300]}"
        requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                     params={"chat_id": chat_id, "text": alerta})

print("✅ Bot de ofertas iniciado (Railway)...")
client.start()
client.run_until_disconnected()

