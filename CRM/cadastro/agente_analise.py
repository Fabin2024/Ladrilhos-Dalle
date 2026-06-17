from agno.models.openai import OpenAIChat
from agno.agent import Agent
from dotenv import load_dotenv

load_dotenv()


agente = Agent(
    name="Atendente",
    model=OpenAIChat(id="gpt-4o-mini"),
    introduction="""

        Voce é um assistente de propecção para atendimento no whatsapp, você ajuda a empresa
        a conversar com clientes e introduzi-los no CRM.

        """,
    
)

agente_dashboard = Agent(
    name="Analista de Dados",
    model=OpenAIChat(id="gpt-4o-mini"),
    introduction="""
        Você é um Analista de Dados e Especialista em CRM.
        Sua função é fornecer insights curtos, diretos e valiosos sobre o funil de atendimento.
        Sempre responda em português, de forma profissional, encorajadora, e no máximo 1 ou 2 parágrafos curtos.
    """
)

def analisar_dashboard(qtd_etapas, nomes_etapas, qtd_canais):
    prompt = f"O CRM atualmente tem {qtd_etapas} etapas cadastradas no Kanban: {', '.join(nomes_etapas)}. E possuímos {qtd_canais} canais/sessões de atendimento ativos. Avalie este cenário brevemente e dê uma dica de sucesso para a gestão de leads."
    
    try:
        resposta = agente_dashboard.run(prompt)
        return resposta.content if hasattr(resposta, 'content') else str(resposta)
    except Exception as e:
        return f"Não foi possível gerar a análise no momento. Erro: {str(e)}"


