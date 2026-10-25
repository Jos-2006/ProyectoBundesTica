from django.db import models

class Equipo(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
class Jugador(models.Model):
    nombre = models.CharField(max_length=100)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='jugadores')

    def __str__(self):
        return self.nombre