from django.db import models

from torneos.models import Torneo


class Inscripcion(models.Model):
    """
    Inscripción de un EQUIPO en un torneo (relación N:M entre Torneo y Equipo).

    Los jugadores no se inscriben por separado: participan con el equipo
    al que pertenecen.
    """

    # CASCADE: si se borra un torneo (solo permitido en INSCRIPCIONES)
    # sus inscripciones desaparecen con él.
    torneo = models.ForeignKey(
        'torneos.Torneo',
        on_delete=models.CASCADE,
        related_name='inscripciones',
    )
    # PROTECT: no se puede borrar un equipo que tiene inscripciones.
    equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.PROTECT,
        related_name='inscripciones',
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['torneo', 'fecha_inscripcion']
        verbose_name = 'equipo inscrito'
        verbose_name_plural = 'equipos inscritos'
        constraints = [
            models.UniqueConstraint(
                fields=['torneo', 'equipo'],
                name='equipo_unico_por_torneo',
                violation_error_message='Este equipo ya está inscrito en el torneo.',
            ),
        ]

    def __str__(self):
        return f'{self.equipo} en {self.torneo}'


class InscripcionPorTorneo(Torneo):
    """
    Vista del torneo para el módulo de inscripciones (modelo proxy, sin tabla
    propia): en el admin se listan los torneos creados y, al entrar a uno,
    se marcan los equipos que se quieren inscribir.
    """

    class Meta:
        proxy = True
        verbose_name = 'inscribir equipos en torneo'
        verbose_name_plural = 'inscribir equipos (por torneo)'
