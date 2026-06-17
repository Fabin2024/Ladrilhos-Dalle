from django import forms
from .models import Workspace,etapas,canais


class registrar_workspace(forms.ModelForm):

    class Meta:
        model = Workspace
        fields = ["Workpaces_name", "nicho", "description"]
    
class registrar_etapa(forms.ModelForm):

    class Meta:
        model = etapas
        fields = ["nome"]


class canais_register(forms.ModelForm):

    class Meta:
        model = canais
        fields = ["nome", "numero"]

