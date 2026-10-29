from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Equipo(models.Model):

    nombre = models.CharField(max_length=100, unique=True)
    entrenador = models.CharField(max_length=100, blank=True, default='')
    ciudad = models.CharField(max_length=100, blank=True, default='')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Jugador(models.Model):

    class Posicion(models.TextChoices):
        PORTERO = 'POR', 'Portero'
        DEFENSA = 'DEF', 'Defensa'
        MEDIOCAMPISTA = 'MED', 'Mediocampista'
        DELANTERO = 'DEL', 'Delantero'

    nombre = models.CharField(max_length=100)
    identificacion = models.CharField('identificación', max_length=20, unique=True)
    numero_camiseta = models.PositiveSmallIntegerField('número de camiseta')
    posicion = models.CharField(
        'posición',
        max_length=3,
        choices=Posicion.choices,
        default=Posicion.MEDIOCAMPISTA,
    )

    # CASCADE: un jugador no existe sin su equipo. Si el jugador ya tiene
    # goles registrados, Anotador.jugador (PROTECT) impide el borrado -> 409.
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name='jugadores',
    )

    class Meta:
        ordering = ['equipo__nombre', 'numero_camiseta']
        verbose_name = 'jugador'
        verbose_name_plural = 'jugadores'
        constraints = [
            models.UniqueConstraint(
                fields=['equipo', 'numero_camiseta'],
                name='camiseta_unica_por_equipo',
                violation_error_message='Ese número de camiseta ya lo usa otro jugador del equipo.',
            ),
            models.CheckConstraint(
                condition=Q(numero_camiseta__gte=1) & Q(numero_camiseta__lte=99),
                name='camiseta_entre_1_y_99',
                violation_error_message='El número de camiseta debe estar entre 1 y 99.',
            ),
        ]

    def clean(self):
        """Reglas del jugador (se aplican en el panel de administración)."""
        from .serializers import (
            equipo_en_torneo_en_curso,
            normalizar_identificacion,
            torneo_que_quedaria_sin_minimo,
        )

        errores = {}

        # Un jugador no puede estar en dos equipos: la identificación es única.
        if self.identificacion:
            self.identificacion = normalizar_identificacion(self.identificacion)
            if len(self.identificacion) < 5:
                errores['identificacion'] = 'La identificación debe tener al menos 5 caracteres.'
            else:
                otro = (Jugador.objects.select_related('equipo')
                        .filter(identificacion=self.identificacion).exclude(pk=self.pk).first())
                if otro:
                    errores['identificacion'] = (
                        f'Ya existe un jugador con esa identificación: {otro.nombre}, del equipo '
                        f'{otro.equipo.nombre}. Un jugador no puede estar en dos equipos.'
                    )

        if self.numero_camiseta is not None and not 1 <= self.numero_camiseta <= 99:
            errores['numero_camiseta'] = 'El número de camiseta debe estar entre 1 y 99.'

        if self.equipo_id:
            if self.pk is None:
                if equipo_en_torneo_en_curso(self.equipo_id):
                    errores['equipo'] = ('No se pueden agregar jugadores a un equipo que está '
                                         'jugando un torneo en curso.')
            else:
                anterior = Jugador.objects.filter(pk=self.pk).values_list('equipo_id', flat=True).first()
                if anterior and anterior != self.equipo_id:
                    if equipo_en_torneo_en_curso(anterior) or equipo_en_torneo_en_curso(self.equipo_id):
                        errores['equipo'] = ('No se puede cambiar de equipo a un jugador mientras alguno '
                                             'de los dos equipos juega un torneo en curso.')
                    else:
                        torneo = torneo_que_quedaria_sin_minimo(anterior)
                        if torneo:
                            errores['equipo'] = (
                                f'Su equipo actual quedaría con menos de {torneo.minimo_jugadores_por_equipo} '
                                f'jugadores, el mínimo del torneo "{torneo.nombre}".'
                            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        if self.identificacion:
            self.identificacion = ''.join(c for c in self.identificacion.upper() if c.isalnum())
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nombre} #{self.numero_camiseta} ({self.equipo.nombre})'
