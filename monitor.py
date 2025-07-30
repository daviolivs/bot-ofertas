import os
from telethon import TelegramClient, events
import requests

# 🔍 DEBUG: Mostrar variáveis lidas pelo Railway
print("🔍 [DEBUG] Lendo variáveis de ambiente do Railway...")
print("API_ID =", os.getenv("API_ID"))
print("API_HASH =", os.getenv("API_HASH"))
print("BOT_TOKEN =", os.getenv("BOT_TOKEN"))
print("CHAT_ID =", os.getenv("CHAT_ID"))
print("GRUPOS =", os.getenv("GRUPOS"))
print("KEYWORDS =", os.getenv("KEYWORDS"))

# ✅ Variáveis com fallback para evitar crash
api_id = int(os.getenv("API_ID") or "27867189")
api_hash = os.getenv("API_HASH") or "aae51a8a046989834c4c50e1188e8dc6"
bot_token = os.getenv("BOT_TOKEN") or "8390189951:AAEyQrBIebvfbIao6xyj8Xr581ydsLKXVYs"
chat_id = os.getenv("CHAT_ID") or "810381547"

# ✅ Lista de grupos (usa variável GRUPOS ou um padrão)
grupos_env = os.getenv("GRUPOS") or "-1001904527261"
grupos_monitorados = [int(g.strip()) for g in grupos_env.split(",") if g.strip()]

# ✅ Palavras-chave (usa variável KEYWORDS ou padrão)
palavras_chave = [p.strip() for p in (os.getenv("KEYWORDS") or "promoção,oferta,bug").split(",")]

# --- CLIENTE TELETHON ---
client = TelegramClient('monitor', api_id, api_hash)

@client.on(events.NewMessage(chats=tuple(grupos_monitorados)))
async def handler(event):
    mensagem = event.raw_text.lower()
    if any(p.lower() in mensagem for p in palavras_chave):
        alerta = f"🔥 Oferta encontrada no grupo {event.chat.title}:\n\n{event.raw_text[:300]}"
        requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                     params={"chat_id": chat_id, "text": alerta})

print("✅ Bot de ofertas iniciado (com fallback)...")
client.start()
client.run_until_disconnected()