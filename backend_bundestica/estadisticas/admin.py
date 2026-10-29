from django.contrib import admin

from torneos.models import Torneo

from .models import Estadistica
from .serializers import porcentaje
from .servicios import tabla_ordenada


class TorneoFinalizadoFiltro(admin.SimpleListFilter):
    title = 'torneo'
    parameter_name = 'torneo'

    def lookups(self, request, model_admin):
        return [(t.pk, t.nombre) for t in Torneo.objects.filter(estado=Torneo.Estado.FINALIZADO)]

    def queryset(self, request, queryset):
        return queryset.filter(torneo_id=self.value()) if self.value() else queryset


@admin.register(Estadistica)
class EstadisticaAdmin(admin.ModelAdmin):
    """Tabla final de posiciones: SOLO torneos finalizados. Es de solo lectura."""

    list_display = ['torneo', 'posicion', 'equipo', 'campeon', 'pts', 'pj', 'pg', 'pe', 'pp',
                    'gf', 'gc', 'dg', 'pct_victorias', 'pct_empates', 'pct_derrotas', 'rendimiento']
    list_filter = [TorneoFinalizadoFiltro]
    list_display_links = None

    def get_queryset(self, request):
        return (super().get_queryset(request)
                .filter(torneo__estado=Torneo.Estado.FINALIZADO)
                .select_related('torneo', 'equipo')
                .order_by('-torneo__fecha_fin', 'torneo__nombre', *Estadistica.ORDEN_TABLA))

    def changelist_view(self, request, extra_context=None):
        self.posiciones = {}
        return super().changelist_view(request, extra_context)

    @admin.display(description='Pos.')
    def posicion(self, fila):
        if fila.torneo_id not in self.posiciones:
            ids = list(tabla_ordenada(fila.torneo).values_list('pk', flat=True))
            self.posiciones[fila.torneo_id] = {pk: n for n, pk in enumerate(ids, start=1)}
        return self.posiciones[fila.torneo_id].get(fila.pk)

    @admin.display(description='Pts')
    def pts(self, fila):
        return fila.puntos

    @admin.display(description='PJ')
    def pj(self, fila):
        return fila.partidos_jugados

    @admin.display(description='PG')
    def pg(self, fila):
        return fila.partidos_ganados

    @admin.display(description='PE')
    def pe(self, fila):
        return fila.partidos_empatados

    @admin.display(description='PP')
    def pp(self, fila):
        return fila.partidos_perdidos

    @admin.display(description='GF')
    def gf(self, fila):
        return fila.goles_a_favor

    @admin.display(description='GC')
    def gc(self, fila):
        return fila.goles_en_contra

    @admin.display(description='DG')
    def dg(self, fila):
        return fila.diferencia_goles

    @admin.display(description='Campeón', boolean=True)
    def campeon(self, fila):
        return fila.equipo_id == fila.torneo.campeon_id

    @admin.display(description='% Vict.')
    def pct_victorias(self, fila):
        return f'{porcentaje(fila.partidos_ganados, fila.partidos_jugados)} %'

    @admin.display(description='% Emp.')
    def pct_empates(self, fila):
        return f'{porcentaje(fila.partidos_empatados, fila.partidos_jugados)} %'

    @admin.display(description='% Derr.')
    def pct_derrotas(self, fila):
        return f'{porcentaje(fila.partidos_perdidos, fila.partidos_jugados)} %'

    @admin.display(description='Rend.')
    def rendimiento(self, fila):
        return f'{porcentaje(fila.puntos, fila.partidos_jugados * fila.torneo.puntos_victoria)} %'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
