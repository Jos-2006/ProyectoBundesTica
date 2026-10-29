"""
Servicios del ciclo de vida de un torneo.

- poner_en_curso: se ejecuta solo cuando el torneo llena su cupo de equipos
  (o cuando el administrador lo inicia antes con al menos 2 equipos).
  Cierra inscripciones, fija cuántos partidos se deben jugar y crea la
  fila de la tabla de posiciones de cada equipo.
"""

from django.db import transaction
from django.db.models import Count
from rest_framework.exceptions import ValidationError

from backend_bundestica.excepciones import Conflicto
from estadisticas.models import Estadistica
from inscripciones.models import Inscripcion

from .models import Torneo


def poner_en_curso(torneo):
    """Debe llamarse dentro de una transacción con el torneo bloqueado."""

    inscripciones = list(
        Inscripcion.objects.filter(torneo=torneo)
        .select_related('equipo')
        .annotate(cantidad_jugadores=Count('equipo__jugadores'))
    )

    if len(inscripciones) < 2:
        raise ValidationError({'detail': 'Se necesitan al menos 2 equipos inscritos para iniciar el torneo.'})

    incompletos = [
        i.equipo.nombre for i in inscripciones
        if i.cantidad_jugadores < torneo.minimo_jugadores_por_equipo
    ]
    if incompletos:
        raise ValidationError({'detail':
            f'Estos equipos no tienen el mínimo de {torneo.minimo_jugadores_por_equipo} '
            f'jugadores: {", ".join(incompletos)}.'
        })

    Estadistica.objects.bulk_create(
        [Estadistica(torneo=torneo, equipo=i.equipo) for i in inscripciones]
    )

    torneo.estado = Torneo.Estado.EN_CURSO
    torneo.cantidad_partidos = Torneo.partidos_para(len(inscripciones), torneo.vueltas)
    torneo.save(update_fields=['estado', 'cantidad_partidos'])
    return torneo


@transaction.atomic
def iniciar_torneo(torneo_id):
    """Inicio manual (antes de llenar el cupo)."""
    torneo = Torneo.objects.select_for_update().get(pk=torneo_id)
    if torneo.estado != Torneo.Estado.INSCRIPCIONES:
        raise Conflicto('El torneo ya fue iniciado.')
    return poner_en_curso(torneo)


def enfrentamientos_pendientes(torneo):
    """
    Enfrentamientos que todavía no se han programado.
    Solo ida: cada pareja una vez. Ida y vuelta: cada pareja una vez en cada cancha.
    """
    from partidos.models import Partido

    equipos = list(
        Inscripcion.objects.filter(torneo=torneo)
        .select_related('equipo').order_by('equipo__nombre')
    )
    programados = set(
        Partido.objects.filter(torneo=torneo).values_list('equipo_local_id', 'equipo_visitante_id')
    )
    pendientes = []
    for i, a in enumerate(equipos):
        for b in equipos[i + 1:]:
            ida = (a.equipo_id, b.equipo_id)
            vuelta = (b.equipo_id, a.equipo_id)
            if torneo.vueltas == Torneo.Vueltas.SOLO_IDA:
                # Una sola vez, en cualquier cancha.
                if ida not in programados and vuelta not in programados:
                    pendientes.append((a.equipo, b.equipo))
            else:
                # Dos veces: cada equipo es local una vez.
                if ida not in programados:
                    pendientes.append((a.equipo, b.equipo))
                if vuelta not in programados:
                    pendientes.append((b.equipo, a.equipo))
    return pendientes
