from django.contrib import admin
from .models import Estadistica


@admin.register(Estadistica)
class EstadisticaAdmin(admin.ModelAdmin):
    list_display = ('id', 'torneo', 'equipo', 'pj', 'pg', 'pe', 'pp', 'gf', 'gc', 'dg', 'pts')
    list_filter = ('torneo', 'equipo')
    search_fields = ('equipo__nombre',)