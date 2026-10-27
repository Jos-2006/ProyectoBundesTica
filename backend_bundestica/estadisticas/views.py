from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from .models import Estadistica
from .serializers import EstadisticaSerializer
from partidos.models import Gol


class TablaPosicionesView(APIView):
    def get(self, request, torneo_id):
        tabla = Estadistica.objects.filter(torneo_id=torneo_id).order_by('-pts', '-dg', '-gf')
        serializer = EstadisticaSerializer(tabla, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TablaGoleadoresView(APIView):
    def get(self, request, torneo_id):
        goleadores = (
            Gol.objects.filter(torneo_id=torneo_id)
            .values('jugador__id', 'jugador__nombre', 'equipo__nombre')
            .annotate(total_goles=Count('id'))
            .order_by('-total_goles')
        )
        data = [
            {
                'jugador_id': g['jugador__id'],
                'jugador': g['jugador__nombre'],
                'equipo': g['equipo__nombre'],
                'goles': g['total_goles'],
            }
            for g in goleadores
        ]
        return Response(data, status=status.HTTP_200_OK)