"""
Pruebas del flujo completo desde el panel de administración de Django
(lo mismo que hace el usuario en el navegador).
"""

from django.contrib.auth.models import User
from django.test import TestCase

from backend_bundestica.pruebas_base import HOY, PruebaBase
from equipos.models import Jugador
from partidos.models import Partido, Resultado
from torneos.models import Torneo


class FlujoAdminTests(PruebaBase, TestCase):

    def setUp(self):
        User.objects.create_superuser('admin', 'admin@x.com', 'Clave12345!')
        self.client.login(username='admin', password='Clave12345!')

    # --- utilidades -------------------------------------------------------- #
    def inscribir_admin(self, torneo, equipos):
        return self.client.post(
            f'/admin/inscripciones/inscripcionportorneo/{torneo.pk}/change/',
            {'equipos': [e.pk for e in equipos], '_save': '1'}, follow=True,
        )

    def programar_admin(self, torneo, local, visitante, fecha=None):
        return self.client.post('/admin/partidos/partido/add/', {
            'torneo': torneo.pk, 'equipo_local': local.pk, 'equipo_visitante': visitante.pk,
            'fecha': (fecha or HOY).isoformat(), '_save': '1',
        }, follow=True)

    def goles_admin(self, partido, local, visitante, goleadores=(), resultado=None):
        datos = {
            'goles_local': local, 'goles_visitante': visitante,
            'anotadores-TOTAL_FORMS': '3', 'anotadores-INITIAL_FORMS': '0',
            'anotadores-MIN_NUM_FORMS': '0', 'anotadores-MAX_NUM_FORMS': '1000', '_save': '1',
        }
        for i in range(3):
            datos[f'anotadores-{i}-tipo'] = 'NORMAL'
        for i, (jugador, minuto) in enumerate(goleadores):
            datos[f'anotadores-{i}-jugador'] = jugador.pk
            datos[f'anotadores-{i}-minuto'] = minuto
        if resultado is None:
            datos['partido'] = partido.pk
            return self.client.post('/admin/partidos/resultado/add/', datos, follow=True)
        return self.client.post(f'/admin/partidos/resultado/{resultado.pk}/change/', datos, follow=True)

    def errores(self, respuesta):
        formulario = respuesta.context.get('adminform') if respuesta.context else None
        return formulario.form.errors if formulario else {}

    # --- inscripciones ----------------------------------------------------- #
    def test_inscripciones_lista_los_torneos_creados(self):
        self.crear_torneo(nombre='Concacaf')
        respuesta = self.client.get('/admin/inscripciones/inscripcionportorneo/')
        self.assertContains(respuesta, 'Concacaf')

    def test_inscribir_respeta_maximo_y_minimo(self):
        torneo = self.crear_torneo(maximo_equipos=2)
        a, b, c = self.crear_equipo('A'), self.crear_equipo('B'), self.crear_equipo('C')
        corto = self.crear_equipo('Corto', jugadores=2)

        self.inscribir_admin(torneo, [a, b, c])
        self.assertEqual(torneo.inscripciones.count(), 0)          # más que el máximo
        self.inscribir_admin(torneo, [a, corto])
        self.assertEqual(torneo.inscripciones.count(), 0)          # sin el mínimo de jugadores
        self.inscribir_admin(torneo, [a])
        self.assertEqual(torneo.inscripciones.count(), 1)
        torneo.refresh_from_db()
        self.assertEqual(torneo.estado, 'INSCRIPCIONES')

    def test_al_llenar_el_cupo_pasa_a_en_curso(self):
        torneo = self.crear_torneo(maximo_equipos=3, vueltas=2)
        equipos = [self.crear_equipo(n) for n in ('A', 'B', 'C')]
        respuesta = self.inscribir_admin(torneo, equipos)
        self.assertContains(respuesta, 'pasó a EN CURSO')
        torneo.refresh_from_db()
        self.assertEqual(torneo.estado, 'EN_CURSO')
        self.assertEqual(torneo.cantidad_partidos, 6)

    # --- partidos ---------------------------------------------------------- #
    def test_partidos_solo_entre_inscritos_y_no_contra_si_mismo(self):
        torneo, (a, b) = self.torneo_en_curso()
        ajeno = self.crear_equipo('Ajeno')
        self.assertContains(self.programar_admin(torneo, a, a), 'no puede enfrentarse a sí mismo')
        self.assertContains(self.programar_admin(torneo, a, ajeno), 'no está inscrito')
        self.programar_admin(torneo, a, b)
        self.assertEqual(Partido.objects.filter(torneo=torneo).count(), 1)

    def test_ida_y_vuelta_dos_partidos_por_pareja(self):
        torneo, (a, b) = self.torneo_en_curso(vueltas=2)
        self.programar_admin(torneo, a, b)
        self.programar_admin(torneo, b, a)
        self.assertContains(self.programar_admin(torneo, a, b), 'ya recibió')
        self.assertEqual(Partido.objects.filter(torneo=torneo).count(), 2)

    def test_solo_ida_una_vez_por_pareja(self):
        torneo, (a, b) = self.torneo_en_curso()
        self.programar_admin(torneo, a, b)
        self.assertContains(self.programar_admin(torneo, b, a), 'una sola vez')

    # --- goles ------------------------------------------------------------- #
    def test_goles_dicen_quien_gano_y_termina_el_torneo(self):
        torneo, (a, b) = self.torneo_en_curso()
        partido = self.crear_partido(torneo, a, b)
        respuesta = self.goles_admin(partido, 0, 2)
        self.assertContains(respuesta, f'Ganó {b.nombre}')
        self.assertContains(respuesta, f'Campeón: {b.nombre}')
        torneo.refresh_from_db()
        self.assertEqual((torneo.estado, torneo.campeon_id), ('FINALIZADO', b.pk))

    def test_empate(self):
        torneo, (a, b, c) = self.torneo_en_curso(cantidad_equipos=3)
        partido = self.crear_partido(torneo, a, b)
        self.assertContains(self.goles_admin(partido, 1, 1), 'Empatado')
        self.assertTrue(Resultado.objects.get(partido=partido).empate)

    def test_goleadores_deben_cuadrar(self):
        torneo, (a, b, c) = self.torneo_en_curso(cantidad_equipos=3)
        partido = self.crear_partido(torneo, a, b)
        self.assertContains(self.goles_admin(partido, 2, 0, [(self.goleador(a), 10)]), 'no cuadran')
        self.assertFalse(Resultado.objects.exists())
        self.goles_admin(partido, 1, 0, [(self.goleador(a), 10)])
        self.assertEqual(Resultado.objects.get().anotadores.count(), 1)

    def test_corregir_marcador_actualiza_ganador(self):
        torneo, (a, b, c) = self.torneo_en_curso(cantidad_equipos=3)
        partido = self.crear_partido(torneo, a, b)
        self.goles_admin(partido, 1, 0)
        resultado = Resultado.objects.get()
        self.goles_admin(partido, 0, 3, resultado=resultado)
        resultado.refresh_from_db()
        self.assertEqual(resultado.ganador_id, b.pk)
        self.assertEqual(torneo.estadisticas.get(equipo=b).puntos, 3)

    def test_ida_y_vuelta_no_termina_con_un_solo_partido(self):
        torneo, (a, b) = self.torneo_en_curso(vueltas=2)
        self.goles_admin(self.crear_partido(torneo, a, b), 1, 0)
        torneo.refresh_from_db()
        self.assertEqual(torneo.estado, 'EN_CURSO')
        self.goles_admin(self.crear_partido(torneo, b, a), 1, 0)
        torneo.refresh_from_db()
        self.assertEqual(torneo.estado, 'FINALIZADO')

    # --- estadísticas y jugadores ------------------------------------------ #
    def test_estadisticas_solo_de_torneos_finalizados(self):
        en_curso, _ = self.torneo_en_curso(nombre='Jugando')
        terminado, (x, y) = self.torneo_en_curso(nombre='Terminado')
        self.goles_admin(self.crear_partido(terminado, x, y), 3, 0)
        respuesta = self.client.get('/admin/estadisticas/estadistica/')
        self.assertContains(respuesta, x.nombre)
        self.assertNotContains(respuesta, 'Juga A')

    def test_jugador_no_puede_estar_en_dos_equipos(self):
        a, b = self.crear_equipo('Uno', jugadores=1), self.crear_equipo('Dos', jugadores=0)
        existente = a.jugadores.first()
        self.client.post('/admin/equipos/jugador/add/', {
            'nombre': 'Copia', 'identificacion': existente.identificacion, 'numero_camiseta': 7,
            'posicion': 'DEL', 'equipo': b.pk, '_save': '1',
        })
        self.assertFalse(Jugador.objects.filter(nombre='Copia').exists())
