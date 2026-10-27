from django.contrib import admin
from .models import Equipo, Jugador


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'numero_camiseta', 'identificacion', 'equipo')
    list_filter = ('equipo',)
    search_fields = ('nombre', 'identificacion')