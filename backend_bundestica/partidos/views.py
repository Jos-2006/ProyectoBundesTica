from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.response import Response

from backend_bundestica.api import ConfiguracionApi
from backend_bundestica.permissions import ADMINISTRADOR_Y_OPERADOR, TODOS_LOS_ROLES

from . import servicios
from .models import Partido, Resultado
from .serializers import PartidoSerializer, ResultadoSerializer


class PartidoViewSet(ConfiguracionApi, viewsets.ModelViewSet):
    """
    Partidos: el usuario decide quién se enfrenta en cada torneo.

    Filtros:   ?torneo=1 ?estado=PROGRAMADO|FINALIZADO ?equipo=3
               ?fecha_desde=2026-11-01 ?fecha_hasta=2026-11-30
    Búsqueda:  ?search=texto (equipos o torneo)
    Orden:     ?ordering=fecha | -fecha
    """

    serializer_class = PartidoSerializer
    roles_lectura = TODOS_LOS_ROLES
    roles_escritura = ADMINISTRADOR_Y_OPERADOR

    search_fields = ['equipo_local__nombre', 'equipo_visitante__nombre', 'torneo__nombre']
    ordering_fields = ['fecha', 'id']
    ordering = ['torneo_id', 'fecha', 'id']
    campos_filtro = {
        'torneo': ('torneo_id', 'entero'),
        'estado': ('estado', 'mayusculas'),
        'equipo': ('metodo:filtrar_por_equipo', 'entero'),
        'fecha_desde': ('fecha__gte', 'fecha'),
        'fecha_hasta': ('fecha__lte', 'fecha'),
    }

    def get_queryset(self):
        return Partido.objects.select_related(
            'torneo', 'equipo_local', 'equipo_visitante',
            'resultado__ganador', 'resultado__perdedor',
        )

    def filtrar_por_equipo(self, queryset, equipo_id):
        return queryset.filter(Q(equipo_local_id=equipo_id) | Q(equipo_visitante_id=equipo_id))

    def perform_destroy(self, partido):
        servicios.exigir_sin_resultado(partido, 'eliminar')
        partido.delete()


class ResultadoViewSet(ConfiguracionApi, viewsets.ModelViewSet):
    """
    Goles: se elige un partido y se registra cuánto quedaron.
    La API indica quién ganó, quién perdió o si quedaron empatados.

    Filtros:   ?torneo=1 ?equipo=2 ?empate=true ?ganador=3
    Orden:     ?ordering=fecha | -fecha
    """

    serializer_class = ResultadoSerializer
    roles_lectura = TODOS_LOS_ROLES
    roles_escritura = ADMINISTRADOR_Y_OPERADOR

    ordering_fields = [('partido__fecha'), 'fecha_registro']
    ordering = ['-partido__fecha', '-id']
    campos_filtro = {
        'torneo': ('partido__torneo_id', 'entero'),
        'partido': ('partido_id', 'entero'),
        'equipo': ('metodo:filtrar_por_equipo', 'entero'),
        'ganador': ('ganador_id', 'entero'),
        'empate': ('empate', 'booleano'),
    }

    def get_queryset(self):
        return Resultado.objects.select_related(
            'partido__torneo', 'partido__equipo_local', 'partido__equipo_visitante',
            'ganador', 'perdedor',
        ).prefetch_related('anotadores__jugador', 'anotadores__equipo')

    def filtrar_por_equipo(self, queryset, equipo_id):
        return queryset.filter(
            Q(partido__equipo_local_id=equipo_id) | Q(partido__equipo_visitante_id=equipo_id)
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = serializer.save()
        campeon = serializer.context.get('campeon')

        datos = self.get_serializer(self.get_queryset().get(pk=resultado.pk)).data
        respuesta = {
            'mensaje': f'Resultado registrado: {datos["marcador"]}. {datos["resultado"]}.',
            'torneo_finalizado': campeon is not None,
            'resultado': datos,
        }
        if campeon is not None:
            respuesta['campeon'] = {'id': campeon.id, 'nombre': campeon.nombre}
            respuesta['mensaje'] += f' ¡Torneo terminado! Campeón: {campeon.nombre}.'
        return Response(respuesta, status=status.HTTP_201_CREATED)

    def perform_destroy(self, resultado):
        servicios.eliminar_resultado(resultado)
