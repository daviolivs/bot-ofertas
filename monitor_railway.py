import os
import time
import hashlib
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ============================
# 🔍 DEBUG – Variáveis do Railway
# ============================
print("🔍 [DEBUG] Lendo variáveis de ambiente do Railway...")
print("API_ID =", os.getenv("API_ID"))
print("API_HASH =", os.getenv("API_HASH"))
print("STRING_SESSION =", "OK" if os.getenv("STRING_SESSION") else "NÃO DEFINIDA!")
print("CHAT_ID =", os.getenv("CHAT_ID"))
print("GRUPOS =", os.getenv("GRUPOS"))
print("KEYWORDS =", os.getenv("KEYWORDS"))

# ============================
# 🔧 CONFIGS
# ============================
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
string_session = os.getenv("STRING_SESSION")

chat_id = int(os.getenv("CHAT_ID"))

# Grupos monitorados
grupos_env = os.getenv("GRUPOS") or ""
grupos_monitorados = [int(g.strip()) for g in grupos_env.split(",") if g.strip()]

# Palavras-chave
palavras_chave = [
    p.strip().lower()
    for p in (os.getenv("KEYWORDS") or "").split(",")
    if p.strip()
]

# Anti-repetição
mensagens_enviadas = deque(maxlen=100)
ultimo_alerta = {}
tempo_cooldown = 300  # 5 minutos

# ============================
# 🔐 Inicialização do cliente (userbot)
# ============================
client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash
)

# ============================
# 📣 Mensagem ao iniciar
# ============================
async def notificar_inicio():
    try:
        await client.send_message(
            chat_id,
            "✅ Bot de ofertas iniciado e monitorando grupos."
        )
    except Exception as e:
        print(f"⚠️ Erro ao notificar início: {e}")

# ============================
# 📡 Handler principal
# ============================
@client.on(events.NewMessage(chats=tuple(grupos_monitorados)))
async def handler(event):

    texto = event.raw_text or ""
    mensagem_lower = texto.lower()

    for palavra in palavras_chave:
        if palavra.lower() in mensagem_lower:

            agora = time.time()

            # Cooldown
            if palavra in ultimo_alerta:
                if agora - ultimo_alerta[palavra] < tempo_cooldown:
                    return

            # Anti repetição
            hash_mensagem = hashlib.sha256(texto.encode()).hexdigest()
            if hash_mensagem in mensagens_enviadas:
                return

            mensagens_enviadas.append(hash_mensagem)
            ultimo_alerta[palavra] = agora

            # ======================
            # ⚠️ Correção do crash: event.chat pode ser None
            # ======================
            try:
                chat = await event.get_chat()
                nome_grupo = getattr(chat, "title", "grupo desconhecido")
            except:
                nome_grupo = "grupo desconhecido"

            alerta = (
                f"🔥 Palavra-chave '{palavra}' encontrada no grupo **{nome_grupo}**:\n\n"
                f"{texto[:300]}"
            )

            try:
                await client.send_message(chat_id, alerta)
                print(f"📤 Alerta enviado ({palavra}) – {nome_grupo}")
            except Exception as e:
                print(f"❌ Erro ao enviar alerta: {e}")

            break

# ============================
# ▶️ Execução
# ============================
print("✅ Bot de ofertas iniciado (userbot + StringSession)...")

with client:
    client.loop.run_until_complete(notificar_inicio())
    client.run_until_disconnected()
