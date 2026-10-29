"""
python manage.py cargar_datos_demo

Crea datos ficticios para probar la API:
  - 4 equipos con 6 jugadores cada uno.
  - Torneo "Copa Pacífico Demo" (máx. 4 equipos) con los 4 inscritos:
    al llenarse pasa solo a EN_CURSO y queda listo para programar partidos.
  - Torneo "Liga Abierta Demo" (máx. 6 equipos) sin inscritos, para probar inscripciones.

No crea usuarios ni roles (se crean desde el admin).
Se puede ejecutar varias veces: no duplica datos.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from equipos.models import Equipo, Jugador
from inscripciones.models import Inscripcion
from torneos.models import Torneo
from torneos.servicios import poner_en_curso


EQUIPOS = [
    ('Pumas del Pacífico', 'Laura Mora', 'Puntarenas'),
    ('Tiburones FC', 'Carlos Rojas', 'Esparza'),
    ('Halcones Unidos', 'Andrea Solís', 'Barranca'),
    ('Deportivo Caldera', 'Mario Vargas', 'Caldera'),
]

NOMBRES = ['Andrés', 'Bryan', 'Daniel', 'Esteban', 'Fabián', 'Gabriel']
APELLIDOS = ['Jiménez', 'Castro', 'Araya', 'Quesada', 'Brenes', 'Chaves']
POSICIONES = ['POR', 'DEF', 'DEF', 'MED', 'MED', 'DEL']


class Command(BaseCommand):
    help = 'Carga equipos, jugadores y un torneo de ejemplo.'

    @transaction.atomic
    def handle(self, *args, **opciones):
        equipos = []
        for indice_equipo, (nombre, entrenador, ciudad) in enumerate(EQUIPOS):
            equipo, _ = Equipo.objects.get_or_create(
                nombre=nombre, defaults={'entrenador': entrenador, 'ciudad': ciudad}
            )
            equipos.append(equipo)
            for indice, posicion in enumerate(POSICIONES):
                Jugador.objects.get_or_create(
                    identificacion=f'6{indice_equipo + 1:04d}{indice + 1:04d}',
                    defaults={
                        'nombre': f'{NOMBRES[indice]} {APELLIDOS[(indice + indice_equipo) % 6]}',
                        'numero_camiseta': [1, 2, 4, 8, 10, 9][indice],
                        'posicion': posicion,
                        'equipo': equipo,
                    },
                )

        hoy = timezone.localdate()
        torneo, _ = Torneo.objects.get_or_create(
            nombre='Copa Pacífico Demo',
            defaults={
                'descripcion': 'Torneo de ejemplo generado por cargar_datos_demo.',
                'fecha_inicio': hoy - timedelta(days=7),
                'fecha_fin': hoy + timedelta(days=90),
                'maximo_equipos': 4,
                'minimo_jugadores_por_equipo': 5,
                'vueltas': Torneo.Vueltas.SOLO_IDA,
            },
        )
        if torneo.estado == Torneo.Estado.INSCRIPCIONES:
            for equipo in equipos:
                Inscripcion.objects.get_or_create(torneo=torneo, equipo=equipo)
            poner_en_curso(torneo)

        Torneo.objects.get_or_create(
            nombre='Liga Abierta Demo',
            defaults={
                'descripcion': 'Torneo de ida y vuelta con inscripciones abiertas.',
                'fecha_inicio': hoy,
                'fecha_fin': hoy + timedelta(days=180),
                'maximo_equipos': 6,
                'minimo_jugadores_por_equipo': 5,
                'vueltas': Torneo.Vueltas.IDA_Y_VUELTA,
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Equipo.objects.count()} equipos, {Jugador.objects.count()} jugadores. '
            f'"{torneo.nombre}" (id={torneo.id}) está {torneo.estado} con '
            f'{torneo.cantidad_partidos} partidos por jugar; "Liga Abierta Demo" tiene '
            'inscripciones abiertas.'
        ))
