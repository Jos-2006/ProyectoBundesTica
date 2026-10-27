from rest_framework import serializers
from .models import Estadistica


class EstadisticaSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)

    class Meta:
        model = Estadistica
        fields = ['id', 'torneo', 'equipo', 'equipo_nombre', 'pj', 'pg', 'pe', 'pp', 'gf', 'gc', 'dg', 'pts']