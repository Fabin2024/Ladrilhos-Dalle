from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import uvicorn
import logging
import asyncio
import requests
import os
import sys

# === Setup Django Environment ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
import django
django.setup()

from asgiref.sync import sync_to_async
from cadastro.models import Lead, Mensagem, etapas, Workspace
# =================================

from dotenv import load_dotenv

# Importando o agente que foi configurado no Agente.py


# Carregar variáveis de ambiente (URL do Evolution API e API KEY)
load_dotenv()

# Configuração de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Webhook CRM")

EVOLUTION_SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("AUTHENTICATION_API_KEY", "B6D711FCDE4D4FD5936544120E7139D5")

async def enviar_mensagem_whatsapp(instancia: str, numero: str, texto: str):
    """
    Envia a resposta gerada pelo agente de volta para o cliente via WhatsApp (Evolution API).
    """
    url = f"{EVOLUTION_SERVER_URL}/message/sendText/{instancia}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    payload = {
        "number": numero,
        "text": texto
    }
    try:
        # Usa asyncio.to_thread para não bloquear o event loop com o requests síncrono
        response = await asyncio.to_thread(requests.post, url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Mensagem do agente enviada com sucesso para {numero} (Instância: {instancia})")
    except Exception as e:
        logger.error(f"Erro ao enviar resposta para o WhatsApp ({numero}): {e}")

@sync_to_async
def get_or_create_lead(remote_jid, instancia, push_name=None):
    workspace_id = None
    if instancia and instancia.startswith("ws_"):
        parts = instancia.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            workspace_id = int(parts[1])
            
    workspace_obj = None
    if workspace_id:
        workspace_obj = Workspace.objects.filter(id=workspace_id).first()
    
    primeira_etapa = etapas.objects.first()
    novo_contato_etapa = etapas.objects.filter(nome__icontains="Novo Contato").first() or primeira_etapa

    numero_limpo = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

    lead = Lead.objects.filter(numero=numero_limpo).first()
    if not lead:
        # Tenta achar pela versão antiga (com @s.whatsapp.net)
        lead = Lead.objects.filter(numero=remote_jid).first()

    if not lead:
        lead = Lead.objects.create(
            numero=numero_limpo,
            nome=push_name if push_name else "Novo Contato",
            workspace=workspace_obj,
            etapa=novo_contato_etapa
        )
    else:
        changed = False
        if push_name and (lead.nome == "Novo Contato" or not lead.nome):
            lead.nome = push_name
            changed = True
        
        if lead.numero == remote_jid and "@" in lead.numero:
            lead.numero = numero_limpo
            changed = True
            
        if changed:
            lead.save(update_fields=["nome", "numero"])

    return lead

@sync_to_async
def save_message(lead, text, from_me):
    return Mensagem.objects.create(lead=lead, texto=text, from_me=from_me)

@sync_to_async
def get_workspace_for_instancia(instancia):
    if instancia and instancia.startswith("ws_"):
        parts = instancia.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            workspace_id = int(parts[1])
            return Workspace.objects.filter(id=workspace_id).first()
    return None

async def processar_mensagem_agente(payload: dict):
    """
    Processa a mensagem em background:
    1. Extrai o texto da mensagem do Evolution API
    2. Envia para o agente (Agno) via .arun() de forma assíncrona
    3. Devolve a resposta para o WhatsApp
    """
    from django.db import close_old_connections
    close_old_connections()
    try:
        # Identifica o evento
        event = payload.get("event")
        if event != "messages.upsert":
            return # Só queremos processar novas mensagens
            
        data = payload.get("data", {})
        message_info = data.get("message", {})
        key = data.get("key", {})
        push_name = data.get("pushName")
        
        # Ignora mensagens enviadas por nós mesmos (para não gerar loop)
        if key.get("fromMe"):
            return
            
        # Na v2.3.7, o número real vem em remoteJidAlt quando o JID principal é oculto
        remote_jid = key.get("remoteJidAlt") or key.get("remoteJid", "")
        
        # Ignora mensagens de grupos (@g.us) ou se por acaso ainda vier como @lid absoluto
        if not remote_jid or "@g.us" in remote_jid or "@lid" in remote_jid:
            return
            
        # Verifica se é uma mensagem de áudio
        message_type = payload.get("messageType") or data.get("messageType")
        arquivo_audio = None
        instancia = payload.get("instance")

        # Extrai o texto da mensagem (Evolution API possui múltiplos formatos dependendo do tipo da msg)
        texto_mensagem = message_info.get("conversation") or \
                         message_info.get("extendedTextMessage", {}).get("text")
        
        if message_type == "audioMessage" or "audioMessage" in message_info:
            # Baixa o áudio via Evolution API
            url_base64 = f"{EVOLUTION_SERVER_URL}/chat/getBase64FromMediaMessage/{instancia}"
            headers_api = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
            }
            try:
                # O Evolution API pede o objeto "message" completo (com key) para baixar a mídia
                payload_media = {"message": data}
                # Para chamadas assíncronas
                resp_media = await asyncio.to_thread(requests.post, url_base64, json=payload_media, headers=headers_api)
                resp_media.raise_for_status()
                
                base64_data = resp_media.json().get("base64")
                if base64_data:
                    import base64
                    import tempfile
                    
                    audio_bytes = base64.b64decode(base64_data)
                    # Cria um arquivo temporário
                    fd, arquivo_audio = tempfile.mkstemp(suffix=".ogg")
                    with os.fdopen(fd, 'wb') as f:
                        f.write(audio_bytes)
                    texto_mensagem = f"O usuário enviou uma mensagem de áudio. O arquivo está salvo em: {arquivo_audio}"
            except Exception as e:
                logger.error(f"Erro ao baixar áudio: {e}")
                return

        if not texto_mensagem:
            return # Ignora se não houver texto (ex: imagem sem legenda) e não for áudio
        
        logger.info(f"Mensagem de {remote_jid}: {texto_mensagem}")
        
        # === Salva Lead e Mensagem de Entrada no Django ===
        lead = None
        try:
            lead = await get_or_create_lead(remote_jid, instancia, push_name=push_name)
            await save_message(lead, texto_mensagem, from_me=False)
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem no DB: {e}")
        # ==================================================
        
        # Verifica se o agente está ativo no workspace
        workspace = await get_workspace_for_instancia(instancia)
        if not workspace or not workspace.agente_ativo:
            logger.info(f"Agente desativado ou workspace não encontrado para a instância {instancia}. Ignorando IA.")
            return
        
        logger.info("Pensando (Agno Agent)...")
        from cadastro.Agente import criar_agente
        agente = criar_agente(nome=workspace.agente_nome, instrucoes=workspace.agente_instrucoes, workspace_id=workspace.id, instancia=instancia, remote_jid=remote_jid)
        
        # ==========================================================
        # CHAMADA ASSÍNCRONA DO AGENTE
        # Utilizamos o arun() conforme documentação do Agno 
        # para que a chamada não trave as outras threads
        # ==========================================================
        resposta_agente = await agente.arun(texto_mensagem)
        
        # Exclui o arquivo temporário de áudio se foi criado
        if arquivo_audio and os.path.exists(arquivo_audio):
            try:
                os.remove(arquivo_audio)
            except Exception as e:
                logger.error(f"Erro ao excluir áudio temporário: {e}")
        
        # O retorno normalmente possui a propriedade 'content'
        texto_resposta = resposta_agente.content if hasattr(resposta_agente, 'content') else str(resposta_agente)
        
        logger.info(f"Resposta gerada: {texto_resposta}")
        
        # === Salva Resposta de Saída no Django ===
        if lead:
            try:
                await save_message(lead, texto_resposta, from_me=True)
            except Exception as e:
                logger.error(f"Erro ao salvar resposta no DB: {e}")
        # ==================================================
        
        # Envia a resposta de volta ao WhatsApp
        await enviar_mensagem_whatsapp(instancia, remote_jid, texto_resposta)
        
    except Exception as e:
        logger.error(f"Erro no processamento background do Agente: {e}")

@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint assíncrono para receber o webhook da Evolution API.
    Utiliza BackgroundTasks do FastAPI para encaminhar o processamento
    da mensagem para o Agente sem segurar a requisição HTTP original.
    """
    try:
        payload = await request.json()
        
        # Repassa o trabalho pesado (processar o LLM e responder) para background
        background_tasks.add_task(processar_mensagem_agente, payload)
        
        # Retorna status HTTP 200 IMEDIATAMENTE para a Evolution API não ficar aguardando
        return {"status": "success", "message": "Mensagem na fila de processamento do agente."}
        
    except Exception as e:
        logger.error(f"Erro ao ler payload do webhook: {e}")
        raise HTTPException(status_code=400, detail="Payload inválido")

if __name__ == "__main__":
    uvicorn.run("webhook:app", host="0.0.0.0", port=8000, reload=True)
