from django.shortcuts import render, redirect
from .models import Workspace, etapas, Lead, Mensagem
from .forms import registrar_workspace,registrar_etapa,canais_register
from django.http import JsonResponse
from create_instance import criar_instancia, conectar_instancia, listar_contatos, listar_conversas, verificar_conexao, desconectar_instancia, deletar_instancia
import re
import json
from django.views.decorators.csrf import csrf_exempt
from .Agente import criar_agente
from .agente_analise import analisar_dashboard
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@login_required
def workspace_view(request):
    if request.method == 'POST':
        form = registrar_workspace(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/workspace/')
            
    workspace_check = Workspace.objects.all()
    form = registrar_workspace()
    
    search_query = request.GET.get("search")
    if search_query:
        workspace_check = workspace_check.filter(Workpaces_name__icontains=search_query)

    return render(request, 'Workspace.html', {
        'workspace_check': workspace_check,
        'form': form
    })

@login_required
def delete_workspace(request, workspace_id):
    if request.method == 'POST':
        ws = Workspace.objects.filter(id=workspace_id)
        ws.delete()
    return redirect('/workspace/')
    

@login_required
def dashboard_view(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    todas_etapas = etapas.objects.all()
    leads = Lead.objects.filter(workspace=workspace)
    
    return render(request, "Dashboard.html", {
        "workspace": workspace,
        "etapas": todas_etapas,
        "leads": leads
    })

@login_required
def criar_etapa(request, workspace_id):
    if request.method == "POST":
        form = registrar_etapa(request.POST)
        if form.is_valid():
            form.save()
            
    return redirect(f'/workspace/{workspace_id}/dashboard/')

@login_required
def deletar_etapa(request, workspace_id, etapa_id):
    if request.method == "POST":
        e = etapas.objects.filter(id=etapa_id)
        e.delete()
    return redirect(f'/workspace/{workspace_id}/dashboard/')

@login_required
def deletar_lead(request, workspace_id, lead_id):
    if request.method == "POST":
        try:
            lead = Lead.objects.get(id=lead_id, workspace_id=workspace_id)
            lead.delete()
        except Lead.DoesNotExist:
            pass
    return redirect(f'/workspace/{workspace_id}/dashboard/')

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def atualizar_etapa_lead(request, workspace_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lead_id = data.get('lead_id')
            etapa_id = data.get('etapa_id')
            
            lead = Lead.objects.get(id=lead_id, workspace_id=workspace_id)
            etapa = etapas.objects.get(id=etapa_id)
            
            lead.etapa = etapa
            lead.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@csrf_exempt
@login_required
def finalizar_lead(request, workspace_id, lead_id):
    if request.method == "POST":
        try:
            lead = Lead.objects.get(id=lead_id, workspace_id=workspace_id)
            lead.finalizado = not lead.finalizado # toggle
            lead.save()
            return JsonResponse({'success': True, 'finalizado': lead.finalizado})
        except Lead.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Lead não encontrado.'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

from .models import canais as model_canais

def get_instance_name(request, workspace_id):
    instance = request.GET.get('instance')
    if instance:
        return instance
    workspace = Workspace.objects.get(id=workspace_id)
    base = re.sub(r'[^a-zA-Z0-9]', '_', workspace.Workpaces_name).lower()
    return f"ws_{workspace_id}_{base}"

@login_required
def atendimento_view(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    canal_id = request.GET.get('canal')
    
    canal_nome = ""
    
    if canal_id:
        canal = model_canais.objects.get(id=canal_id)
        nome_limpo = re.sub(r'[^a-zA-Z0-9]', '_', canal.nome).lower()
        instance_name = f"ws_{workspace_id}_canal_{nome_limpo}"
        canal_nome = canal.nome
    else:
        primeiro_canal = model_canais.objects.first()
        if primeiro_canal:
            nome_limpo = re.sub(r'[^a-zA-Z0-9]', '_', primeiro_canal.nome).lower()
            instance_name = f"ws_{workspace_id}_canal_{nome_limpo}"
            canal_nome = primeiro_canal.nome
        else:
            nome_base = re.sub(r'[^a-zA-Z0-9]', '_', workspace.Workpaces_name).lower()
            instance_name = f"ws_{workspace_id}_{nome_base}"
            canal_nome = instance_name
            
    return render(request, 'Atendimento.html', {
        'workspace': workspace,
        'instance_name': instance_name,
        'canal_nome': canal_nome
    })


@login_required
def qrcode_view(request, workspace_id):
    instance_name = get_instance_name(request, workspace_id)
    
    # 1. Cria a instância (a API lida com a duplicação se já existir)
    criar_instancia(instance_name)
    
    # 2. Conecta para obter o QR Code
    con_data = conectar_instancia(instance_name)
    
    if con_data:
        qrcode_base64 = None
        pairing_code = None
        
        # A Evolution API v2 pode retornar o base64 aninhado em 'qrcode'
        if isinstance(con_data, dict):
            if "qrcode" in con_data:
                qrcode_base64 = con_data["qrcode"].get("base64")
                pairing_code = con_data["qrcode"].get("pairingCode")
            else:
                qrcode_base64 = con_data.get("base64")
                pairing_code = con_data.get("pairingCode")
                
        return JsonResponse({
            "success": True,
            "base64": qrcode_base64,
            "pairing_code": pairing_code,
            "instance_name": instance_name
        })
        
    return JsonResponse({
        "success": False,
        "message": "Não foi possível obter o QR Code. Certifique-se de que a Evolution API está ativa."
    })

@login_required
def listar_contatos_view(request, workspace_id):
    instance_name = get_instance_name(request, workspace_id)

    contatos = listar_contatos(instance_name)
    
    if contatos is not None:
        return JsonResponse({
            "success": True,
            "contatos": contatos
        })
        
    return JsonResponse({
        "success": False,
        "message": "Não foi possível buscar os contatos."
    })

@login_required
def listar_conversas_view(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    leads = Lead.objects.filter(workspace=workspace)
    
    conversas = []
    for lead in leads:
        ultima_mensagem = lead.mensagens.order_by('-timestamp').first()
        texto = ultima_mensagem.texto if ultima_mensagem else "Sem mensagens"
        time_str = ultima_mensagem.timestamp.strftime("%H:%M") if ultima_mensagem else ""
        
        conversas.append({
            "id": lead.id,
            "name": lead.nome,
            "number": lead.numero,
            "lastMessage": texto,
            "unread": 0,
            "time": time_str,
            "profilePicUrl": "",
            "initials": lead.nome[:2].upper()
        })
        
    return JsonResponse({
        "success": True,
        "conversas": conversas
    })

@login_required
def listar_mensagens_view(request, workspace_id, lead_id):
    try:
        lead = Lead.objects.get(id=lead_id, workspace_id=workspace_id)
        mensagens = lead.mensagens.order_by('timestamp')
        
        msgs_data = []
        for msg in mensagens:
            msgs_data.append({
                "sender": "bot" if msg.from_me else "user",
                "text": msg.texto,
                "time": msg.timestamp.strftime("%H:%M")
            })
            
        return JsonResponse({
            "success": True,
            "messages": msgs_data
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})

@login_required
def status_conexao_view(request, workspace_id):
    instance_name = get_instance_name(request, workspace_id)

    status = verificar_conexao(instance_name)
    
    if status is not None:
        return JsonResponse({
            "success": True,
            "instance": status.get("instance"),
            "state": status.get("instance", {}).get("state", "disconnected")
        })
        
    return JsonResponse({
        "success": False,
        "message": "Não foi possível buscar o status.",
        "instance_name": instance_name
    })

@login_required
def desconectar_instancia_view(request, workspace_id):
    if request.method == "POST":
        instance_name = get_instance_name(request, workspace_id)
        
        response = desconectar_instancia(instance_name)
        if response is not None:
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "message": "Falha ao desconectar."})
    return JsonResponse({"success": False, "message": "Método inválido."})

@login_required
def deletar_instancia_view(request, workspace_id):
    if request.method == "POST":
        instance_name = get_instance_name(request, workspace_id)
        
        response = deletar_instancia(instance_name)
        if response is not None:
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "message": "Falha ao deletar."})
    return JsonResponse({"success": False, "message": "Método inválido."})




@csrf_exempt
@login_required
def agente_view(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    if request.method == "POST":
        try:
            # Tenta pegar os dados via JSON
            data = json.loads(request.body)
            mensagem = data.get("message", "")
            
            if mensagem:
                # Inicializa o agente passando as instruções dinâmicas
                agente = criar_agente(nome=workspace.agente_nome, instrucoes=workspace.agente_instrucoes, workspace_id=workspace.id)
                resposta = agente.run(mensagem)
                
                # O retorno do Agno/Phidata normalmente possui o atributo content
                texto_resposta = resposta.content if hasattr(resposta, 'content') else str(resposta)
                return JsonResponse({"success": True, "resposta": texto_resposta})
            return JsonResponse({"success": False, "error": "Nenhuma mensagem fornecida."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
            
    conhecimentos = workspace.conhecimentos.all()
    return render(request, "agente.html", {"workspace": workspace, "conhecimentos": conhecimentos})


@csrf_exempt
@login_required
def toggle_agente_view(request, workspace_id):
    if request.method == "POST":
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            data = json.loads(request.body)
            novo_status = data.get("ativo")
            if novo_status is not None:
                workspace.agente_ativo = novo_status
                workspace.save()
            else:
                workspace.agente_ativo = not workspace.agente_ativo
                workspace.save()
                
            return JsonResponse({"success": True, "agente_ativo": workspace.agente_ativo})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
            
    return JsonResponse({"success": False, "message": "Método inválido"})

@csrf_exempt
@login_required
def salvar_configuracoes_agente_view(request, workspace_id):
    if request.method == "POST":
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            data = json.loads(request.body)
            instrucoes = data.get("instrucoes")
            nome = data.get("nome")
            
            updated = False
            if instrucoes is not None:
                workspace.agente_instrucoes = instrucoes
                updated = True
            if nome is not None:
                workspace.agente_nome = nome
                updated = True
                
            if updated:
                workspace.save()
                return JsonResponse({"success": True})
            return JsonResponse({"success": False, "message": "Nenhum dado fornecido."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "message": "Método inválido"})


from .models import canais as model_canais

@login_required
def canais(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    
    if request.method == "POST":
        forms = canais_register(request.POST)
        if forms.is_valid():
            novo_canal = forms.save()
            
            # Cria a nova instância na Evolution API baseada no nome do canal
            nome_limpo = re.sub(r'[^a-zA-Z0-9]', '_', novo_canal.nome).lower()
            instance_name = f"ws_{workspace_id}_canal_{nome_limpo}"
            
            import uuid
            token_gerado = str(uuid.uuid4())
            
            criar_instancia(instance_name, token=token_gerado, numero=novo_canal.numero)
            
            return redirect('canais', workspace_id=workspace_id)
    else:
        forms = canais_register()
        
    lista_canais = model_canais.objects.all()
    
    return render(request, "canais.html", {
        "workspace": workspace,
        "forms": forms,
        "canais": lista_canais
    })

@login_required
def deletar_canal(request, workspace_id, canal_id):
    if request.method == "POST":
        try:
            canal = model_canais.objects.get(id=canal_id)
            nome_limpo = re.sub(r'[^a-zA-Z0-9]', '_', canal.nome).lower()
            instance_name = f"ws_{workspace_id}_canal_{nome_limpo}"
            
            # Chama a função existente em create_instance.py para deletar na Evolution API
            deletar_instancia(instance_name)
            
            # Deleta o registro do banco de dados local
            canal.delete()
        except Exception as e:
            print(f"Erro ao deletar canal: {e}")
            
    return redirect('canais', workspace_id=workspace_id)

@login_required
def analise_view(request, workspace_id):
    import json
    workspace = Workspace.objects.get(id=workspace_id)
    lista_canais = model_canais.objects.all()
    todas_etapas = etapas.objects.all()
    
    labels_status = []
    data_status = []
    
    pendentes_count = 0
    finalizados_count = 0
    
    total_etapas = todas_etapas.count()
    
    from django.utils import timezone
    import calendar
    import datetime
    
    hoje = timezone.now()
    
    month_param = request.GET.get('month')
    year_param = request.GET.get('year')
    
    if month_param and year_param:
        try:
            target_month = int(month_param)
            target_year = int(year_param)
        except ValueError:
            target_month = hoje.month
            target_year = hoje.year
    else:
        target_month = hoje.month
        target_year = hoje.year
    
    # Helper for subtracting months
    def get_past_month(y, m, diff):
        for _ in range(diff):
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        return y, m
        
    historico_labels = []
    historico_entraram = []
    historico_finalizados = []
    
    meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    
    for i in range(5, -1, -1):
        y, m = get_past_month(target_year, target_month, i)
        historico_labels.append(f"{meses_pt[m]}/{y}")
        entraram = Lead.objects.filter(workspace=workspace, criado_em__year=y, criado_em__month=m).count()
        finalizados = Lead.objects.filter(workspace=workspace, finalizado=True, atualizado_em__year=y, atualizado_em__month=m).count()
        historico_entraram.append(entraram)
        historico_finalizados.append(finalizados)
    
    for idx, etapa in enumerate(todas_etapas):
        labels_status.append(etapa.nome)
        count = Lead.objects.filter(workspace=workspace, etapa=etapa, finalizado=False).count()
        data_status.append(count)
        
    pendentes_count = Lead.objects.filter(workspace=workspace, finalizado=False).count()
    finalizados_count = Lead.objects.filter(workspace=workspace, finalizado=True).count()
    
    # Monthly stats relative to target_month
    entraram_mes_count = Lead.objects.filter(workspace=workspace, criado_em__year=target_year, criado_em__month=target_month).count()
    finalizados_mes_count = Lead.objects.filter(workspace=workspace, finalizado=True, atualizado_em__year=target_year, atualizado_em__month=target_month).count()
            
    # Also count leads with no etapa as "Sem Etapa"
    leads_sem_etapa = Lead.objects.filter(workspace=workspace, etapa__isnull=True, finalizado=False).count()
    if leads_sem_etapa > 0:
        labels_status.append("Sem Etapa")
        data_status.append(leads_sem_etapa)
        
    # Return JSON for AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        from django.http import JsonResponse
        return JsonResponse({
            "entraram_mes_count": entraram_mes_count,
            "finalizados_mes_count": finalizados_mes_count,
            "pendentes_count": pendentes_count,
            "finalizados_count": finalizados_count,
            "labels_status": labels_status,
            "data_status": data_status,
            "historico_labels": historico_labels,
            "historico_entraram": historico_entraram,
            "historico_finalizados": historico_finalizados,
            "mes_selecionado": f"{target_year}-{target_month:02d}"
        })
    
    return render(request, "Analise.html", {
        "workspace": workspace,
        "canais": lista_canais,
        "etapas": todas_etapas,
        "labels_status": json.dumps(labels_status),
        "data_status": json.dumps(data_status),
        "pendentes_count": pendentes_count,
        "finalizados_count": finalizados_count,
        "entraram_mes_count": entraram_mes_count,
        "finalizados_mes_count": finalizados_mes_count,
        "historico_labels": json.dumps(historico_labels),
        "historico_entraram": json.dumps(historico_entraram),
        "historico_finalizados": json.dumps(historico_finalizados),
        "target_month": target_month,
        "target_year": target_year
    })

@login_required
def api_analise_ia(request, workspace_id):
    lista_canais = model_canais.objects.all()
    todas_etapas = etapas.objects.all()
    
    qtd_etapas = todas_etapas.count()
    nomes_etapas = [e.nome for e in todas_etapas]
    qtd_canais = lista_canais.count()
    
    resposta = analisar_dashboard(qtd_etapas, nomes_etapas, qtd_canais)
    
    return JsonResponse({"success": True, "analise": resposta})

from .models import DocumentoConhecimento
from .Agente import adicionar_arquivo_ao_rag
import os

@csrf_exempt
@login_required
def upload_conhecimento_view(request, workspace_id):
    if request.method == "POST":
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            if 'arquivo' not in request.FILES:
                return JsonResponse({"success": False, "message": "Nenhum arquivo enviado."})
                
            arquivo = request.FILES['arquivo']
            tamanho = f"{arquivo.size / (1024*1024):.2f} MB" if arquivo.size > 1024*1024 else f"{arquivo.size / 1024:.2f} KB"
            
            documento = DocumentoConhecimento.objects.create(
                workspace=workspace,
                arquivo=arquivo,
                nome_arquivo=arquivo.name,
                tamanho=tamanho
            )
            
            # Adiciona ao RAG
            caminho_absoluto = documento.arquivo.path
            adicionar_arquivo_ao_rag(caminho_absoluto, workspace.id)
            
            return JsonResponse({
                "success": True, 
                "documento": {
                    "id": documento.id,
                    "nome_arquivo": documento.nome_arquivo,
                    "tamanho": documento.tamanho
                }
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "message": "Método inválido"})

@csrf_exempt
@login_required
def deletar_conhecimento_view(request, workspace_id, doc_id):
    if request.method == "DELETE" or request.method == "POST":
        try:
            documento = DocumentoConhecimento.objects.get(id=doc_id, workspace_id=workspace_id)
            if documento.arquivo:
                if os.path.exists(documento.arquivo.path):
                    os.remove(documento.arquivo.path)
            documento.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "message": "Método inválido"})

