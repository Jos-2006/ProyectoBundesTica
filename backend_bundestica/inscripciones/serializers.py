from rest_framework import serializers

from django.db.models import Count, F

from backend_bundestica.campos import RelacionConOpciones
from equipos.serializers import JugadorResumenSerializer
from torneos.models import Torneo

from .models import Inscripcion


class InscripcionSerializer(serializers.ModelSerializer):
    """
    Solo se inscriben EQUIPOS. La respuesta muestra los jugadores con los
    que el equipo participa (solo lectura).
    """

    # En el formulario solo aparecen torneos con inscripciones abiertas y cupo.
    torneo = RelacionConOpciones(
        queryset=Torneo.objects.all(),
        opciones=Torneo.objects.annotate(inscritos=Count('inscripciones'))
        .filter(estado=Torneo.Estado.INSCRIPCIONES, inscritos__lt=F('maximo_equipos')),
    )
    nombre_torneo = serializers.CharField(source='torneo.nombre', read_only=True)
    estado_torneo = serializers.CharField(source='torneo.estado', read_only=True)
    nombre_equipo = serializers.CharField(source='equipo.nombre', read_only=True)
    jugadores = JugadorResumenSerializer(source='equipo.jugadores', many=True, read_only=True)

    class Meta:
        model = Inscripcion
        fields = [
            'id', 'torneo', 'nombre_torneo', 'estado_torneo', 'equipo', 'nombre_equipo',
            'fecha_inscripcion', 'jugadores',
        ]
        read_only_fields = ['fecha_inscripcion']
     
        validators = []

    def validate(self, datos):

        torneo = datos.get('torneo', getattr(self.instance, 'torneo', None))
        equipo = datos.get('equipo', getattr(self.instance, 'equipo', None))

        if self.instance and torneo.pk != self.instance.torneo_id:
            raise serializers.ValidationError(
                {'torneo': 'No se puede mover una inscripción a otro torneo; '
                           'elimínala y crea una nueva.'}
            )

        # Regla: solo se inscribe con inscripciones abiertas.
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            raise serializers.ValidationError(
                {'torneo': 'Las inscripciones de este torneo están cerradas.'}
            )

        otras = Inscripcion.objects.filter(torneo=torneo)
        if self.instance:
            otras = otras.exclude(pk=self.instance.pk)

        # Regla: un equipo no se inscribe dos veces en el mismo torneo.
        if otras.filter(equipo=equipo).exists():
            raise serializers.ValidationError(
                {'equipo': 'Este equipo ya está inscrito en el torneo.'}
            )

        # Regla: máximo de inscripciones por torneo.
        if self.instance is None and otras.count() >= torneo.maximo_equipos:
            raise serializers.ValidationError(
                {'torneo': f'El torneo ya alcanzó su máximo de {torneo.maximo_equipos} equipos.'}
            )

        # Regla: el equipo debe tener la plantilla mínima.
        cantidad = equipo.jugadores.count()
        if cantidad < torneo.minimo_jugadores_por_equipo:
            raise serializers.ValidationError(
                {'equipo': f'El equipo tiene {cantidad} jugador(es); el torneo exige al menos '
                           f'{torneo.minimo_jugadores_por_equipo}.'}
            )

        return datos
