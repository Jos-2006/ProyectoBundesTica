from django.db import models


class Estadistica(models.Model):
    """
    Fila de la tabla de posiciones de un equipo dentro de un torneo.

    No se edita a mano: se recalcula cada vez que se finaliza un partido
    (ver estadisticas/servicios.py).
    """

    torneo = models.ForeignKey(
        'torneos.Torneo',
        on_delete=models.CASCADE,
        related_name='estadisticas',
    )
    equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.PROTECT,
        related_name='estadisticas',
    )

    partidos_jugados = models.PositiveSmallIntegerField(default=0)
    partidos_ganados = models.PositiveSmallIntegerField(default=0)
    partidos_empatados = models.PositiveSmallIntegerField(default=0)
    partidos_perdidos = models.PositiveSmallIntegerField(default=0)
    goles_a_favor = models.PositiveSmallIntegerField(default=0)
    goles_en_contra = models.PositiveSmallIntegerField(default=0)
    diferencia_goles = models.SmallIntegerField(default=0)
    puntos = models.PositiveSmallIntegerField(default=0)

    # Criterio de desempate de la tabla.
    ORDEN_TABLA = [
        '-puntos', '-diferencia_goles', '-goles_a_favor',
        '-partidos_ganados', 'equipo__nombre',
    ]

    class Meta:
        ordering = ['torneo', '-puntos', '-diferencia_goles', '-goles_a_favor']
        verbose_name = 'posición en la tabla'
        verbose_name_plural = 'tablas de torneos finalizados'
        constraints = [
            models.UniqueConstraint(
                fields=['torneo', 'equipo'],
                name='estadistica_unica_por_equipo_y_torneo',
            ),
        ]

    def __str__(self):
        return f'{self.equipo} - {self.puntos} pts ({self.torneo})'
