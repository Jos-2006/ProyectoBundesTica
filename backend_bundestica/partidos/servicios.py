"""
Reglas de negocio de partidos y goles (marcadores).

Partidos
    - Solo en torneos EN_CURSO.
    - Solo entre equipos inscritos en ese torneo, y nunca un equipo contra sí mismo.
    - Solo ida: cada pareja se enfrenta UNA vez.
      Ida y vuelta: cada pareja se enfrenta DOS veces, una en cada cancha.
    - La fecha debe estar dentro de las fechas del torneo.

Goles (resultado)
    - Se elige un partido y se indican los goles de cada equipo.
    - El sistema decide ganador / perdedor o "Empatado".
    - Al registrarse el último resultado el torneo pasa a FINALIZADO y se
      asigna el campeón (primer lugar de la tabla).
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from backend_bundestica.excepciones import Conflicto
from estadisticas.servicios import recalcular_tabla, tabla_ordenada
from inscripciones.models import Inscripcion
from torneos.models import Torneo

from .models import Anotador, Partido, Resultado


MAXIMO_GOLES = 50
MINUTO_MINIMO, MINUTO_MAXIMO = 1, 130


# --------------------------------------------------------------------------- #
# Partidos
# --------------------------------------------------------------------------- #
def validar_partido(torneo, local, visitante, fecha, partido_actual=None):

    if torneo.estado != Torneo.Estado.EN_CURSO:
        if torneo.estado == Torneo.Estado.INSCRIPCIONES:
            raise ValidationError(
                {'torneo': 'El torneo todavía tiene inscripciones abiertas. Los partidos se '
                           'programan cuando el torneo está EN_CURSO (al llenarse el cupo).'}
            )
        raise ValidationError({'torneo': 'El torneo ya finalizó; no se pueden programar partidos.'})

    if local.pk == visitante.pk:
        raise ValidationError({'equipo_visitante': 'Un equipo no puede enfrentarse a sí mismo.'})

    inscritos = set(
        Inscripcion.objects.filter(torneo=torneo, equipo__in=[local, visitante])
        .values_list('equipo_id', flat=True)
    )
    for campo, equipo in (('equipo_local', local), ('equipo_visitante', visitante)):
        if equipo.pk not in inscritos:
            raise ValidationError({campo: f'{equipo.nombre} no está inscrito en el torneo {torneo.nombre}.'})

    if not torneo.fecha_inicio <= fecha <= torneo.fecha_fin:
        raise ValidationError(
            {'fecha': f'La fecha debe estar entre {torneo.fecha_inicio} y {torneo.fecha_fin}.'}
        )

    otros = Partido.objects.filter(torneo=torneo)
    if partido_actual is not None:
        otros = otros.exclude(pk=partido_actual.pk)

    misma_localia = otros.filter(equipo_local=local, equipo_visitante=visitante).exists()
    localia_inversa = otros.filter(equipo_local=visitante, equipo_visitante=local).exists()

    if torneo.vueltas == Torneo.Vueltas.SOLO_IDA:
        if misma_localia or localia_inversa:
            raise ValidationError(
                f'{local.nombre} y {visitante.nombre} ya tienen su partido en este torneo '
                '(torneo de solo ida: se enfrentan una sola vez).'
            )
    elif misma_localia:
        sugerencia = '' if localia_inversa else (
            f' Falta el partido de vuelta: {visitante.nombre} (local) vs {local.nombre}.'
        )
        raise ValidationError(
            f'{local.nombre} ya recibió a {visitante.nombre} en este torneo.{sugerencia}'
        )


def exigir_sin_resultado(partido, accion):
    if partido.estado == Partido.Estado.FINALIZADO:
        raise Conflicto(f'No se puede {accion} un partido que ya tiene resultado. '
                        'Elimine primero el resultado en /api/goles/.')


# --------------------------------------------------------------------------- #
# Resultados (módulo "goles")
# --------------------------------------------------------------------------- #
def calcular_ganador(partido, goles_local, goles_visitante):
    if goles_local == goles_visitante:
        return None, None, True
    if goles_local > goles_visitante:
        return partido.equipo_local, partido.equipo_visitante, False
    return partido.equipo_visitante, partido.equipo_local, False


def validar_marcador(partido, goles_local, goles_visitante, anotadores):

    if partido.torneo.estado != Torneo.Estado.EN_CURSO:
        raise ValidationError({'partido': 'El torneo de este partido no está en curso.'})

    if partido.fecha > timezone.localdate():
        raise ValidationError(
            {'partido': f'El partido está programado para el {partido.fecha}; no se puede '
                        'registrar el resultado antes de que se juegue.'}
        )

    for campo, valor in (('goles_local', goles_local), ('goles_visitante', goles_visitante)):
        if valor is None or not 0 <= valor <= MAXIMO_GOLES:
            raise ValidationError({campo: f'Debe estar entre 0 y {MAXIMO_GOLES}.'})

    if anotadores is None:
        return []

    # Si se detallan los goleadores, deben cuadrar exactamente con el marcador.
    detalle = []
    conteo = {partido.equipo_local_id: 0, partido.equipo_visitante_id: 0}
    for dato in anotadores:
        jugador, tipo = dato['jugador'], dato.get('tipo', Anotador.Tipo.NORMAL)
        if jugador.equipo_id not in conteo:
            raise ValidationError(
                {'anotadores': f'{jugador.nombre} no juega en ninguno de los dos equipos del partido.'}
            )
        if not MINUTO_MINIMO <= dato['minuto'] <= MINUTO_MAXIMO:
            raise ValidationError({'anotadores': f'El minuto debe estar entre {MINUTO_MINIMO} y {MINUTO_MAXIMO}.'})

        if tipo == Anotador.Tipo.AUTOGOL:
            equipo_id = (partido.equipo_visitante_id if jugador.equipo_id == partido.equipo_local_id
                         else partido.equipo_local_id)
        else:
            equipo_id = jugador.equipo_id
        conteo[equipo_id] += 1
        detalle.append((jugador, equipo_id, dato['minuto'], tipo))

    if (conteo[partido.equipo_local_id], conteo[partido.equipo_visitante_id]) != (goles_local, goles_visitante):
        raise ValidationError(
            {'anotadores': (
                f'Los goleadores no cuadran con el marcador: indicaste {goles_local}-{goles_visitante} '
                f'pero los anotadores suman {conteo[partido.equipo_local_id]}-'
                f'{conteo[partido.equipo_visitante_id]} (un autogol suma al rival).'
            )}
        )
    return detalle


def guardar_anotadores(resultado, detalle):
    resultado.anotadores.all().delete()
    Anotador.objects.bulk_create([
        Anotador(resultado=resultado, jugador=jugador, equipo_id=equipo_id, minuto=minuto, tipo=tipo)
        for (jugador, equipo_id, minuto, tipo) in detalle
    ])


def bloquear_partido(partido_id):
    return (
        Partido.objects.select_for_update()
        .select_related('torneo', 'equipo_local', 'equipo_visitante')
        .get(pk=partido_id)
    )


@transaction.atomic
def registrar_resultado(partido_id, goles_local, goles_visitante, anotadores=None):
    partido = bloquear_partido(partido_id)

    if partido.estado == Partido.Estado.FINALIZADO:
        raise Conflicto('Este partido ya tiene resultado. Para corregirlo use PATCH en /api/goles/{id}/.')

    detalle = validar_marcador(partido, goles_local, goles_visitante, anotadores)
    ganador, perdedor, empate = calcular_ganador(partido, goles_local, goles_visitante)

    resultado = Resultado.objects.create(
        partido=partido, goles_local=goles_local, goles_visitante=goles_visitante,
        ganador=ganador, perdedor=perdedor, empate=empate,
    )
    guardar_anotadores(resultado, detalle)

    partido.estado = Partido.Estado.FINALIZADO
    partido.save(update_fields=['estado'])

    recalcular_tabla(partido.torneo)
    campeon = cerrar_torneo_si_termino(partido.torneo_id)
    return resultado, campeon


@transaction.atomic
def corregir_resultado(resultado, goles_local, goles_visitante, anotadores=None):
    partido = bloquear_partido(resultado.partido_id)

    if partido.torneo.estado == Torneo.Estado.FINALIZADO:
        raise Conflicto('El torneo ya finalizó; sus resultados no se pueden modificar.')

    # Si cambia el marcador y no se mandan goleadores nuevos, los anteriores deben seguir cuadrando.
    if anotadores is None and resultado.anotadores.exists() and (
        (goles_local, goles_visitante) != (resultado.goles_local, resultado.goles_visitante)
    ):
        raise ValidationError(
            {'anotadores': 'Cambiaste el marcador: envía también la lista de anotadores corregida '
                           '(o una lista vacía [] si no quieres detallar goleadores).'}
        )

    detalle = validar_marcador(partido, goles_local, goles_visitante, anotadores)
    ganador, perdedor, empate = calcular_ganador(partido, goles_local, goles_visitante)

    resultado.goles_local, resultado.goles_visitante = goles_local, goles_visitante
    resultado.ganador, resultado.perdedor, resultado.empate = ganador, perdedor, empate
    resultado.save()
    if anotadores is not None:
        guardar_anotadores(resultado, detalle)

    recalcular_tabla(partido.torneo)
    return resultado


@transaction.atomic
def eliminar_resultado(resultado):
    partido = bloquear_partido(resultado.partido_id)

    if partido.torneo.estado == Torneo.Estado.FINALIZADO:
        raise Conflicto('El torneo ya finalizó; sus resultados no se pueden eliminar.')

    resultado.delete()
    partido.estado = Partido.Estado.PROGRAMADO
    partido.save(update_fields=['estado'])
    recalcular_tabla(partido.torneo)


def cerrar_torneo_si_termino(torneo_id):
    """El torneo termina cuando todos los equipos se enfrentaron (1 o 2 veces)."""
    torneo = Torneo.objects.select_for_update().get(pk=torneo_id)

    if torneo.estado != Torneo.Estado.EN_CURSO:
        return None

    jugados = torneo.partidos.filter(estado=Partido.Estado.FINALIZADO).count()
    if jugados < torneo.cantidad_partidos:
        return None

    lider = tabla_ordenada(torneo).first()
    torneo.campeon = lider.equipo
    torneo.estado = Torneo.Estado.FINALIZADO
    torneo.save(update_fields=['campeon', 'estado'])
    return torneo.campeon
