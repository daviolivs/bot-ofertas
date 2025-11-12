import os
import time
import hashlib
from collections import deque
from telethon import TelegramClient, events

# --- DEBUG: Lendo variáveis do Railway ---
print("🔍 [DEBUG] Lendo variáveis de ambiente do Railway...")
print("API_ID =", os.getenv("API_ID"))
print("API_HASH =", os.getenv("API_HASH"))
print("CHAT_ID =", os.getenv("CHAT_ID"))
print("GRUPOS =", os.getenv("GRUPOS"))
print("KEYWORDS =", os.getenv("KEYWORDS"))

# --- Variáveis com fallback (funciona local também) ---
api_id = int(os.getenv("API_ID") or "27867189")
api_hash = os.getenv("API_HASH") or "aae51a8a046989834c4c50e1188e8dc6"
chat_id = int(os.getenv("CHAT_ID") or "810381547")  # precisa ser int

# --- Grupos monitorados ---
grupos_env = os.getenv("GRUPOS") or "-1001904527261"
grupos_monitorados = [int(g.strip()) for g in grupos_env.split(",") if g.strip()]

# --- Palavras-chave monitoradas ---
palavras_chave = [p.strip().lower() for p in (os.getenv("KEYWORDS") or "promoção,oferta,bug").split(",")]

# --- Proteções ---
mensagens_enviadas = deque(maxlen=50)  # últimos 50 hashes
ultimo_alerta = {}  # palavra-chave -> timestamp
tempo_cooldown = 300  # segundos de espera por palavra (5 min)

# --- Cliente Telegram com conta pessoal ---
client = TelegramClient('monitor', api_id, api_hash)

@client.on(events.NewMessage(chats=tuple(grupos_monitorados)))
async def handler(event):
    texto = event.raw_text
    mensagem = texto.lower()

    for palavra in palavras_chave:
        if palavra in mensagem:
            agora = time.time()

            # Cooldown por palavra
            if palavra in ultimo_alerta:
                if agora - ultimo_alerta[palavra] < tempo_cooldown:
                    return

            # Hash anti-repetição
            hash_mensagem = hashlib.sha256(texto.encode()).hexdigest()
            if hash_mensagem in mensagens_enviadas:
                return

            # Atualiza controles
            ultimo_alerta[palavra] = agora
            mensagens_enviadas.append(hash_mensagem)

            # Envia alerta pela conta pessoal
            alerta = f"🔥 Palavra-chave '{palavra}' encontrada no grupo {event.chat.title}:\n\n{texto[:300]}"
            await client.send_message(chat_id, alerta)
            break

print("✅ Bot de ofertas iniciado (usando client.send_message)...")
client.start()
client.run_until_disconnected()
