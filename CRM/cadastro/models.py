from django.db import models

class Workspace(models.Model):

    id = models.AutoField(primary_key=True)
    Workpaces_name = models.CharField()
    nicho = models.CharField(null=True,blank=True)
    description = models.CharField(null=True,blank=True)
    agente_ativo = models.BooleanField(default=False)
    agente_nome = models.CharField(max_length=255, default="Agente IA Assistente")
    agente_instrucoes = models.TextField(
        default="Você é um assistente de prospecção do Dalle Piagge Ladrilhos. Responda de forma clara e objetiva.",
        blank=True
    )

    def __str__(self):
        return self.Workpaces_name


class DocumentoConhecimento(models.Model):
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='conhecimentos')
    arquivo = models.FileField(upload_to='conhecimento/')
    nome_arquivo = models.CharField(max_length=255)
    tamanho = models.CharField(max_length=50, null=True, blank=True)
    data_upload = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nome_arquivo


class etapas(models.Model):

    id = models.AutoField(primary_key=True)
    nome = models.CharField()

    def __str__(self):
        return self.nome


class canais(models.Model):

    id = models.AutoField(primary_key=True)
    nome = models.CharField()
    numero = models.CharField(max_length=50)
    

class Lead(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255, default="Novo Contato")
    numero = models.CharField(max_length=50) # ex: 5512981565315@s.whatsapp.net
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True)
    etapa = models.ForeignKey(etapas, on_delete=models.SET_NULL, null=True, blank=True)
    finalizado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nome} ({self.numero})"

class Mensagem(models.Model):
    id = models.AutoField(primary_key=True)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="mensagens")
    texto = models.TextField()
    from_me = models.BooleanField(default=False) # True se o bot enviou, False se o cliente enviou
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        remetente = "Bot" if self.from_me else "Cliente"
        return f"[{remetente}] {self.texto[:30]}"
