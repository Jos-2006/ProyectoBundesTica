from django.contrib import admin
from django.db.models import Count

from .models import Equipo, Jugador
from .serializers import equipo_en_torneo_en_curso


class JugadorEnLinea(admin.TabularInline):
    model = Jugador
    fields = ['nombre', 'identificacion', 'numero_camiseta', 'posicion']
    extra = 1


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'entrenador', 'ciudad', 'cantidad_jugadores']
    search_fields = ['nombre', 'entrenador', 'ciudad']
    inlines = [JugadorEnLinea]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_jugadores=Count('jugadores'))

    @admin.display(description='Jugadores', ordering='num_jugadores')
    def cantidad_jugadores(self, equipo):
        return equipo.num_jugadores


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'identificacion', 'numero_camiseta', 'posicion', 'equipo']
    list_filter = ['equipo', 'posicion']
    search_fields = ['nombre', 'identificacion']

    def has_delete_permission(self, request, obj=None):
        # La plantilla se congela mientras el equipo juega un torneo en curso.
        if obj is not None and equipo_en_torneo_en_curso(obj.equipo_id):
            return False
        return super().has_delete_permission(request, obj)
