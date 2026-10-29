from rest_framework import serializers

from partidos.models import Resultado

from .models import Estadistica


def porcentaje(parte, total):
    return round(parte * 100 / total, 2) if total else 0.0


class FilaPosicionesSerializer(serializers.ModelSerializer):

    posicion = serializers.SerializerMethodField()
    equipo_id = serializers.IntegerField(source='equipo.id', read_only=True)
    equipo = serializers.CharField(source='equipo.nombre', read_only=True)
    porcentaje_victorias = serializers.SerializerMethodField()
    porcentaje_empates = serializers.SerializerMethodField()
    porcentaje_derrotas = serializers.SerializerMethodField()
    rendimiento = serializers.SerializerMethodField()
    promedio_goles_a_favor = serializers.SerializerMethodField()
    promedio_goles_en_contra = serializers.SerializerMethodField()

    class Meta:
        model = Estadistica
        fields = [
            'posicion', 'equipo_id', 'equipo',
            'partidos_jugados', 'partidos_ganados', 'partidos_empatados', 'partidos_perdidos',
            'goles_a_favor', 'goles_en_contra', 'diferencia_goles', 'puntos',
            'porcentaje_victorias', 'porcentaje_empates', 'porcentaje_derrotas',
            'rendimiento', 'promedio_goles_a_favor', 'promedio_goles_en_contra',
        ]

    def get_posicion(self, fila):
        return self.context['posiciones'][fila.pk]

    def get_porcentaje_victorias(self, fila):
        return porcentaje(fila.partidos_ganados, fila.partidos_jugados)

    def get_porcentaje_empates(self, fila):
        return porcentaje(fila.partidos_empatados, fila.partidos_jugados)

    def get_porcentaje_derrotas(self, fila):
        return porcentaje(fila.partidos_perdidos, fila.partidos_jugados)

    def get_rendimiento(self, fila):
        """% de los puntos posibles que el equipo obtuvo."""
        return porcentaje(fila.puntos, fila.partidos_jugados * fila.torneo.puntos_victoria)

    def get_promedio_goles_a_favor(self, fila):
        return round(fila.goles_a_favor / fila.partidos_jugados, 2) if fila.partidos_jugados else 0.0

    def get_promedio_goles_en_contra(self, fila):
        return round(fila.goles_en_contra / fila.partidos_jugados, 2) if fila.partidos_jugados else 0.0


class PartidoJugadoSerializer(serializers.ModelSerializer):
    """Estadística de un partido jugado en un torneo finalizado."""

    partido_id = serializers.IntegerField(source='partido.id', read_only=True)
    torneo = serializers.CharField(source='partido.torneo.nombre', read_only=True)
    fecha = serializers.DateField(source='partido.fecha', read_only=True)
    local = serializers.CharField(source='partido.equipo_local.nombre', read_only=True)
    visitante = serializers.CharField(source='partido.equipo_visitante.nombre', read_only=True)
    marcador = serializers.SerializerMethodField()
    resultado = serializers.CharField(source='descripcion', read_only=True)
    ganador = serializers.SerializerMethodField()
    perdedor = serializers.SerializerMethodField()
    total_goles = serializers.IntegerField(read_only=True)
    goleadores_local = serializers.SerializerMethodField()
    goleadores_visitante = serializers.SerializerMethodField()

    class Meta:
        model = Resultado
        fields = [
            'id', 'partido_id', 'torneo', 'fecha', 'local', 'visitante',
            'goles_local', 'goles_visitante', 'marcador', 'resultado', 'empate',
            'ganador', 'perdedor', 'total_goles', 'goleadores_local', 'goleadores_visitante',
        ]

    def get_marcador(self, r):
        return (f'{r.partido.equipo_local.nombre} {r.goles_local} - '
                f'{r.goles_visitante} {r.partido.equipo_visitante.nombre}')

    def get_ganador(self, r):
        return r.ganador.nombre if r.ganador else None

    def get_perdedor(self, r):
        return r.perdedor.nombre if r.perdedor else None

    def detalle(self, r, equipo_id):
        return [
            {'minuto': a.minuto, 'jugador': a.jugador.nombre,
             'numero_camiseta': a.jugador.numero_camiseta, 'tipo': a.tipo}
            for a in r.anotadores.all()          # viene de prefetch_related
            if a.equipo_id == equipo_id
        ]

    def get_goleadores_local(self, r):
        return self.detalle(r, r.partido.equipo_local_id)

    def get_goleadores_visitante(self, r):
        return self.detalle(r, r.partido.equipo_visitante_id)
