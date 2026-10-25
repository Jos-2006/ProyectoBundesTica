from django.db import models
from torneos.models import Torneo
from equipos.models import Equipo

class Estadistica(models.Model):
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    pg = models.IntegerField(default=0)
    pp = models.IntegerField(default=0)
    pe = models.IntegerField(default=0)
    gf = models.IntegerField(default=0)
    gc = models.IntegerField(default=0)  
    pts = models.IntegerField(default=0) 

    class Meta:
        unique_together = ('torneo', 'equipo')

    def __str__(self):
        return f"{self.equipo} - {self.pts} pts"
