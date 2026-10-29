from django.db import models
from django.db.models import F, Q


class Partido(models.Model):
    """
    Enfrentamiento entre dos equipos inscritos en un torneo.
    Lo crea el usuario indicando quién juega contra quién y la fecha.

        PROGRAMADO  -> todavía no tiene resultado.
        FINALIZADO  -> ya se registró el marcador (ver Resultado / "goles").
    """

    class Estado(models.TextChoices):
        PROGRAMADO = 'PROGRAMADO', 'Programado'
        FINALIZADO = 'FINALIZADO', 'Finalizado'

    torneo = models.ForeignKey(
        'torneos.Torneo',
        on_delete=models.PROTECT,
        related_name='partidos',
    )
    equipo_local = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.PROTECT,
        related_name='partidos_como_local',
    )
    equipo_visitante = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.PROTECT,
        related_name='partidos_como_visitante',
    )
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROGRAMADO)

    class Meta:
        ordering = ['torneo', 'fecha', 'id']
        constraints = [
            # Un equipo nunca juega contra sí mismo.
            models.CheckConstraint(
                condition=~Q(equipo_local=F('equipo_visitante')),
                name='partido_equipos_distintos',
                violation_error_message='Un equipo no puede enfrentarse a sí mismo.',
            ),
            # La misma localía no se repite en un torneo
            # (en ida y vuelta, A-B y B-A son partidos distintos).
            models.UniqueConstraint(
                fields=['torneo', 'equipo_local', 'equipo_visitante'],
                name='partido_unico_por_localia',
                violation_error_message='Ese enfrentamiento (con esa misma localía) ya existe en el torneo.',
            ),
        ]

    def __str__(self):
        return f'{self.equipo_local} vs {self.equipo_visitante} ({self.fecha})'


class Resultado(models.Model):
    """
    Marcador final de un partido (módulo "goles").

    El usuario indica cuántos goles hizo cada equipo y el sistema decide
    quién ganó, quién perdió o si quedaron empatados.
    """

    partido = models.OneToOneField(Partido, on_delete=models.CASCADE, related_name='resultado')
    goles_local = models.PositiveSmallIntegerField()
    goles_visitante = models.PositiveSmallIntegerField()

    # Se calculan solos a partir del marcador.
    ganador = models.ForeignKey(
        'equipos.Equipo', on_delete=models.PROTECT, null=True, blank=True,
        related_name='partidos_ganados',
    )
    perdedor = models.ForeignKey(
        'equipos.Equipo', on_delete=models.PROTECT, null=True, blank=True,
        related_name='partidos_perdidos',
    )
    empate = models.BooleanField(default=False)

    fecha_registro = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-partido__fecha', '-id']
        verbose_name = 'gol (resultado del partido)'
        verbose_name_plural = 'goles (resultados de partidos)'
        constraints = [
            models.CheckConstraint(
                condition=Q(goles_local__lte=50) & Q(goles_visitante__lte=50),
                name='resultado_goles_maximo_50',
                violation_error_message='Cada equipo puede tener como máximo 50 goles.',
            ),
        ]

    @property
    def descripcion(self):
        if self.empate:
            return 'Empatado'
        return f'Ganó {self.ganador.nombre}'

    def __str__(self):
        p = self.partido
        return f'{p.equipo_local} {self.goles_local} - {self.goles_visitante} {p.equipo_visitante}'


class Anotador(models.Model):
    """
    Detalle opcional de un gol: qué jugador lo hizo y en qué minuto.
    `equipo` es el equipo al que se le suma (en un AUTOGOL, el rival).
    """

    class Tipo(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        PENAL = 'PENAL', 'Penal'
        AUTOGOL = 'AUTOGOL', 'Autogol'

    resultado = models.ForeignKey(Resultado, on_delete=models.CASCADE, related_name='anotadores')
    jugador = models.ForeignKey('equipos.Jugador', on_delete=models.PROTECT, related_name='goles')
    equipo = models.ForeignKey('equipos.Equipo', on_delete=models.PROTECT, related_name='goles_a_favor')
    minuto = models.PositiveSmallIntegerField()
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.NORMAL)

    class Meta:
        ordering = ['resultado', 'minuto', 'id']
        verbose_name = 'goleador'
        verbose_name_plural = 'goleadores (opcional)'
        constraints = [
            models.CheckConstraint(
                condition=Q(minuto__gte=1) & Q(minuto__lte=130),
                name='anotador_minuto_1_a_130',
                violation_error_message='El minuto debe estar entre 1 y 130.',
            ),
        ]

    def __str__(self):
        return f"{self.jugador.nombre} {self.minuto}'"
