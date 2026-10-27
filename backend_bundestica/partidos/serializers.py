from rest_framework import serializers
from .models import Partido, Gol


class GolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gol
        fields = '__all__'
        extra_kwargs = {
            'torneo': {'required': False}
        }

    def validate(self, attrs):
        partido = attrs.get('partido', getattr(self.instance, 'partido', None))
        jugador = attrs.get('jugador', getattr(self.instance, 'jugador', None))
        equipo = attrs.get('equipo', getattr(self.instance, 'equipo', None))

        if partido:
            if partido.torneo.cerrado:
                raise serializers.ValidationError('El torneo esta cerrado.')
            if partido.estado != 'EN_JUEGO':
                raise serializers.ValidationError(
                    f"No se pueden registrar goles en partidos '{partido.estado}'. Debe estar 'EN_JUEGO'."
                )
            if not equipo and jugador:
                equipo = jugador.equipo
                attrs['equipo'] = equipo

            if equipo and equipo.id not in [partido.equipo_casa_id, partido.equipo_visita_id]:
                raise serializers.ValidationError({'equipo': 'El equipo no juega en este partido.'})

            if jugador and equipo and jugador.equipo_id != equipo.id:
                raise serializers.ValidationError({'jugador': 'El jugador no pertenece a este equipo.'})

        return attrs


class PartidoSerializer(serializers.ModelSerializer):
    goles = GolSerializer(many=True, read_only=True)

    class Meta:
        model = Partido
        fields = '__all__'

    def validate(self, attrs):
        torneo = attrs.get('torneo', getattr(self.instance, 'torneo', None))
        casa = attrs.get('equipo_casa', getattr(self.instance, 'equipo_casa', None))
        visita = attrs.get('equipo_visita', getattr(self.instance, 'equipo_visita', None))

        if torneo and torneo.cerrado:
            raise serializers.ValidationError('No se pueden modificar partidos en un torneo cerrado.')

        if casa and visita and casa.id == visita.id:
            raise serializers.ValidationError('El equipo de casa y visita deben ser distintos.')

        return attrs