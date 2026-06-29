from agno.models.openai import OpenAIChat
from agno.agent import Agent
from agno.tools.openai import OpenAITools
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.excel_reader import ExcelReader
from dotenv import load_dotenv
import os

load_dotenv()

def obter_knowledge(workspace_id):
    vector_store = ChromaDb(
        collection=f"workspace_{workspace_id}_conhecimento",
        path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db"),
        embedder=OpenAIEmbedder(id="text-embedding-3-small", api_key=os.getenv("OPENAI_API_KEY")),
        persistent_client=True
    )
    return Knowledge(vector_db=vector_store)

def adicionar_arquivo_ao_rag(caminho_arquivo, workspace_id):
    rag = obter_knowledge(workspace_id)
    
    ext = caminho_arquivo.lower().split('.')[-1]
    if ext == 'pdf':
        reader = PDFReader()
    elif ext in ['xls', 'xlsx']:
        reader = ExcelReader()
    else:
        # Fallback (agno might have issues with unknown, but let's assume it ignores or throws)
        reader = PDFReader() # just a placeholder

    # Add content to the knowledge base (this processes and inserts it automatically)
    rag.add_content(path=caminho_arquivo, reader=reader, skip_if_exists=True)

import requests

from agno.db.postgres import PostgresDb

def criar_agente(nome, instrucoes, workspace_id=None, instancia=None, remote_jid=None):
    # Prepara as instruções garantindo que o Agente saiba o próprio nome e saiba lidar com áudios
    instrucoes_finais = f"O seu nome é {nome}. Ao se apresentar, use este nome e nunca use placeholders como '[Seu Nome]'.\n"
    instrucoes_finais += "Se você receber uma mensagem informando que 'O arquivo está salvo em: /caminho/do/audio', use sua ferramenta de transcrição para ler o que o usuário disse e responda como se fosse uma mensagem de texto normal.\n\n"
    if isinstance(instrucoes, list):
        instrucoes_finais += "\n".join(instrucoes)
    else:
        instrucoes_finais += str(instrucoes)

    tools_list = [OpenAITools(transcription_model="whisper-1")]
    
    # Configuração de Memória no PostgreSQL
    db_url = os.getenv("DATABASE_CONNECTION_URI", "postgresql://postgres:postgres123@postgres:5432/evolution")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "?schema=" in db_url:
        db_url = db_url.split("?schema=")[0]
    
    db = PostgresDb(
        db_url=db_url,
        memory_table="agent_memory_table"
    )
    
    session_id = f"ws_{workspace_id}_{remote_jid}" if workspace_id and remote_jid else "default_session"

    if instancia and remote_jid:
        def enviar_contato_whatsapp(nome_contato: str, numero_contato: str) -> str:
            """
            Usa esta ferramenta exclusivamente para enviar um cartão de contato (vCard) do WhatsApp de uma pessoa/atendente para o usuário atual.
            Use esta ferramenta SEMPRE que o usuário pedir para falar com um atendente ou precisar do contato de alguém.
            
            Args:
                nome_contato: O nome da pessoa ou atendente que você está indicando.
                numero_contato: O número de WhatsApp da pessoa (ex: 5511999999999).
            """
            EVOLUTION_SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8080").rstrip("/")
            EVOLUTION_API_KEY = os.getenv("AUTHENTICATION_API_KEY", "B6D711FCDE4D4FD5936544120E7139D5")
            
            url = f"{EVOLUTION_SERVER_URL}/message/sendContact/{instancia}"
            headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
            }
            
            # Limpa o numero de caracteres especiais para criar o WUID (identificador do whatsapp)
            wuid = "".join(filter(str.isdigit, numero_contato))
            if wuid.startswith("0"): wuid = "55" + wuid[1:]
            elif not wuid.startswith("55") and len(wuid) <= 11: wuid = "55" + wuid
                
            payload = {
                "number": remote_jid,
                "contactMessage": [
                    {
                        "fullName": nome_contato,
                        "wuid": wuid,
                        "phoneNumber": numero_contato
                    }
                ]
            }
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=15)
                resp.raise_for_status()
                return f"Cartão de contato de {nome_contato} enviado com sucesso para o WhatsApp do usuário! Diga a ele que acabou de enviar o contato."
            except Exception as e:
                return f"Falha ao enviar contato: {str(e)}"
                
        tools_list.append(enviar_contato_whatsapp)

    kwargs = {
        "name": nome,
        "model": OpenAIChat(id="gpt-4o-mini"),
        "tools": tools_list,
        "instructions": instrucoes_finais,
        "db": db,
        "session_id": session_id,
        "update_memory_on_run": True,
        "add_history_to_context": True,
        "num_history_runs": 3,
        "enable_user_memories": True,
        "add_memories_to_context": True,
        "enable_agentic_memory": True,
    }
    
    if workspace_id:
        rag = obter_knowledge(workspace_id)
        kwargs["knowledge"] = rag
        kwargs["search_knowledge"] = True
        
    return Agent(**kwargs)
