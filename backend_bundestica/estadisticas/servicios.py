"""
Servicio: recalcular la tabla de posiciones de un torneo.

Se ejecuta cada vez que se registra, corrige o elimina un resultado. Recalcula desde cero a
partir de los resultados registrados, así la tabla nunca queda desfasada.
"""

from partidos.models import Resultado

from .models import Estadistica


def recalcular_tabla(torneo):

    filas = {
        fila.equipo_id: fila
        for fila in Estadistica.objects.filter(torneo=torneo)
    }

    for fila in filas.values():
        fila.partidos_jugados = fila.partidos_ganados = 0
        fila.partidos_empatados = fila.partidos_perdidos = 0
        fila.goles_a_favor = fila.goles_en_contra = 0

    resultados = Resultado.objects.filter(partido__torneo=torneo).select_related('partido')

    for resultado in resultados:
        partido = resultado.partido
        local = filas.get(partido.equipo_local_id)
        visitante = filas.get(partido.equipo_visitante_id)
        if local is None or visitante is None:
            continue

        for fila, a_favor, en_contra in (
            (local, resultado.goles_local, resultado.goles_visitante),
            (visitante, resultado.goles_visitante, resultado.goles_local),
        ):
            fila.partidos_jugados += 1
            fila.goles_a_favor += a_favor
            fila.goles_en_contra += en_contra
            if a_favor > en_contra:
                fila.partidos_ganados += 1
            elif a_favor == en_contra:
                fila.partidos_empatados += 1
            else:
                fila.partidos_perdidos += 1

    for fila in filas.values():
        fila.diferencia_goles = fila.goles_a_favor - fila.goles_en_contra
        fila.puntos = (
            fila.partidos_ganados * torneo.puntos_victoria
            + fila.partidos_empatados * torneo.puntos_empate
            + fila.partidos_perdidos * torneo.puntos_derrota
        )

    Estadistica.objects.bulk_update(
        filas.values(),
        [
            'partidos_jugados', 'partidos_ganados', 'partidos_empatados',
            'partidos_perdidos', 'goles_a_favor', 'goles_en_contra',
            'diferencia_goles', 'puntos',
        ],
    )


def tabla_ordenada(torneo):
    return (
        Estadistica.objects.filter(torneo=torneo)
        .select_related('equipo', 'torneo')
        .order_by(*Estadistica.ORDEN_TABLA)
    )
