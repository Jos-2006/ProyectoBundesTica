from rest_framework import serializers
from .models import TorneoEquipo, TorneoJugador


class TorneoEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TorneoEquipo
        fields = '__all__'

    def validate(self, attrs):
        torneo = attrs.get('torneo', getattr(self.instance, 'torneo', None))
        if torneo and torneo.cerrado:
            raise serializers.ValidationError('No se pueden inscribir equipos en un torneo cerrado.')
        return attrs


class TorneoJugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TorneoJugador
        fields = '__all__'

    def validate(self, attrs):
        torneo = attrs.get('torneo', getattr(self.instance, 'torneo', None))
        equipo = attrs.get('equipo', getattr(self.instance, 'equipo', None))
        jugador = attrs.get('jugador', getattr(self.instance, 'jugador', None))

        if torneo and torneo.cerrado:
            raise serializers.ValidationError('No se pueden inscribir jugadores en un torneo cerrado.')

        if not TorneoEquipo.objects.filter(torneo=torneo, equipo=equipo).exists():
            raise serializers.ValidationError({'equipo': 'El equipo no esta inscrito en este torneo.'})

        if jugador and jugador.equipo_id != equipo.id:
            raise serializers.ValidationError({'jugador': 'El jugador no pertenece a la plantilla de este equipo.'})

        qs = TorneoJugador.objects.filter(torneo=torneo, jugador=jugador)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({'jugador': 'El jugador ya esta inscrito en este torneo con otro equipo.'})

        return attrs