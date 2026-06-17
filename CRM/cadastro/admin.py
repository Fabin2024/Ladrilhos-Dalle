from django.contrib import admin
from .models import Workspace, etapas, canais


class wokspace_admin(admin.ModelAdmin):

    list_display = ('id','Workpaces_name','nicho','description')
    search_fields = ('Workpaces_name',)

class etapas_admin(admin.ModelAdmin):

    list_display=('id','nome')
    search_fields=('nome',)

class canais_admin (admin.ModelAdmin):

    list_display = ('id','nome','numero')
    search_fields = ('nome','numero')

admin.site.register(Workspace,wokspace_admin)
admin.site.register(etapas,etapas_admin)
admin.site.register(canais,canais_admin)
