from django.db import models
from torneos.models import Torneo
from equipos.models import Equipo, Jugador

class TorneoEquipo(models.Model):
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('torneo', 'equipo')

class TorneoJugador(models.Model):
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('torneo', 'jugador')