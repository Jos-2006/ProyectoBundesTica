from rest_framework import serializers

from backend_bundestica.campos import RelacionConOpciones
from equipos.models import Jugador
from torneos.models import Torneo

from . import servicios
from .models import Anotador, Partido, Resultado


def equipo_basico(equipo):
    return {'id': equipo.id, 'nombre': equipo.nombre} if equipo else None


# --------------------------------------------------------------------------- #
# Partidos
# --------------------------------------------------------------------------- #
class PartidoSerializer(serializers.ModelSerializer):
    """
    POST /api/partidos/
    { "torneo": 1, "equipo_local": 2, "equipo_visitante": 5, "fecha": "2026-11-07" }
    """

    # En el formulario solo aparecen torneos donde se pueden programar partidos.
    torneo = RelacionConOpciones(
        queryset=Torneo.objects.all(),
        opciones=Torneo.objects.filter(estado=Torneo.Estado.EN_CURSO),
    )
    nombre_torneo = serializers.CharField(source='torneo.nombre', read_only=True)
    nombre_local = serializers.CharField(source='equipo_local.nombre', read_only=True)
    nombre_visitante = serializers.CharField(source='equipo_visitante.nombre', read_only=True)
    marcador = serializers.SerializerMethodField()
    resultado = serializers.SerializerMethodField()
    ganador = serializers.SerializerMethodField()
    perdedor = serializers.SerializerMethodField()

    class Meta:
        model = Partido
        fields = [
            'id', 'torneo', 'nombre_torneo', 'fecha', 'estado',
            'equipo_local', 'nombre_local', 'equipo_visitante', 'nombre_visitante',
            'marcador', 'resultado', 'ganador', 'perdedor',
        ]
        read_only_fields = ['estado']
        validators = []     # las reglas de enfrentamiento se validan en validate()

    def obtener_resultado(self, partido):
        return getattr(partido, 'resultado', None) if partido.estado == Partido.Estado.FINALIZADO else None

    def get_marcador(self, partido):
        r = self.obtener_resultado(partido)
        return f'{r.goles_local} - {r.goles_visitante}' if r else None

    def get_resultado(self, partido):
        r = self.obtener_resultado(partido)
        return r.descripcion if r else 'Pendiente'

    def get_ganador(self, partido):
        r = self.obtener_resultado(partido)
        return equipo_basico(r.ganador) if r else None

    def get_perdedor(self, partido):
        r = self.obtener_resultado(partido)
        return equipo_basico(r.perdedor) if r else None

    def validate(self, datos):
        actual = self.instance
        if actual is not None:
            servicios.exigir_sin_resultado(actual, 'modificar')
            if 'torneo' in datos and datos['torneo'].pk != actual.torneo_id:
                raise serializers.ValidationError({'torneo': 'Un partido no se puede mover a otro torneo.'})

        def valor(campo):
            return datos.get(campo, getattr(actual, campo, None))

        servicios.validar_partido(
            valor('torneo'), valor('equipo_local'), valor('equipo_visitante'), valor('fecha'),
            partido_actual=actual,
        )
        return datos


# --------------------------------------------------------------------------- #
# Goles: resultado de un partido
# --------------------------------------------------------------------------- #
class AnotadorSerializer(serializers.ModelSerializer):

    jugador = serializers.PrimaryKeyRelatedField(queryset=Jugador.objects.select_related('equipo'))
    nombre_jugador = serializers.CharField(source='jugador.nombre', read_only=True)
    numero_camiseta = serializers.IntegerField(source='jugador.numero_camiseta', read_only=True)
    equipo = serializers.CharField(source='equipo.nombre', read_only=True)

    class Meta:
        model = Anotador
        fields = ['jugador', 'nombre_jugador', 'numero_camiseta', 'equipo', 'minuto', 'tipo']


class ResultadoSerializer(serializers.ModelSerializer):
    """
    POST /api/goles/
    {
      "partido": 3,
      "goles_local": 2,
      "goles_visitante": 1,
      "anotadores": [                         <- opcional
        {"jugador": 7,  "minuto": 15},
        {"jugador": 7,  "minuto": 60, "tipo": "PENAL"},
        {"jugador": 21, "minuto": 88}
      ]
    }
    """

    # En el formulario solo aparecen partidos que todavía no tienen resultado.
    partido = RelacionConOpciones(
        queryset=Partido.objects.select_related('torneo', 'equipo_local', 'equipo_visitante'),
        opciones=Partido.objects.filter(
            estado=Partido.Estado.PROGRAMADO, torneo__estado=Torneo.Estado.EN_CURSO,
        ).select_related('equipo_local', 'equipo_visitante'),
    )
    goles_local = serializers.IntegerField(min_value=0, max_value=servicios.MAXIMO_GOLES)
    goles_visitante = serializers.IntegerField(min_value=0, max_value=servicios.MAXIMO_GOLES)
    anotadores = AnotadorSerializer(many=True, required=False)

    torneo = serializers.CharField(source='partido.torneo.nombre', read_only=True)
    fecha = serializers.DateField(source='partido.fecha', read_only=True)
    equipo_local = serializers.CharField(source='partido.equipo_local.nombre', read_only=True)
    equipo_visitante = serializers.CharField(source='partido.equipo_visitante.nombre', read_only=True)
    marcador = serializers.SerializerMethodField()
    resultado = serializers.CharField(source='descripcion', read_only=True)
    ganador = serializers.SerializerMethodField()
    perdedor = serializers.SerializerMethodField()

    class Meta:
        model = Resultado
        fields = [
            'id', 'partido', 'torneo', 'fecha', 'equipo_local', 'equipo_visitante',
            'goles_local', 'goles_visitante', 'marcador', 'resultado', 'empate',
            'ganador', 'perdedor', 'anotadores', 'fecha_registro',
        ]
        read_only_fields = ['empate', 'fecha_registro']

    def get_marcador(self, r):
        return (f'{r.partido.equipo_local.nombre} {r.goles_local} - '
                f'{r.goles_visitante} {r.partido.equipo_visitante.nombre}')

    def get_ganador(self, r):
        return equipo_basico(r.ganador)

    def get_perdedor(self, r):
        return equipo_basico(r.perdedor)

    def get_fields(self):
        campos = super().get_fields()
        # Al corregir un resultado el partido ya tiene marcador: no se puede cambiar de partido.
        if self.instance is not None:
            campos['partido'] = serializers.PrimaryKeyRelatedField(read_only=True)
        return campos

    def create(self, datos):
        resultado, campeon = servicios.registrar_resultado(
            datos['partido'].pk, datos['goles_local'], datos['goles_visitante'], datos.get('anotadores'),
        )
        self.context['campeon'] = campeon
        return resultado

    def update(self, resultado, datos):
        return servicios.corregir_resultado(
            resultado,
            datos.get('goles_local', resultado.goles_local),
            datos.get('goles_visitante', resultado.goles_visitante),
            datos.get('anotadores'),
        )
