from django.db.models import Count, Q

from rest_framework import viewsets

from backend_bundestica.excepciones import Conflicto
from backend_bundestica.api import ConfiguracionApi
from backend_bundestica.permissions import SOLO_ADMINISTRADOR, TODOS_LOS_ROLES

from .models import Equipo, Jugador
from .serializers import (
    EquipoSerializer,
    JugadorSerializer,
    equipo_en_torneo_en_curso,
    normalizar_identificacion,
    torneo_que_quedaria_sin_minimo,
)


class EquipoViewSet(ConfiguracionApi, viewsets.ModelViewSet):
    """
    CRUD de equipos.

    Filtros:   ?ciudad=San José   ?con_jugadores=true
    Búsqueda:  ?search=texto      (nombre, entrenador, ciudad)
    Orden:     ?ordering=nombre | -cantidad_jugadores | fecha_registro
    """

    serializer_class = EquipoSerializer
    roles_lectura = TODOS_LOS_ROLES
    roles_escritura = SOLO_ADMINISTRADOR

    search_fields = ['nombre', 'entrenador', 'ciudad']
    ordering_fields = ['nombre', 'fecha_registro', 'cantidad_jugadores', 'torneos_ganados']
    ordering = ['nombre']
    campos_filtro = {
        'ciudad': ('ciudad__iexact', 'texto'),
        'con_jugadores': ('metodo:filtrar_con_jugadores', 'booleano'),
    }

    def get_queryset(self):
        # Consulta ORM: anotaciones con Count + prefetch de la plantilla.
        return Equipo.objects.annotate(
            cantidad_jugadores=Count('jugadores', distinct=True),
            torneos_ganados=Count('campeonatos', distinct=True),
        ).prefetch_related('jugadores')

    def filtrar_con_jugadores(self, queryset, valor):
        return queryset.filter(cantidad_jugadores__gt=0) if valor else queryset.filter(cantidad_jugadores=0)

    def perform_destroy(self, equipo):
        if equipo.inscripciones.exists():
            raise Conflicto(
                'No se puede eliminar un equipo que está o estuvo inscrito en un torneo.'
            )
        equipo.delete()


class JugadorViewSet(ConfiguracionApi, viewsets.ModelViewSet):
    """
    CRUD de jugadores. Cada jugador pertenece a un equipo.

    Un jugador pertenece a un solo equipo: la identificación es única.

    Filtros:   ?equipo=1  ?posicion=DEL  ?numero_camiseta=9  ?torneo=2  ?identificacion=...
    Búsqueda:  ?search=texto  (nombre, identificación, equipo)
    Orden:     ?ordering=nombre | numero_camiseta | -goles_totales
    """

    serializer_class = JugadorSerializer
    roles_lectura = TODOS_LOS_ROLES
    roles_escritura = SOLO_ADMINISTRADOR

    search_fields = ['nombre', 'identificacion', 'equipo__nombre']
    ordering_fields = ['nombre', 'numero_camiseta', 'goles_totales', 'equipo__nombre']
    ordering = ['equipo__nombre', 'numero_camiseta']
    campos_filtro = {
        'equipo': ('equipo_id', 'entero'),
        'posicion': ('posicion', 'mayusculas'),
        'numero_camiseta': ('numero_camiseta', 'entero'),
        'identificacion': ('metodo:filtrar_por_identificacion', 'texto'),
        # Filtro por relación: jugadores de equipos inscritos en un torneo.
        'torneo': ('equipo__inscripciones__torneo_id', 'entero'),
    }

    def get_queryset(self):
        # Consulta ORM: select_related + goles anotados (sin contar autogoles).
        return Jugador.objects.select_related('equipo').annotate(
            goles_totales=Count('goles', filter=~Q(goles__tipo='AUTOGOL'), distinct=True)
        )

    def filtrar_por_identificacion(self, queryset, valor):
        return queryset.filter(identificacion=normalizar_identificacion(valor))

    def perform_destroy(self, jugador):
        if equipo_en_torneo_en_curso(jugador.equipo_id):
            raise Conflicto(
                'No se puede eliminar un jugador de un equipo que juega un torneo en curso.'
            )
        torneo = torneo_que_quedaria_sin_minimo(jugador.equipo_id)
        if torneo:
            raise Conflicto(
                f'{jugador.equipo.nombre} quedaría con menos de {torneo.minimo_jugadores_por_equipo} '
                f'jugadores, el mínimo del torneo "{torneo.nombre}" en el que está inscrito.'
            )
        # Si tiene goles registrados, ProtectedError -> 409.
        jugador.delete()
