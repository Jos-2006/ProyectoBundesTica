from backend_bundestica.pruebas_base import PruebaBase


class EstadisticasTests(PruebaBase):

    def torneo_finalizado(self):
        """Torneo de 3 equipos jugado completo: A 2-0 B, A 1-1 C, B 0-3 C (con anotadores)."""
        torneo, (a, b, c) = self.torneo_en_curso(cantidad_equipos=3)
        ga, gb, gc = self.goleador(a), self.goleador(b), self.goleador(c)
        self.registrar(self.crear_partido(torneo, a, b), 2, 0,
                       [{'jugador': ga.pk, 'minuto': 10}, {'jugador': gb.pk, 'minuto': 30, 'tipo': 'AUTOGOL'}])
        self.registrar(self.crear_partido(torneo, a, c), 1, 1,
                       [{'jugador': ga.pk, 'minuto': 5}, {'jugador': gc.pk, 'minuto': 70}])
        self.registrar(self.crear_partido(torneo, b, c), 0, 3,
                       [{'jugador': gc.pk, 'minuto': m} for m in (1, 2, 3)])
        torneo.refresh_from_db()
        return torneo, (a, b, c)

    def test_solo_torneos_finalizados(self):
        finalizado, _ = self.torneo_finalizado()
        en_curso, _ = self.torneo_en_curso(nombre='Sin terminar')
        cliente = self.como('Consulta')

        lista = cliente.get('/api/estadisticas/torneos/')
        self.assertEqual([t['torneo_id'] for t in lista.data['results']], [finalizado.pk])

        respuesta = cliente.get(f'/api/estadisticas/torneos/{en_curso.pk}/posiciones/')
        self.assertEqual(respuesta.status_code, 400)

    def test_tabla_final_con_porcentajes(self):
        torneo, (a, b, c) = self.torneo_finalizado()
        respuesta = self.como('Consulta').get(f'/api/estadisticas/torneos/{torneo.pk}/posiciones/')
        self.assertEqual(respuesta.status_code, 200)
        tabla = respuesta.data['tabla']
        # A y C con 4 puntos; C gana por diferencia de goles (+3 vs +2).
        self.assertEqual([f['equipo_id'] for f in tabla], [c.pk, a.pk, b.pk])
        self.assertEqual(respuesta.data['campeon'], c.nombre)
        lider = tabla[0]
        self.assertEqual(lider['porcentaje_victorias'], 50.0)
        self.assertEqual(lider['porcentaje_empates'], 50.0)
        self.assertAlmostEqual(lider['rendimiento'], 66.67)

    def test_goleadores_sin_autogoles(self):
        torneo, (a, b, c) = self.torneo_finalizado()
        respuesta = self.como('Consulta').get(f'/api/estadisticas/torneos/{torneo.pk}/goleadores/')
        goles = {fila['jugador']: fila['goles'] for fila in respuesta.data['goleadores']}
        self.assertEqual(goles[self.goleador(c).nombre], 4)
        self.assertEqual(goles[self.goleador(a).nombre], 2)
        self.assertNotIn(self.goleador(b).nombre, goles)

    def test_partidos_jugados_de_torneos_finalizados(self):
        torneo, _ = self.torneo_finalizado()
        otro, (x, y) = self.torneo_en_curso(nombre='Pendiente')
        self.registrar(self.crear_partido(otro, x, y), 0, 0)   # este lo termina también
        respuesta = self.como('Consulta').get('/api/estadisticas/partidos/', {'torneo': torneo.pk})
        self.assertEqual(respuesta.data['count'], 3)
        empates = self.como('Consulta').get('/api/estadisticas/partidos/', {'resultado': 'EMPATE'})
        self.assertEqual(empates.data['count'], 2)

    def test_resumen_del_torneo(self):
        torneo, _ = self.torneo_finalizado()
        respuesta = self.como('Consulta').get(f'/api/estadisticas/torneos/{torneo.pk}/resumen/')
        self.assertEqual(respuesta.data['goles_totales'], 7)
        self.assertAlmostEqual(respuesta.data['porcentaje_empates'], 33.33)
        self.assertEqual(respuesta.data['maximo_goleador']['goles'], 4)

    def test_tabla_en_vivo_desde_torneos(self):
        torneo, (a, b) = self.torneo_en_curso(nombre='En vivo', maximo_equipos=3)
        respuesta = self.como('Consulta').get(f'/api/torneos/{torneo.pk}/tabla/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data['tabla']), 2)

    def test_estadisticas_son_solo_lectura_405(self):
        torneo, _ = self.torneo_finalizado()
        cliente = self.como('Administrador')
        self.assertEqual(cliente.post('/api/estadisticas/partidos/', {}).status_code, 405)
        self.assertEqual(cliente.delete(f'/api/estadisticas/torneos/{torneo.pk}/').status_code, 405)

    def test_estadisticas_requieren_token_401(self):
        respuesta = self.client.get('/api/estadisticas/torneos/')
        self.assertEqual(respuesta.status_code, 401)
