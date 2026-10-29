from datetime import timedelta

from backend_bundestica.pruebas_base import HOY, PruebaBase
from partidos.models import Partido


class PartidosTests(PruebaBase):
    """Programar enfrentamientos: quién juega contra quién en cada torneo."""

    def programar(self, torneo, local, visitante, fecha=None, rol='Operador'):
        return self.como(rol).post('/api/partidos/', {
            'torneo': torneo.pk, 'equipo_local': local.pk, 'equipo_visitante': visitante.pk,
            'fecha': (fecha or HOY).isoformat(),
        })

    def test_crear_partido(self):
        torneo, (a, b) = self.torneo_en_curso()
        respuesta = self.programar(torneo, a, b)
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'PROGRAMADO')
        self.assertEqual(respuesta.data['resultado'], 'Pendiente')

    def test_equipo_contra_si_mismo_400(self):
        torneo, (a, b) = self.torneo_en_curso()
        respuesta = self.programar(torneo, a, a)
        self.assertEqual(respuesta.status_code, 400)

    def test_equipo_no_inscrito_400(self):
        torneo, (a, b) = self.torneo_en_curso()
        ajeno = self.crear_equipo('Ajeno')
        respuesta = self.programar(torneo, a, ajeno)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('equipo_visitante', respuesta.data)

    def test_torneo_con_inscripciones_abiertas_400(self):
        torneo = self.crear_torneo()
        a, b = self.crear_equipo('Uno'), self.crear_equipo('Dos')
        self.inscribir(torneo, a, b)
        respuesta = self.programar(torneo, a, b)
        self.assertEqual(respuesta.status_code, 400)

    def test_solo_ida_se_enfrentan_una_vez_400(self):
        torneo, (a, b) = self.torneo_en_curso()
        self.programar(torneo, a, b)
        self.assertEqual(self.programar(torneo, a, b).status_code, 400)
        self.assertEqual(self.programar(torneo, b, a).status_code, 400)

    def test_ida_y_vuelta_se_enfrentan_dos_veces(self):
        torneo, (a, b) = self.torneo_en_curso(vueltas=2)
        self.assertEqual(self.programar(torneo, a, b).status_code, 201)
        self.assertEqual(self.programar(torneo, b, a).status_code, 201)
        tercero = self.programar(torneo, a, b)
        self.assertEqual(tercero.status_code, 400)
        self.assertEqual(Partido.objects.filter(torneo=torneo).count(), 2)

    def test_fecha_fuera_del_torneo_400(self):
        torneo, (a, b) = self.torneo_en_curso()
        respuesta = self.programar(torneo, a, b, fecha=torneo.fecha_fin + timedelta(days=1))
        self.assertEqual(respuesta.status_code, 400)

    def test_reprogramar_partido_sin_resultado(self):
        torneo, (a, b) = self.torneo_en_curso()
        partido = self.crear_partido(torneo, a, b)
        nueva = (HOY + timedelta(days=5)).isoformat()
        respuesta = self.como('Operador').patch(f'/api/partidos/{partido.pk}/', {'fecha': nueva})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)

    def test_patch_no_puede_poner_al_mismo_equipo_400(self):
        torneo, (a, b) = self.torneo_en_curso()
        partido = self.crear_partido(torneo, a, b)
        respuesta = self.como('Operador').patch(f'/api/partidos/{partido.pk}/', {'equipo_visitante': a.pk})
        self.assertEqual(respuesta.status_code, 400)

    def test_no_modificar_ni_eliminar_partido_con_resultado_409(self):
        torneo, (a, b, c) = self.torneo_en_curso(cantidad_equipos=3)
        partido = self.crear_partido(torneo, a, b)
        self.registrar(partido, 1, 0)
        cliente = self.como('Administrador')
        self.assertEqual(cliente.patch(f'/api/partidos/{partido.pk}/', {'fecha': HOY.isoformat()}).status_code, 409)
        self.assertEqual(cliente.delete(f'/api/partidos/{partido.pk}/').status_code, 409)

    def test_eliminar_partido_programado(self):
        torneo, (a, b) = self.torneo_en_curso()
        partido = self.crear_partido(torneo, a, b)
        respuesta = self.como('Operador').delete(f'/api/partidos/{partido.pk}/')
        self.assertEqual(respuesta.status_code, 204)

    def test_consulta_no_programa_partidos_403(self):
        torneo, (a, b) = self.torneo_en_curso()
        respuesta = self.programar(torneo, a, b, rol='Consulta')
        self.assertEqual(respuesta.status_code, 403)

    def test_filtro_partidos_por_equipo_y_estado(self):
        torneo, (a, b, c) = self.torneo_en_curso(cantidad_equipos=3)
        self.crear_partido(torneo, a, b)
        self.crear_partido(torneo, a, c)
        self.crear_partido(torneo, b, c)
        respuesta = self.como('Consulta').get('/api/partidos/', {
            'torneo': torneo.pk, 'equipo': a.pk, 'estado': 'programado',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 2)


class GolesTests(PruebaBase):
    """Registrar el marcador de un partido: la API decide quién ganó o si empataron."""

    def setUp(self):
        self.torneo, (self.a, self.b, self.c) = self.torneo_en_curso(cantidad_equipos=3)
        self.partido = self.crear_partido(self.torneo, self.a, self.b)

    def test_registrar_victoria(self):
        respuesta = self.registrar(self.partido, 3, 1)
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        resultado = respuesta.data['resultado']
        self.assertEqual(resultado['resultado'], f'Ganó {self.a.nombre}')
        self.assertEqual(resultado['ganador']['id'], self.a.pk)
        self.assertEqual(resultado['perdedor']['id'], self.b.pk)
        self.partido.refresh_from_db()
        self.assertEqual(self.partido.estado, 'FINALIZADO')

    def test_registrar_empate(self):
        respuesta = self.registrar(self.partido, 2, 2)
        self.assertEqual(respuesta.data['resultado']['resultado'], 'Empatado')
        self.assertTrue(respuesta.data['resultado']['empate'])
        self.assertIsNone(respuesta.data['resultado']['ganador'])

    def test_goles_negativos_400(self):
        respuesta = self.registrar(self.partido, -1, 0)
        self.assertEqual(respuesta.status_code, 400)

    def test_partido_que_aun_no_se_juega_400(self):
        futuro = self.crear_partido(self.torneo, self.b, self.c, fecha=HOY + timedelta(days=3))
        respuesta = self.registrar(futuro, 1, 0)
        self.assertEqual(respuesta.status_code, 400)

    def test_resultado_dos_veces_409(self):
        self.registrar(self.partido, 1, 0)
        respuesta = self.registrar(self.partido, 2, 0)
        self.assertEqual(respuesta.status_code, 409)

    def test_anotadores_que_cuadran(self):
        anotadores = [
            {'jugador': self.goleador(self.a).pk, 'minuto': 10},
            {'jugador': self.goleador(self.a).pk, 'minuto': 50, 'tipo': 'PENAL'},
            {'jugador': self.goleador(self.a).pk, 'minuto': 80, 'tipo': 'AUTOGOL'},
        ]
        respuesta = self.registrar(self.partido, 2, 1, anotadores)
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(len(respuesta.data['resultado']['anotadores']), 3)

    def test_anotadores_que_no_cuadran_400(self):
        anotadores = [{'jugador': self.goleador(self.a).pk, 'minuto': 10}]
        respuesta = self.registrar(self.partido, 2, 0, anotadores)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('anotadores', respuesta.data)
        self.partido.refresh_from_db()
        self.assertEqual(self.partido.estado, 'PROGRAMADO')

    def test_anotador_de_otro_equipo_400(self):
        anotadores = [{'jugador': self.goleador(self.c).pk, 'minuto': 10}]
        respuesta = self.registrar(self.partido, 1, 0, anotadores)
        self.assertEqual(respuesta.status_code, 400)

    def test_corregir_resultado_actualiza_la_tabla(self):
        resultado_id = self.registrar(self.partido, 1, 0).data['resultado']['id']
        respuesta = self.como('Operador').patch(
            f'/api/goles/{resultado_id}/', {'goles_local': 0, 'goles_visitante': 2}, format='json'
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['ganador']['id'], self.b.pk)
        fila_b = self.torneo.estadisticas.get(equipo=self.b)
        self.assertEqual((fila_b.partidos_ganados, fila_b.puntos), (1, 3))

    def test_patch_cambia_marcador_sin_corregir_anotadores_400(self):
        anotadores = [{'jugador': self.goleador(self.a).pk, 'minuto': 10}]
        resultado_id = self.registrar(self.partido, 1, 0, anotadores).data['resultado']['id']
        respuesta = self.como('Operador').patch(
            f'/api/goles/{resultado_id}/', {'goles_local': 2}, format='json'
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_eliminar_resultado_vuelve_a_programado(self):
        resultado_id = self.registrar(self.partido, 1, 0).data['resultado']['id']
        respuesta = self.como('Operador').delete(f'/api/goles/{resultado_id}/')
        self.assertEqual(respuesta.status_code, 204)
        self.partido.refresh_from_db()
        self.assertEqual(self.partido.estado, 'PROGRAMADO')
        self.assertEqual(self.torneo.estadisticas.get(equipo=self.a).puntos, 0)

    def test_torneo_termina_cuando_todos_se_enfrentan(self):
        self.registrar(self.partido, 2, 0)                                     # A gana
        self.registrar(self.crear_partido(self.torneo, self.a, self.c), 1, 0)  # A gana
        ultimo = self.registrar(self.crear_partido(self.torneo, self.b, self.c), 1, 1)
        self.assertEqual(ultimo.status_code, 201, ultimo.data)
        self.assertTrue(ultimo.data['torneo_finalizado'])
        self.assertEqual(ultimo.data['campeon']['id'], self.a.pk)
        self.torneo.refresh_from_db()
        self.assertEqual(self.torneo.estado, 'FINALIZADO')
        self.assertEqual(self.torneo.campeon_id, self.a.pk)

    def test_torneo_ida_y_vuelta_necesita_los_dos_partidos(self):
        torneo, (x, y) = self.torneo_en_curso(nombre='Clásico', vueltas=2)
        ida = self.registrar(self.crear_partido(torneo, x, y), 1, 0)
        self.assertFalse(ida.data['torneo_finalizado'])
        vuelta = self.registrar(self.crear_partido(torneo, y, x), 3, 0)
        self.assertTrue(vuelta.data['torneo_finalizado'])
        self.assertEqual(vuelta.data['campeon']['id'], y.pk)

    def test_no_corregir_resultados_de_torneo_finalizado_409(self):
        torneo, (x, y) = self.torneo_en_curso(nombre='Final')
        resultado_id = self.registrar(self.crear_partido(torneo, x, y), 1, 0).data['resultado']['id']
        respuesta = self.como('Operador').delete(f'/api/goles/{resultado_id}/')
        self.assertEqual(respuesta.status_code, 409)

    def test_consulta_no_registra_goles_403(self):
        respuesta = self.registrar(self.partido, 1, 0, rol='Consulta')
        self.assertEqual(respuesta.status_code, 403)

    def test_no_eliminar_jugador_con_goles_409(self):
        jugador = self.goleador(self.a)
        self.registrar(self.partido, 1, 0, [{'jugador': jugador.pk, 'minuto': 5}])
        self.torneo.estado = 'FINALIZADO'       # la plantilla ya no está congelada
        self.torneo.save()
        respuesta = self.como('Administrador').delete(f'/api/jugadores/{jugador.pk}/')
        self.assertEqual(respuesta.status_code, 409)
