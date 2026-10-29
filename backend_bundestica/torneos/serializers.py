from django.db.models import Count
from rest_framework import serializers

from .models import Torneo


class TorneoSerializer(serializers.ModelSerializer):

    estado_nombre = serializers.CharField(source='get_estado_display', read_only=True)
    nombre_campeon = serializers.CharField(source='campeon.nombre', read_only=True, default=None)

    # Valores anotados en la consulta (ver TorneoViewSet.get_queryset).
    equipos_inscritos = serializers.IntegerField(read_only=True, default=0)
    partidos_jugados = serializers.IntegerField(read_only=True, default=0)

    cupos_disponibles = serializers.SerializerMethodField()
    partidos_restantes = serializers.SerializerMethodField()
    partidos_si_se_llena = serializers.SerializerMethodField()
    vueltas_nombre = serializers.CharField(source='get_vueltas_display', read_only=True)

    class Meta:
        model = Torneo
        fields = [
            'id', 'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'maximo_equipos', 'minimo_jugadores_por_equipo', 'vueltas', 'vueltas_nombre',
            'puntos_victoria', 'puntos_empate',
            'puntos_derrota', 'estado', 'estado_nombre',
            'equipos_inscritos', 'cupos_disponibles',
            'cantidad_partidos', 'partidos_jugados', 'partidos_restantes',
            'partidos_si_se_llena', 'campeon', 'nombre_campeon',
            'fecha_creacion',
        ]
        read_only_fields = ['estado', 'cantidad_partidos', 'campeon', 'fecha_creacion']

    def get_cupos_disponibles(self, torneo):
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            return 0
        return max(torneo.maximo_equipos - (getattr(torneo, 'equipos_inscritos', 0) or 0), 0)

    def get_partidos_restantes(self, torneo):
        return max(torneo.cantidad_partidos - (getattr(torneo, 'partidos_jugados', 0) or 0), 0)

    def get_partidos_si_se_llena(self, torneo):
        """Partidos que tendrá el torneo con el cupo lleno (todos contra todos x vueltas)."""
        return Torneo.partidos_para(torneo.maximo_equipos, torneo.vueltas)

    # ------------------------------------------------------------------ #
    # Validaciones de campo
    # ------------------------------------------------------------------ #
    def validate_nombre(self, valor):
        valor = valor.strip()
        repetidos = Torneo.objects.filter(nombre__iexact=valor)
        if self.instance:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError('Ya existe un torneo con ese nombre.')
        return valor

    def validate_maximo_equipos(self, valor):
        if not 2 <= valor <= 20:
            raise serializers.ValidationError('El máximo de equipos debe estar entre 2 y 20.')
        return valor

    def validate_minimo_jugadores_por_equipo(self, valor):
        if not 1 <= valor <= 30:
            raise serializers.ValidationError('El mínimo de jugadores debe estar entre 1 y 30.')
        return valor

    # ------------------------------------------------------------------ #
    # Validaciones combinadas (se aplican igual en POST, PUT y PATCH)
    # ------------------------------------------------------------------ #
    def validate(self, datos):

        def valor(campo, por_defecto=None):
            if campo in datos:
                return datos[campo]
            if self.instance is not None:
                return getattr(self.instance, campo)
            return por_defecto

        if self.instance and self.instance.estado != Torneo.Estado.INSCRIPCIONES:
            raise serializers.ValidationError(
                'Solo se puede modificar un torneo mientras tiene las inscripciones abiertas.'
            )

        fecha_inicio = valor('fecha_inicio')
        fecha_fin = valor('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha final no puede ser anterior a la fecha de inicio.'}
            )

        victoria = valor('puntos_victoria', 3)
        empate = valor('puntos_empate', 1)
        derrota = valor('puntos_derrota', 0)
        if not victoria > empate >= derrota:
            raise serializers.ValidationError(
                'Los puntos deben cumplir: victoria > empate >= derrota.'
            )

        maximo = valor('maximo_equipos', 8)
        if self.instance:
            inscritos = self.instance.inscripciones.count()
            if maximo < inscritos:
                raise serializers.ValidationError(
                    {'maximo_equipos': f'Ya hay {inscritos} equipos inscritos; '
                                       'el máximo no puede ser menor.'}
                )

            minimo = valor('minimo_jugadores_por_equipo')
            cortos = [
                i.equipo.nombre
                for i in self.instance.inscripciones.select_related('equipo')
                .annotate(cantidad=Count('equipo__jugadores'))
                if i.cantidad < minimo
            ]
            if cortos:
                raise serializers.ValidationError(
                    {'minimo_jugadores_por_equipo': 'Equipos ya inscritos quedarían por debajo del '
                                                    f'mínimo: {", ".join(cortos)}.'}
                )

        return datos
