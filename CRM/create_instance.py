import os
import requests
from pathlib import Path

def load_env_file():
    """
    Carrega as variáveis de ambiente do arquivo .env caso não estejam definidas.
    Busca na pasta atual, na pasta pai ou na raiz do projeto.
    """
    for p in [Path('.'), Path('..'), Path(__file__).resolve().parents[1]]:
        env_path = p / '.env'
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        key = key.strip()
                        val = val.strip().strip('\'"')
                        if key not in os.environ:
                            os.environ[key] = val
            break

# Carrega as configurações do arquivo .env
load_env_file()

# Configurações da Evolution API vindas do arquivo .env (com fallbacks seguros)
EVOLUTION_SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("AUTHENTICATION_API_KEY", "B6D711FCDE4D4FD5936544120E7139D5")

def criar_instancia(nome_instancia, token=None, habilitar_qrcode=True, integracao="WHATSAPP-BAILEYS", numero=None):
    """
    Cria uma nova instância na Evolution API.
    
    :param nome_instancia: Nome único da instância (variável/dinâmico)
    :param token: Token de segurança para a instância (se None, a API gera automaticamente)
    :param habilitar_qrcode: Se deve habilitar/retornar QR Code na criação (padrão: True)
    :param integracao: Tipo de integração (padrão: WHATSAPP-BAILEYS)
    :param numero: Número do WhatsApp associado (opcional)
    :return: Dicionário com a resposta da API ou None em caso de erro
    """
    url = f"{EVOLUTION_SERVER_URL}/instance/create"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    payload = {
        "instanceName": nome_instancia,
        "qrcode": habilitar_qrcode,
        "integration": integracao
    }
    
    if token:
        payload["token"] = token
        
    if numero:
        payload["number"] = str(numero)
        
    print(f"Enviando requisição para criar a instância: '{nome_instancia}'...")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        dados_resposta = response.json()
        print("Instância criada com sucesso!")
        return dados_resposta
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao criar instância: {http_err}")
        if response.text:
            print(f"Detalhes do erro: {response.text}")
        return None
    except Exception as err:
        print(f"Erro inesperado ao criar instância: {err}")
        return None

def conectar_instancia(nome_instancia):
    """
    Gera e retorna o código QR para conexão do WhatsApp da instância.
    De acordo com a documentação oficial, é uma requisição GET.
    
    :param nome_instancia: Nome único da instância (variável/dinâmico)
    :return: Dicionário contendo a resposta com o QR code (base64) e pairing code, ou None
    """
    url = f"{EVOLUTION_SERVER_URL}/instance/connect/{nome_instancia}"
    
    headers = {
        "apikey": EVOLUTION_API_KEY
    }
    
    print(f"Enviando requisição GET para conectar a instância '{nome_instancia}' (gerar QR Code)...")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dados_resposta = response.json()
        print("QR Code / Conexão gerada com sucesso!")
        return dados_resposta
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao conectar instância: {http_err}")
        if response.text:
            print(f"Detalhes do erro: {response.text}")
        return None
    except Exception as err:
        print(f"Erro inesperado ao conectar instância: {err}")
        return None

def listar_contatos(nome_instancia):
    """
    Busca os contatos da instância do WhatsApp na Evolution API.
    A requisição utiliza POST na rota /chat/findContacts/{nome_instancia}
    """
    url = f"{EVOLUTION_SERVER_URL}/chat/findContacts/{nome_instancia}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    payload = {}  # Busca todos
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao listar contatos: {http_err}")
        if response.text:
            print(f"Detalhes do erro: {response.text}")
        return []
    except Exception as err:
        print(f"Erro inesperado ao listar contatos: {err}")
        return []

def listar_conversas(nome_instancia):
    """
    Busca as conversas da instância do WhatsApp na Evolution API.
    A requisição utiliza POST na rota /chat/findChats/{nome_instancia}
    """
    url = f"{EVOLUTION_SERVER_URL}/chat/findChats/{nome_instancia}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    payload = {}  # Busca todas as conversas
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao listar conversas: {http_err}")
        if response.text:
            print(f"Detalhes do erro: {response.text}")
        return []
    except Exception as err:
        print(f"Erro inesperado ao listar conversas: {err}")
        return []

def verificar_conexao(nome_instancia):
    """
    Verifica o estado da conexão da instância.
    Tenta usar a rota /instance/fetchInstances para obter o nome e número do perfil conectado.
    Se falhar, faz o fallback para /instance/connectionState/{nome_instancia}.
    """
    headers = {
        "apikey": EVOLUTION_API_KEY
    }
    
    # 1. Tenta obter informações detalhadas do perfil conectado via fetchInstances
    try:
        url = f"{EVOLUTION_SERVER_URL}/instance/fetchInstances?instanceName={nome_instancia}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dados = response.json()
            if isinstance(dados, list) and len(dados) > 0:
                inst = dados[0]
                state = "open" if inst.get("connectionStatus") == "open" else "disconnected"
                
                profile_name = inst.get("profileName")
                owner_jid = inst.get("ownerJid")
                profile_pic_url = inst.get("profilePicUrl")
                
                # Se estiver conectado mas o nome de perfil estiver nulo, busca usando fetchProfile complementar
                if state == "open" and owner_jid and not profile_name:
                    try:
                        raw_number = owner_jid.split("@")[0]
                        profile_url = f"{EVOLUTION_SERVER_URL}/chat/fetchProfile/{nome_instancia}"
                        profile_response = requests.post(
                            profile_url,
                            json={"number": raw_number},
                            headers={"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY},
                            timeout=5
                        )
                        if profile_response.status_code == 200:
                            profile_data = profile_response.json()
                            profile_name = profile_data.get("name")
                    except Exception as p_err:
                        print(f"Erro ao buscar profileName complementar para '{nome_instancia}': {p_err}")
                
                return {
                    "instance": {
                        "instanceName": nome_instancia,
                        "state": state,
                        "ownerJid": owner_jid,
                        "profileName": profile_name,
                        "profilePicUrl": profile_pic_url
                    }
                }
    except Exception as err:
        print(f"Erro ao verificar conexão via fetchInstances para '{nome_instancia}': {err}")

    # 2. Fallback para a rota original caso o fetchInstances falhe ou não retorne dados
    try:
        url_fallback = f"{EVOLUTION_SERVER_URL}/instance/connectionState/{nome_instancia}"
        response = requests.get(url_fallback, headers=headers)
        response.raise_for_status()
        dados_fallback = response.json()
        
        # Adapta o retorno do fallback para incluir chaves vazias se não existirem
        instance_data = dados_fallback.get("instance", {})
        return {
            "instance": {
                "instanceName": instance_data.get("instanceName", nome_instancia),
                "state": instance_data.get("state", "disconnected"),
                "ownerJid": None,
                "profileName": None,
                "profilePicUrl": None
            }
        }
    except Exception as err:
        print(f"Erro no fallback verificar_conexao para '{nome_instancia}': {err}")
        return None

def desconectar_instancia(nome_instancia):
    """
    Desconecta a sessão do WhatsApp da instância (realiza o logout).
    A requisição utiliza DELETE na rota /instance/logout/{nome_instancia}
    """
    url = f"{EVOLUTION_SERVER_URL}/instance/logout/{nome_instancia}"
    
    headers = {
        "apikey": EVOLUTION_API_KEY
    }
    
    print(f"Enviando requisição DELETE para deslogar a instância '{nome_instancia}'...")
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao desconectar instância '{nome_instancia}': {http_err}")
        if response.text:
            print(f"Detalhes do erro: {response.text}")
        return None
    except Exception as err:
        print(f"Erro inesperado ao desconectar instância '{nome_instancia}': {err}")
        return None

def deletar_instancia(nome_instancia):
    """
    Exclui a instância permanentemente da Evolution API.
    A requisição utiliza DELETE na rota /instance/delete/{nome_instancia}
    """
    url = f"{EVOLUTION_SERVER_URL}/instance/delete/{nome_instancia}"
    
    headers = {
        "apikey": EVOLUTION_API_KEY
    }
    
    print(f"Enviando requisição DELETE para excluir a instância '{nome_instancia}'...")
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao deletar instância '{nome_instancia}': {http_err}")
        if response.text:
            print(f"Detalhes do erro: {response.text}")
        return None
    except Exception as err:
        print(f"Erro inesperado ao deletar instância '{nome_instancia}': {err}")
        return None

def configurar_webhook(nome_instancia, webhook_url="http://webhook-crm:8001/webhook"):
    """
    Configura o Webhook na Evolution API para a instância especificada.
    
    :param nome_instancia: Nome único da instância
    :param webhook_url: URL do seu webhook
    :return: Dicionário com a resposta da API ou None em caso de erro
    """
    url = f"{EVOLUTION_SERVER_URL}/webhook/set/{nome_instancia}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    # Eventos base comuns para escutar no CRM
    payload = {
        "webhook": {
            "enabled": True,
            "url": webhook_url,
            "webhookByEvents": False,
            "webhookBase64": False,
            "events": [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "MESSAGES_DELETE",
                "SEND_MESSAGE",
                "CONNECTION_UPDATE",
                "CALL",
                "PRESENCE_UPDATE"
            ]
        }
    }
    
    print(f"Enviando requisição POST para configurar webhook na instância '{nome_instancia}'...")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Webhook configurado com sucesso para a instância '{nome_instancia}'!")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao configurar webhook '{nome_instancia}': {http_err}")
        if response.text:
            print(f"Detalhes do erro: {response.text}")
        return None
    except Exception as err:
        print(f"Erro inesperado ao configurar webhook '{nome_instancia}': {err}")
        return None


if __name__ == "__main__":
    import sys
    import json
    
    # Nome da instância recebido por argumento ou padrão de teste
    instancia_teste = sys.argv[1] if len(sys.argv) > 1 else "instancia_teste_ladrilho"
    
    print("--- Testando Criação e Conexão Automática de Instância ---")
    
    # Passo 1: Criar a instância
    resultado_criacao = criar_instancia(nome_instancia=instancia_teste)
    
    if resultado_criacao:
        print("\nPasso 1 Concluído! Resposta de Criação:")
        print(json.dumps(resultado_criacao, indent=2, ensure_ascii=False))
        
        print("\n" + "="*50 + "\n")
        
        # Passo 2: Conectar e obter o QR Code
        resultado_conexao = conectar_instancia(nome_instancia=instancia_teste)
        if resultado_conexao:
            print("\nPasso 2 Concluído! Resposta de Conexão (QR Code):")
            # Vamos mascarar o base64 longo no print do terminal para não poluir
            copia_resposta = json.loads(json.dumps(resultado_conexao))
            try:
                base64_data = copia_resposta.get("base64", "")
                if not base64_data and "qrcode" in copia_resposta:
                    base64_data = copia_resposta["qrcode"].get("base64", "")
                
                if base64_data and len(base64_data) > 100:
                    # Mostra só o início do base64 para confirmar que veio
                    if "qrcode" in copia_resposta:
                        copia_resposta["qrcode"]["base64"] = base64_data[:60] + "... [TRUNCADO]"
                    else:
                        copia_resposta["base64"] = base64_data[:60] + "... [TRUNCADO]"
            except Exception:
                pass
                
            print(json.dumps(copia_resposta, indent=2, ensure_ascii=False))
            
            print("\n" + "="*50 + "\n")
            
            # Passo 3: Configurar Webhook
            resultado_webhook = configurar_webhook(nome_instancia=instancia_teste)
            if resultado_webhook:
                print("\nPasso 3 Concluído! Resposta de Configuração do Webhook:")
                print(json.dumps(resultado_webhook, indent=2, ensure_ascii=False))
            else:
                print("\nFalha ao configurar o Webhook.")
        else:
            print("\nFalha ao obter o QR Code de conexão.")
    else:
        print("\nFalha ao criar a instância. Abortando passo de conexão.")
