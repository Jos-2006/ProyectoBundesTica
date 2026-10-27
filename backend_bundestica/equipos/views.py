from rest_framework import viewsets
from .models import Equipo, Jugador
from .serializers import EquipoSerializer, JugadorSerializer
from backend_bundestica.permissions import EsAdminLiga, EsConsultaOReadOnly


class EquipoViewSet(viewsets.ModelViewSet):
    queryset = Equipo.objects.all()
    serializer_class = EquipoSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [EsConsultaOReadOnly()]
        return [EsAdminLiga()]


class JugadorViewSet(viewsets.ModelViewSet):
    queryset = Jugador.objects.all()
    serializer_class = JugadorSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [EsConsultaOReadOnly()]
        return [EsAdminLiga()]