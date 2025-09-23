import os
import time
import hashlib
from collections import deque
from telethon import TelegramClient, events
import requests

# --- DEBUG: Lendo variáveis do Railway ---
print("🔍 [DEBUG] Lendo variáveis de ambiente do Railway...")
print("API_ID =", os.getenv("API_ID"))
print("API_HASH =", os.getenv("API_HASH"))
print("BOT_TOKEN =", os.getenv("BOT_TOKEN"))
print("CHAT_ID =", os.getenv("CHAT_ID"))
print("GRUPOS =", os.getenv("GRUPOS"))
print("KEYWORDS =", os.getenv("KEYWORDS"))

# --- Variáveis com fallback (funciona local também) ---
api_id = int(os.getenv("API_ID") or "27867189")
api_hash = os.getenv("API_HASH") or "aae51a8a046989834c4c50e1188e8dc6"
bot_token = os.getenv("BOT_TOKEN") or "8390189951:AAEyQrBIebvfbIao6xyj8Xr581ydsLKXVYs"
chat_id = os.getenv("CHAT_ID") or "810381547"

# --- Grupos monitorados ---
grupos_env = os.getenv("GRUPOS") or "-1001904527261"
grupos_monitorados = [int(g.strip()) for g in grupos_env.split(",") if g.strip()]

# --- Palavras-chave monitoradas ---
palavras_chave = [p.strip().lower() for p in (os.getenv("KEYWORDS") or "promoção,oferta,bug").split(",")]

# --- Proteções ---
mensagens_enviadas = deque(maxlen=50)  # armazena últimos 50 hashes
ultimo_alerta = {}  # palavra-chave -> timestamp
tempo_cooldown = 300  # segundos de espera por palavra (5 min)

# --- Cliente Telegram ---
client = TelegramClient('monitor', api_id, api_hash)

@client.on(events.NewMessage(chats=tuple(grupos_monitorados)))
async def handler(event):
    texto = event.raw_text
    mensagem = texto.lower()

    # Verifica se contém alguma palavra-chave
    for palavra in palavras_chave:
        if palavra in mensagem:
            agora = time.time()

            # ⚠️ Cooldown por palavra
            if palavra in ultimo_alerta:
                if agora - ultimo_alerta[palavra] < tempo_cooldown:
                    return  # Está dentro do cooldown → ignora

            # ⚠️ Hash anti-repetição
            hash_mensagem = hashlib.sha256(texto.encode()).hexdigest()
            if hash_mensagem in mensagens_enviadas:
                return  # Já enviou mensagem igual → ignora

            # Atualiza controles
            ultimo_alerta[palavra] = agora
            mensagens_enviadas.append(hash_mensagem)

            # Envia alerta
            alerta = f"🔥 Palavra-chave '{palavra}' encontrada no grupo {event.chat.title}:\n\n{texto[:300]}"
            requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                         params={"chat_id": chat_id, "text": alerta})
            break  # já encontrou e enviou, não precisa checar outras palavras

print("✅ Bot de ofertas iniciado (com hash e cooldown)...")
client.start()
client.run_until_disconnected()
