from django.db import transaction
from django.db.models import Count, F, Q

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backend_bundestica.api import ConfiguracionApi
from backend_bundestica.excepciones import Conflicto
from backend_bundestica.permissions import SOLO_ADMINISTRADOR, TODOS_LOS_ROLES
from estadisticas.serializers import FilaPosicionesSerializer
from estadisticas.servicios import tabla_ordenada
from partidos.models import Partido

from .models import Torneo
from .serializers import TorneoSerializer
from .servicios import enfrentamientos_pendientes, iniciar_torneo, poner_en_curso


class TorneoViewSet(ConfiguracionApi, viewsets.ModelViewSet):
    """
    CRUD de torneos + acciones del ciclo de vida.

    Filtros:   ?estado=EN_CURSO  ?fecha_desde=2026-01-01  ?fecha_hasta=2026-12-31
               ?campeon=3        ?con_cupos=true
    Búsqueda:  ?search=texto
    Orden:     ?ordering=fecha_inicio | -equipos_inscritos | nombre

    POST /api/torneos/{id}/iniciar/                    empezar antes de llenar el cupo (mín. 2 equipos)
    GET  /api/torneos/{id}/enfrentamientos_pendientes/ partidos que faltan por programar
    GET  /api/torneos/{id}/tabla/                      posiciones actuales (torneo en curso)
    """

    serializer_class = TorneoSerializer
    roles_lectura = TODOS_LOS_ROLES
    roles_escritura = SOLO_ADMINISTRADOR

    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'equipos_inscritos', 'partidos_jugados']
    ordering = ['-fecha_inicio', 'nombre']
    campos_filtro = {
        'estado': ('estado', 'mayusculas'),
        'fecha_desde': ('fecha_inicio__gte', 'fecha'),
        'fecha_hasta': ('fecha_inicio__lte', 'fecha'),
        'campeon': ('campeon_id', 'entero'),
        'con_cupos': ('metodo:filtrar_con_cupos', 'booleano'),
    }

    def get_queryset(self):
        # Consulta ORM: agregaciones condicionales sobre dos relaciones.
        return Torneo.objects.select_related('campeon').annotate(
            equipos_inscritos=Count('inscripciones', distinct=True),
            partidos_jugados=Count(
                'partidos',
                filter=Q(partidos__estado=Partido.Estado.FINALIZADO),
                distinct=True,
            ),
        )

    def filtrar_con_cupos(self, queryset, valor):
        con_cupo = Q(estado=Torneo.Estado.INSCRIPCIONES, equipos_inscritos__lt=F('maximo_equipos'))
        return queryset.filter(con_cupo) if valor else queryset.exclude(con_cupo)

    @transaction.atomic
    def perform_update(self, serializer):
        torneo = serializer.save()
        # Si al editar el máximo queda igual a los inscritos, el torneo ya está lleno.
        inscritos = torneo.inscripciones.count()
        if inscritos >= 2 and inscritos == torneo.maximo_equipos:
            poner_en_curso(torneo)

    def perform_destroy(self, torneo):
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            raise Conflicto('Solo se puede eliminar un torneo que no ha iniciado.')
        torneo.delete()

    def respuesta_torneo(self, pk, **extra):
        return {**extra, 'torneo': self.get_serializer(self.get_queryset().get(pk=pk)).data}

    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """Cierra inscripciones antes de llenar el cupo (mínimo 2 equipos)."""
        torneo = iniciar_torneo(self.get_object().pk)
        return Response(
            self.respuesta_torneo(
                torneo.pk,
                mensaje=f'Torneo en curso: se deben jugar {torneo.cantidad_partidos} partidos.',
            ),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'])
    def enfrentamientos_pendientes(self, request, pk=None):
        torneo = self.get_object()
        if torneo.estado == Torneo.Estado.INSCRIPCIONES:
            pendientes = []
        else:
            pendientes = enfrentamientos_pendientes(torneo)
        return Response({
            'torneo': torneo.nombre,
            'estado': torneo.estado,
            'vueltas': torneo.get_vueltas_display(),
            'partidos_totales': torneo.cantidad_partidos,
            'partidos_programados': torneo.partidos.count(),
            'pendientes_por_programar': len(pendientes),
            'enfrentamientos': [
                {'equipo_local': {'id': local.id, 'nombre': local.nombre},
                 'equipo_visitante': {'id': visita.id, 'nombre': visita.nombre}}
                for local, visita in pendientes
            ],
        })

    @action(detail=True, methods=['get'])
    def tabla(self, request, pk=None):
        """Cómo van las posiciones mientras el torneo se juega."""
        torneo = self.get_object()
        filas = list(tabla_ordenada(torneo))
        contexto = {'posiciones': {fila.pk: n for n, fila in enumerate(filas, start=1)}}
        return Response({
            'torneo': torneo.nombre,
            'estado': torneo.estado,
            'partidos_jugados': torneo.partidos.filter(estado=Partido.Estado.FINALIZADO).count(),
            'partidos_totales': torneo.cantidad_partidos,
            'campeon': torneo.campeon.nombre if torneo.campeon else None,
            'tabla': FilaPosicionesSerializer(filas, many=True, context=contexto).data,
        })
