from django.db import models

class Torneo(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    puntos_victoria = models.IntegerField(default=3)
    puntos_empate = models.IntegerField(default=1)

    def __str__(self):
        return self.nombre