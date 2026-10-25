from django.db import models
from torneos.models import Torneo
from equipos.models import Equipo, Jugador

class Partido(models.Model):
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    equipo_casa = models.ForeignKey(Equipo, related_name='partidos_casa', on_delete=models.CASCADE)
    equipo_visita = models.ForeignKey(Equipo, related_name='partidos_visita', on_delete=models.CASCADE)
    jornada = models.IntegerField()
    fecha = models.DateField()

    def __str__(self):
        return f"Jornada {self.jornada}: {self.equipo_casa} vs {self.equipo_visita}"

class Gol(models.Model):
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='goles')
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    minuto_juego = models.IntegerField()

    def __str__(self):
        return f"Gol al minuto {self.minuto_juego} - {self.jugador}"