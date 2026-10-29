from rest_framework import serializers

from torneos.models import Torneo
from inscripciones.models import Inscripcion

from .models import Equipo, Jugador


def normalizar_identificacion(valor):
    """'1-1111-1111', ' 111111111 ' y '1 1111 1111' son la misma persona."""
    return ''.join(caracter for caracter in str(valor).upper() if caracter.isalnum())


def torneo_que_quedaria_sin_minimo(equipo_id):
    """
    Si el equipo perdiera un jugador, ¿quedaría por debajo del mínimo de algún
    torneo con inscripciones abiertas en el que está inscrito? Devuelve ese torneo.
    """
    cantidad = Jugador.objects.filter(equipo_id=equipo_id).count()
    return (
        Torneo.objects.filter(
            inscripciones__equipo_id=equipo_id,
            estado=Torneo.Estado.INSCRIPCIONES,
            minimo_jugadores_por_equipo__gt=cantidad - 1,
        ).first()
    )


def equipo_en_torneo_en_curso(equipo_id):
    """True si el equipo está jugando un torneo que ya empezó y no ha terminado."""
    return Inscripcion.objects.filter(
        equipo_id=equipo_id,
        torneo__estado=Torneo.Estado.EN_CURSO,
    ).exists()


class JugadorSerializer(serializers.ModelSerializer):

    nombre_equipo = serializers.CharField(source='equipo.nombre', read_only=True)
    posicion_nombre = serializers.CharField(source='get_posicion_display', read_only=True)
    goles_totales = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Jugador
        fields = [
            'id', 'nombre', 'identificacion', 'numero_camiseta',
            'posicion', 'posicion_nombre', 'equipo', 'nombre_equipo',
            'goles_totales',
        ]
        # Las unicidades se validan a mano con mensajes claros.
        validators = []
        extra_kwargs = {'identificacion': {'validators': []}}

    def validate_identificacion(self, valor):
        valor = normalizar_identificacion(valor)
        if len(valor) < 5:
            raise serializers.ValidationError('La identificación debe tener al menos 5 caracteres.')
        # Regla: un jugador (misma identificación) no puede estar en dos equipos.
        existente = Jugador.objects.select_related('equipo').filter(identificacion=valor)
        if self.instance:
            existente = existente.exclude(pk=self.instance.pk)
        existente = existente.first()
        if existente:
            raise serializers.ValidationError(
                f'Ya existe un jugador con esa identificación: {existente.nombre}, del equipo '
                f'{existente.equipo.nombre}. Un jugador no puede estar en dos equipos.'
            )
        return valor

    def validate_numero_camiseta(self, valor):
        if not 1 <= valor <= 99:
            raise serializers.ValidationError('El número de camiseta debe estar entre 1 y 99.')
        return valor

    def validate(self, datos):

        equipo = datos.get('equipo', getattr(self.instance, 'equipo', None))
        numero = datos.get('numero_camiseta', getattr(self.instance, 'numero_camiseta', None))

        # Regla: número de camiseta único dentro del equipo (también en PATCH).
        repetidos = Jugador.objects.filter(equipo=equipo, numero_camiseta=numero)
        if self.instance:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError(
                {'numero_camiseta': 'Ese número ya lo usa otro jugador del equipo.'}
            )

        # Regla: la plantilla se congela mientras el equipo juega un torneo en curso.
        if self.instance is None:
            if equipo_en_torneo_en_curso(equipo.pk):
                raise serializers.ValidationError(
                    'No se pueden agregar jugadores a un equipo que está jugando '
                    'un torneo en curso.'
                )
        elif equipo.pk != self.instance.equipo_id:
            if (
                equipo_en_torneo_en_curso(self.instance.equipo_id)
                or equipo_en_torneo_en_curso(equipo.pk)
            ):
                raise serializers.ValidationError(
                    {'equipo': 'No se puede cambiar de equipo a un jugador mientras '
                               'alguno de los dos equipos juega un torneo en curso.'}
                )
            torneo = torneo_que_quedaria_sin_minimo(self.instance.equipo_id)
            if torneo:
                raise serializers.ValidationError(
                    {'equipo': f'Si este jugador se va, {self.instance.equipo.nombre} quedaría con menos '
                               f'de {torneo.minimo_jugadores_por_equipo} jugadores, el mínimo del '
                               f'torneo "{torneo.nombre}" en el que está inscrito.'}
                )

        return datos


class JugadorResumenSerializer(serializers.ModelSerializer):

    class Meta:
        model = Jugador
        fields = ['id', 'nombre', 'numero_camiseta', 'posicion']


class EquipoSerializer(serializers.ModelSerializer):

    jugadores = JugadorResumenSerializer(many=True, read_only=True)
    cantidad_jugadores = serializers.IntegerField(read_only=True, default=0)
    torneos_ganados = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Equipo
        fields = [
            'id', 'nombre', 'entrenador', 'ciudad', 'fecha_registro',
            'cantidad_jugadores', 'torneos_ganados', 'jugadores',
        ]
        read_only_fields = ['fecha_registro']

    def validate_nombre(self, valor):
        valor = valor.strip()
        if len(valor) < 3:
            raise serializers.ValidationError('El nombre debe tener al menos 3 caracteres.')
        repetidos = Equipo.objects.filter(nombre__iexact=valor)
        if self.instance:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError('Ya existe un equipo con ese nombre.')
        return valor
