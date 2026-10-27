from rest_framework import serializers
from .models import Torneo


class TorneoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Torneo
        fields = '__all__'