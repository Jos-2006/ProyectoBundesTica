from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Torneo(models.Model):
    """
    Torneo de liga (todos contra todos).

    Ciclo de vida:
        INSCRIPCIONES -> (se llena el cupo, o POST /torneos/{id}/iniciar/) -> EN_CURSO
        EN_CURSO      -> (todos se enfrentaron 1 o 2 veces) -> FINALIZADO + campeón
    """

    class Estado(models.TextChoices):
        INSCRIPCIONES = 'INSCRIPCIONES', 'Inscripciones abiertas'
        EN_CURSO = 'EN_CURSO', 'En curso'
        FINALIZADO = 'FINALIZADO', 'Finalizado'

    class Vueltas(models.IntegerChoices):
        SOLO_IDA = 1, 'Solo ida'
        IDA_Y_VUELTA = 2, 'Ida y vuelta'

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField('descripción', blank=True, default='')

    fecha_inicio = models.DateField('fecha de inicio')
    fecha_fin = models.DateField('fecha final')

    # Máximo de inscripciones (equipos) permitidas en el torneo.
    maximo_equipos = models.PositiveSmallIntegerField('máximo de equipos', default=8)
    # Jugadores mínimos que debe tener un equipo para poder inscribirse.
    minimo_jugadores_por_equipo = models.PositiveSmallIntegerField('mínimo de jugadores por equipo', default=5)

    # 1 = cada pareja juega una vez; 2 = ida y vuelta.
    vueltas = models.PositiveSmallIntegerField(
        choices=Vueltas.choices,
        default=Vueltas.SOLO_IDA,
    )

    puntos_victoria = models.PositiveSmallIntegerField('puntos por victoria', default=3)
    puntos_empate = models.PositiveSmallIntegerField('puntos por empate', default=1)
    puntos_derrota = models.PositiveSmallIntegerField('puntos por derrota', default=0)

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.INSCRIPCIONES,
    )

    # Se fija al pasar a EN_CURSO: n(n-1)/2 x vueltas. El torneo termina
    # cuando se registran los resultados de todos estos partidos.
    cantidad_partidos = models.PositiveIntegerField('partidos a jugar', default=0)

    campeon = models.ForeignKey(
        'equipos.Equipo',
        verbose_name='campeón',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='campeonatos',
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_inicio', 'nombre']
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_fin__gte=F('fecha_inicio')),
                name='torneo_fecha_fin_posterior',
                violation_error_message='La fecha final no puede ser anterior a la fecha de inicio.',
            ),
            models.CheckConstraint(
                condition=Q(maximo_equipos__gte=2) & Q(maximo_equipos__lte=20),
                name='torneo_maximo_equipos_2_a_20',
                violation_error_message='El máximo de equipos debe estar entre 2 y 20.',
            ),
        ]

    @staticmethod
    def partidos_para(cantidad_equipos, vueltas):
        """Partidos de una liga todos contra todos: n(n-1)/2 por vuelta."""
        return cantidad_equipos * (cantidad_equipos - 1) // 2 * vueltas

    def clean(self):
        """Reglas del torneo (se aplican en el panel de administración)."""
        from django.db.models import Count

        errores = {}
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            errores['fecha_fin'] = 'La fecha final no puede ser anterior a la fecha de inicio.'
        if self.maximo_equipos is not None and not 2 <= self.maximo_equipos <= 20:
            errores['maximo_equipos'] = 'El máximo de equipos debe estar entre 2 y 20.'
        if self.minimo_jugadores_por_equipo is not None and not 1 <= self.minimo_jugadores_por_equipo <= 30:
            errores['minimo_jugadores_por_equipo'] = 'El mínimo de jugadores debe estar entre 1 y 30.'
        if None not in (self.puntos_victoria, self.puntos_empate, self.puntos_derrota):
            if not self.puntos_victoria > self.puntos_empate >= self.puntos_derrota:
                errores['puntos_empate'] = 'Los puntos deben cumplir: victoria > empate >= derrota.'

        if self.pk:
            anterior = Torneo.objects.filter(pk=self.pk).values_list('estado', flat=True).first()
            if anterior and anterior != self.Estado.INSCRIPCIONES:
                raise ValidationError('Solo se puede modificar un torneo mientras tiene las inscripciones abiertas.')

            inscripciones = self.inscripciones.select_related('equipo').annotate(cantidad=Count('equipo__jugadores'))
            if self.maximo_equipos is not None and self.maximo_equipos < len(inscripciones):
                errores['maximo_equipos'] = (f'Ya hay {len(inscripciones)} equipos inscritos; '
                                             'el máximo no puede ser menor.')
            if self.minimo_jugadores_por_equipo:
                cortos = [i.equipo.nombre for i in inscripciones if i.cantidad < self.minimo_jugadores_por_equipo]
                if cortos:
                    errores['minimo_jugadores_por_equipo'] = (
                        'Equipos ya inscritos quedarían por debajo del mínimo: ' + ', '.join(cortos) + '.'
                    )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return self.nombre
