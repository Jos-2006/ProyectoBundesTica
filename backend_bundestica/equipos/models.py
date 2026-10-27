from django.db import models


class Equipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Jugador(models.Model):
    nombre = models.CharField(max_length=100)
    identificacion = models.CharField(max_length=20, unique=True, null=True, blank=True)
    numero_camiseta = models.PositiveIntegerField(default=1)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='jugadores')

    def __str__(self):
        return f"{self.nombre} ({self.equipo.nombre})"