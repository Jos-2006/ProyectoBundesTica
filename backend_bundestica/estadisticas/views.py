"""
Módulo de estadísticas: SOLO LECTURA y SOLO de torneos FINALIZADOS.

- /api/estadisticas/partidos/                    partidos jugados de torneos finalizados
- /api/estadisticas/torneos/                     torneos finalizados con su campeón
- /api/estadisticas/torneos/{id}/posiciones/     tabla final con porcentajes
- /api/estadisticas/torneos/{id}/goleadores/     tabla de goleadores
- /api/estadisticas/torneos/{id}/resumen/        totales y récords del torneo

(Para ver cómo va un torneo EN_CURSO: GET /api/torneos/{id}/tabla/)
"""

from django.db.models import Count, F, Prefetch, Q, Sum

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from backend_bundestica.api import ConfiguracionApi
from backend_bundestica.permissions import TODOS_LOS_ROLES
from partidos.models import Anotador, Resultado
from torneos.models import Torneo

from .serializers import FilaPosicionesSerializer, PartidoJugadoSerializer, porcentaje
from .servicios import tabla_ordenada


class PartidoJugadoViewSet(ConfiguracionApi, viewsets.ReadOnlyModelViewSet):
    """
    Partidos jugados en torneos finalizados.

    Filtros:  ?torneo=1 ?equipo=2 ?resultado=EMPATE|GANA_LOCAL|GANA_VISITANTE
    Orden:    ?ordering=fecha | -total_goles
    """

    serializer_class = PartidoJugadoSerializer
    roles_lectura = TODOS_LOS_ROLES

    search_fields = ['partido__equipo_local__nombre', 'partido__equipo_visitante__nombre']
    ordering_fields = ['partido__fecha', 'total_goles']
    ordering = ['-partido__fecha', 'id']
    campos_filtro = {
        'torneo': ('partido__torneo_id', 'entero'),
        'equipo': ('metodo:filtrar_por_equipo', 'entero'),
        'resultado': ('metodo:filtrar_por_resultado', 'mayusculas'),
    }

    def get_queryset(self):
        return (
            Resultado.objects.filter(partido__torneo__estado=Torneo.Estado.FINALIZADO)
            .select_related('partido__torneo', 'partido__equipo_local', 'partido__equipo_visitante',
                            'ganador', 'perdedor')
            .prefetch_related(
                Prefetch('anotadores', queryset=Anotador.objects.select_related('jugador').order_by('minuto'))
            )
            .annotate(total_goles=F('goles_local') + F('goles_visitante'))
        )

    def filtrar_por_equipo(self, queryset, equipo_id):
        return queryset.filter(
            Q(partido__equipo_local_id=equipo_id) | Q(partido__equipo_visitante_id=equipo_id)
        )

    def filtrar_por_resultado(self, queryset, resultado):
        condiciones = {
            'EMPATE': Q(empate=True),
            'GANA_LOCAL': Q(goles_local__gt=F('goles_visitante')),
            'GANA_VISITANTE': Q(goles_local__lt=F('goles_visitante')),
        }
        if resultado not in condiciones:
            raise ValidationError({'resultado': 'Use EMPATE, GANA_LOCAL o GANA_VISITANTE.'})
        return queryset.filter(condiciones[resultado])


class EstadisticaTorneoViewSet(ConfiguracionApi, viewsets.ReadOnlyModelViewSet):
    """Estadísticas de torneos finalizados: posiciones, goleadores y resumen."""

    roles_lectura = TODOS_LOS_ROLES

    search_fields = ['nombre']
    ordering_fields = ['fecha_inicio', 'nombre']
    ordering = ['-fecha_inicio']

    def get_queryset(self):
        return Torneo.objects.filter(estado=Torneo.Estado.FINALIZADO).select_related('campeon').annotate(
            equipos=Count('inscripciones', distinct=True),
        )

    def get_object(self):
        # Mensaje claro si el torneo existe pero todavía no termina.
        torneo = Torneo.objects.filter(pk=self.kwargs['pk']).first()
        if torneo is not None and torneo.estado != Torneo.Estado.FINALIZADO:
            raise ValidationError({'detail':
                f'El torneo "{torneo.nombre}" está {torneo.get_estado_display().lower()}; '
                'las estadísticas solo están disponibles para torneos finalizados. '
                f'Para ver cómo va use GET /api/torneos/{torneo.pk}/tabla/.'
            })
        return super().get_object()

    def ficha(self, torneo):
        return {
            'torneo_id': torneo.id,
            'torneo': torneo.nombre,
            'fecha_inicio': torneo.fecha_inicio,
            'fecha_fin': torneo.fecha_fin,
            'vueltas': torneo.get_vueltas_display(),
            'equipos': torneo.equipos,
            'partidos_jugados': torneo.cantidad_partidos,
            'campeon': torneo.campeon.nombre if torneo.campeon else None,
        }

    def list(self, request, *args, **kwargs):
        pagina = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        return self.get_paginated_response([self.ficha(t) for t in pagina])

    def retrieve(self, request, *args, **kwargs):
        return Response(self.ficha(self.get_object()))

    @action(detail=True, methods=['get'])
    def posiciones(self, request, pk=None):
        torneo = self.get_object()
        filas = list(tabla_ordenada(torneo))
        contexto = {'posiciones': {fila.pk: numero for numero, fila in enumerate(filas, start=1)}}
        return Response({
            **self.ficha(torneo),
            'criterio_desempate': 'puntos, diferencia de goles, goles a favor, partidos ganados, nombre',
            'tabla': FilaPosicionesSerializer(filas, many=True, context=contexto).data,
        })

    @action(detail=True, methods=['get'])
    def goleadores(self, request, pk=None):
        torneo = self.get_object()
        try:
            limite = int(request.query_params.get('limite', 10))
        except ValueError:
            raise ValidationError({'limite': 'Debe ser un número entero.'})

        # Consulta ORM: agregación agrupada por jugador, filtrando por relaciones.
        goleadores = (
            Anotador.objects.filter(resultado__partido__torneo=torneo)
            .exclude(tipo=Anotador.Tipo.AUTOGOL)
            .values('jugador_id', 'jugador__nombre', 'jugador__numero_camiseta', 'jugador__equipo__nombre')
            .annotate(
                goles=Count('id'),
                penales=Count('id', filter=Q(tipo=Anotador.Tipo.PENAL)),
                partidos_con_gol=Count('resultado', distinct=True),
            )
            .order_by('-goles', 'jugador__nombre')[:max(limite, 1)]
        )
        return Response({
            'torneo': torneo.nombre,
            'nota': 'Solo cuenta los goles con anotador registrado; los autogoles no suman al jugador.',
            'goleadores': [
                {
                    'posicion': numero,
                    'jugador_id': fila['jugador_id'],
                    'jugador': fila['jugador__nombre'],
                    'numero_camiseta': fila['jugador__numero_camiseta'],
                    'equipo': fila['jugador__equipo__nombre'],
                    'goles': fila['goles'],
                    'penales': fila['penales'],
                    'partidos_con_gol': fila['partidos_con_gol'],
                }
                for numero, fila in enumerate(goleadores, start=1)
            ],
        })

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        torneo = self.get_object()
        resultados = Resultado.objects.filter(partido__torneo=torneo)

        # Consulta ORM: varias agregaciones condicionales en una sola consulta.
        totales = resultados.aggregate(
            partidos=Count('id'),
            goles=Sum(F('goles_local') + F('goles_visitante')),
            victorias_local=Count('id', filter=Q(goles_local__gt=F('goles_visitante'))),
            victorias_visitante=Count('id', filter=Q(goles_local__lt=F('goles_visitante'))),
            empates=Count('id', filter=Q(empate=True)),
        )
        partidos = totales['partidos']
        goles = totales['goles'] or 0

        mas_goles = (
            resultados.select_related('partido__equipo_local', 'partido__equipo_visitante')
            .annotate(total=F('goles_local') + F('goles_visitante'))
            .order_by('-total', 'partido__fecha').first()
        )
        tabla = tabla_ordenada(torneo)
        mas_goleador = tabla.order_by('-goles_a_favor', 'equipo__nombre').first()
        menos_goleado = tabla.order_by('goles_en_contra', 'equipo__nombre').first()
        goleador = (
            Anotador.objects.filter(resultado__partido__torneo=torneo).exclude(tipo=Anotador.Tipo.AUTOGOL)
            .values('jugador__nombre', 'jugador__equipo__nombre')
            .annotate(goles=Count('id')).order_by('-goles', 'jugador__nombre').first()
        )

        return Response({
            **self.ficha(torneo),
            'goles_totales': goles,
            'promedio_goles_por_partido': round(goles / partidos, 2) if partidos else 0.0,
            'victorias_local': totales['victorias_local'],
            'victorias_visitante': totales['victorias_visitante'],
            'empates': totales['empates'],
            'porcentaje_victorias_local': porcentaje(totales['victorias_local'], partidos),
            'porcentaje_victorias_visitante': porcentaje(totales['victorias_visitante'], partidos),
            'porcentaje_empates': porcentaje(totales['empates'], partidos),
            'partido_con_mas_goles': str(mas_goles) if mas_goles else None,
            'equipo_mas_goleador': (
                {'equipo': mas_goleador.equipo.nombre, 'goles': mas_goleador.goles_a_favor}
                if mas_goleador else None
            ),
            'valla_menos_vencida': (
                {'equipo': menos_goleado.equipo.nombre, 'goles_en_contra': menos_goleado.goles_en_contra}
                if menos_goleado else None
            ),
            'maximo_goleador': (
                {'jugador': goleador['jugador__nombre'], 'equipo': goleador['jugador__equipo__nombre'],
                 'goles': goleador['goles']}
                if goleador else None
            ),
        })
