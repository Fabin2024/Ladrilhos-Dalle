"""
URL configuration for CRM project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from cadastro import views
from cadastro.views import workspace_view, delete_workspace, dashboard_view, criar_etapa, deletar_etapa, deletar_lead, atendimento_view, qrcode_view, listar_contatos_view, listar_conversas_view, listar_mensagens_view, status_conexao_view, desconectar_instancia_view, deletar_instancia_view, agente_view, canais, deletar_canal, analise_view, api_analise_ia, toggle_agente_view, salvar_configuracoes_agente_view, upload_conhecimento_view, deletar_conhecimento_view, atualizar_etapa_lead, finalizar_lead
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('workspace/', workspace_view, name='workspace'),
    path('workspace/delete/<int:workspace_id>/', delete_workspace),
    path('workspace/<int:workspace_id>/dashboard/', dashboard_view, name='dashboard'),
    path('workspace/<int:workspace_id>/etapa/nova/', criar_etapa, name='criar_etapa'),
    path('workspace/<int:workspace_id>/lead/atualizar_etapa/', atualizar_etapa_lead, name='atualizar_etapa_lead'),
    path('workspace/<int:workspace_id>/etapa/<int:etapa_id>/deletar/', deletar_etapa, name='deletar_etapa'),
    path('workspace/<int:workspace_id>/lead/<int:lead_id>/deletar/', deletar_lead, name='deletar_lead'),
    path('workspace/<int:workspace_id>/lead/<int:lead_id>/finalizar/', finalizar_lead, name='finalizar_lead'),
    path('workspace/<int:workspace_id>/atendimento/', atendimento_view, name='atendimento'),
    path('workspace/<int:workspace_id>/atendimento/qrcode/', qrcode_view, name='qrcode_view'),
    path('workspace/<int:workspace_id>/atendimento/contatos/', listar_contatos_view, name='listar_contatos'),
    path('workspace/<int:workspace_id>/atendimento/conversas/', listar_conversas_view, name='listar_conversas'),
    path('workspace/<int:workspace_id>/atendimento/conversas/<int:lead_id>/', listar_mensagens_view, name='listar_mensagens'),
    path('workspace/<int:workspace_id>/atendimento/status/', status_conexao_view, name='status_conexao'),
    path('workspace/<int:workspace_id>/atendimento/desconectar/', desconectar_instancia_view, name='desconectar_instancia'),
    path('workspace/<int:workspace_id>/atendimento/deletar/', deletar_instancia_view, name='deletar_instancia'),
    path('workspace/<int:workspace_id>/agente/', agente_view, name='agente'),
    path('workspace/<int:workspace_id>/agente/toggle/', toggle_agente_view, name='toggle_agente'),
    path('workspace/<int:workspace_id>/agente/salvar_configuracoes/', salvar_configuracoes_agente_view, name='salvar_configuracoes_agente'),
    path('workspace/<int:workspace_id>/agente/conhecimento/upload/', upload_conhecimento_view, name='upload_conhecimento'),
    path('workspace/<int:workspace_id>/agente/conhecimento/<int:doc_id>/deletar/', deletar_conhecimento_view, name='deletar_conhecimento'),
    path('workspace/<int:workspace_id>/canais/', canais, name='canais'),
    path('workspace/<int:workspace_id>/canais/<int:canal_id>/delete/', deletar_canal, name='deletar_canal'),
    path('workspace/<int:workspace_id>/analise/', analise_view, name='analise'),
    path('workspace/<int:workspace_id>/analise/ia/', api_analise_ia, name='api_analise_ia'),
]
