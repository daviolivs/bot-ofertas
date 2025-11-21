import os
import time
import hashlib
import traceback
from collections import deque

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, RPCError

# ============================
# DEBUG – Variáveis do Railway
# ============================
print("🔍 [DEBUG] Lendo variáveis de ambiente do Railway...")
print("API_ID =", os.getenv("API_ID"))
print("API_HASH =", os.getenv("API_HASH"))
print("STRING_SESSION =", "OK" if os.getenv("STRING_SESSION") else "NÃO DEFINIDA!")
print("CHAT_ID =", os.getenv("CHAT_ID"))
print("GRUPOS =", os.getenv("GRUPOS"))
print("KEYWORDS =", os.getenv("KEYWORDS"))

# ============================
# CONFIGS
# ============================
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
string_session = os.getenv("STRING_SESSION")

if not string_session:
    raise RuntimeError("STRING_SESSION não definida nas variáveis de ambiente")

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

# ============================
# Proteções contra flood
# ============================

# Anti repetição por conteúdo (hash da mensagem)
mensagens_enviadas = deque(maxlen=200)

# Cooldown por palavra (segundos)
ultimo_alerta = {}
tempo_cooldown_palavra = int(os.getenv("COOLDOWN_PALAVRA") or "300")  # padrão: 5 minutos

# Cooldown global entre alertas (segundos)
ultimo_envio_global = 0
cooldown_global = int(os.getenv("COOLDOWN_GLOBAL") or "3")  # padrão: 3 segundos

# Limite de alertas por minuto
envios_minuto = deque()  # guarda timestamps dos envios
janela_segundos = 60
limite_por_minuto = int(os.getenv("LIMITE_POR_MINUTO") or "40")  # padrão: 40 alertas / minuto


async def notificar_inicio(client: TelegramClient) -> None:
    try:
        await client.send_message(
            chat_id,
            "✅ Bot de ofertas iniciado e monitorando grupos."
        )
    except Exception as e:
        print(f"⚠️ Erro ao notificar início: {e}")
        traceback.print_exc()


def criar_cliente() -> TelegramClient:
    """
    Cria o client com StringSession e registra o handler de mensagens.
    """
    client = TelegramClient(
        StringSession(string_session),
        api_id,
        api_hash
    )

    @client.on(events.NewMessage(chats=tuple(grupos_monitorados)))
    async def handler(event):
        global ultimo_envio_global

        texto = event.raw_text or ""
        mensagem_lower = texto.lower()
        agora = time.time()

        # Limpa janela de 1 minuto
        while envios_minuto and (agora - envios_minuto[0] > janela_segundos):
            envios_minuto.popleft()

        # Limite por minuto
        if len(envios_minuto) >= limite_por_minuto:
            print("⏱️ Limite de alertas por minuto atingido, ignorando mensagem.")
            return

        for palavra in palavras_chave:
            pl = palavra.lower()

            if pl in mensagem_lower:
                # Cooldown por palavra
                if pl in ultimo_alerta:
                    if agora - ultimo_alerta[pl] < tempo_cooldown_palavra:
                        return

                # Cooldown global entre alertas
                if agora - ultimo_envio_global < cooldown_global:
                    return

                # Anti repetição por hash do texto
                hash_mensagem = hashlib.sha256(texto.encode()).hexdigest()
                if hash_mensagem in mensagens_enviadas:
                    return

                mensagens_enviadas.append(hash_mensagem)
                ultimo_alerta[pl] = agora
                ultimo_envio_global = agora
                envios_minuto.append(agora)

                # Nome do grupo com fallback
                try:
                    chat = await event.get_chat()
                    nome_grupo = getattr(chat, "title", "grupo desconhecido")
                except Exception:
                    nome_grupo = "grupo desconhecido"

                alerta = (
                    f"🔥 Palavra-chave '{palavra}' encontrada no grupo {nome_grupo}:\n\n"
                    f"{texto[:300]}"
                )

                try:
                    await client.send_message(chat_id, alerta)
                    print(f"📤 Alerta enviado ({palavra}) – {nome_grupo}")
                except FloodWaitError as fw:
                    print(f"⏳ FloodWait: aguardando {fw.seconds} segundos.")
                    time.sleep(fw.seconds)
                except RPCError as e:
                    print(f"❌ Erro RPC ao enviar alerta: {e}")
                    traceback.print_exc()
                except Exception as e:
                    print(f"❌ Erro inesperado ao enviar alerta: {e}")
                    traceback.print_exc()

                break  # evita disparar mais de uma palavra por mensagem

    return client


def main():
    """
    Loop principal: cria o client, conecta e, se cair, tenta reconectar.
    """
    while True:
        try:
            client = criar_cliente()
            print("✅ Bot de ofertas iniciado (userbot + StringSession)...")

            with client:
                client.loop.run_until_complete(notificar_inicio(client))
                client.run_until_disconnected()

        except Exception as e:
            print("❌ Erro principal no loop do bot:")
            print(repr(e))
            traceback.print_exc()
            print("⏳ Aguardando 15 segundos para tentar reconectar...")
            time.sleep(15)


if __name__ == "__main__":
    main()
