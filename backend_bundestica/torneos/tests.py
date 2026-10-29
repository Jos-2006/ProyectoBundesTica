from backend_bundestica.pruebas_base import HOY, PruebaBase
from torneos.models import Torneo


class TorneosTests(PruebaBase):

    def datos(self, **cambios):
        datos = {
            'nombre': 'Copa API',
            'fecha_inicio': HOY.isoformat(),
            'fecha_fin': '2027-12-31',
            'maximo_equipos': 6,
            'vueltas': 1,
        }
        datos.update(cambios)
        return datos

    def test_crear_torneo(self):
        respuesta = self.como('Administrador').post('/api/torneos/', self.datos())
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'INSCRIPCIONES')
        self.assertEqual(respuesta.data['partidos_si_se_llena'], 15)

    def test_ida_y_vuelta_duplica_los_partidos(self):
        respuesta = self.como('Administrador').post('/api/torneos/', self.datos(vueltas=2))
        self.assertEqual(respuesta.data['partidos_si_se_llena'], 30)

    def test_fecha_fin_anterior_400(self):
        respuesta = self.como('Administrador').post('/api/torneos/', self.datos(fecha_fin='2000-01-01'))
        self.assertEqual(respuesta.status_code, 400)

    def test_puntos_invalidos_400(self):
        respuesta = self.como('Administrador').post(
            '/api/torneos/', self.datos(puntos_victoria=1, puntos_empate=2)
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_maximo_equipos_fuera_de_rango_400(self):
        respuesta = self.como('Administrador').post('/api/torneos/', self.datos(maximo_equipos=1))
        self.assertEqual(respuesta.status_code, 400)

    def test_al_llenarse_pasa_a_en_curso(self):
        torneo, _ = self.torneo_en_curso(cantidad_equipos=4)
        self.assertEqual(torneo.estado, 'EN_CURSO')
        self.assertEqual(torneo.cantidad_partidos, 6)
        self.assertEqual(torneo.estadisticas.count(), 4)

    def test_ida_y_vuelta_en_curso(self):
        torneo, _ = self.torneo_en_curso(cantidad_equipos=3, vueltas=2)
        self.assertEqual(torneo.cantidad_partidos, 6)

    def test_iniciar_antes_de_llenarse(self):
        torneo = self.crear_torneo(maximo_equipos=6)
        self.inscribir(torneo, self.crear_equipo('Uno'), self.crear_equipo('Dos'), self.crear_equipo('Tres'))
        respuesta = self.como('Administrador').post(f'/api/torneos/{torneo.pk}/iniciar/')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['torneo']['cantidad_partidos'], 3)

    def test_iniciar_con_menos_de_dos_equipos_400(self):
        torneo = self.crear_torneo()
        self.inscribir(torneo, self.crear_equipo('Solo'))
        respuesta = self.como('Administrador').post(f'/api/torneos/{torneo.pk}/iniciar/')
        self.assertEqual(respuesta.status_code, 400)

    def test_iniciar_dos_veces_409(self):
        torneo, _ = self.torneo_en_curso()
        respuesta = self.como('Administrador').post(f'/api/torneos/{torneo.pk}/iniciar/')
        self.assertEqual(respuesta.status_code, 409)

    def test_no_modificar_torneo_iniciado_400(self):
        torneo, _ = self.torneo_en_curso()
        respuesta = self.como('Administrador').patch(f'/api/torneos/{torneo.pk}/', {'maximo_equipos': 10})
        self.assertEqual(respuesta.status_code, 400)

    def test_no_bajar_maximo_por_debajo_de_inscritos_400(self):
        torneo = self.crear_torneo()
        self.inscribir(torneo, self.crear_equipo('Uno'), self.crear_equipo('Dos'), self.crear_equipo('Tres'))
        respuesta = self.como('Administrador').patch(f'/api/torneos/{torneo.pk}/', {'maximo_equipos': 2})
        self.assertEqual(respuesta.status_code, 400)

    def test_no_subir_minimo_por_encima_de_inscritos_400(self):
        torneo = self.crear_torneo()
        self.inscribir(torneo, self.crear_equipo('Uno'))
        respuesta = self.como('Administrador').patch(
            f'/api/torneos/{torneo.pk}/', {'minimo_jugadores_por_equipo': 11}
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_no_eliminar_torneo_iniciado_409(self):
        torneo, _ = self.torneo_en_curso()
        respuesta = self.como('Administrador').delete(f'/api/torneos/{torneo.pk}/')
        self.assertEqual(respuesta.status_code, 409)

    def test_eliminar_torneo_sin_iniciar(self):
        torneo = self.crear_torneo()
        respuesta = self.como('Administrador').delete(f'/api/torneos/{torneo.pk}/')
        self.assertEqual(respuesta.status_code, 204)
        self.assertFalse(Torneo.objects.filter(pk=torneo.pk).exists())

    def test_enfrentamientos_pendientes(self):
        torneo, equipos = self.torneo_en_curso(cantidad_equipos=3, vueltas=2)
        self.crear_partido(torneo, equipos[0], equipos[1])
        respuesta = self.como('Consulta').get(f'/api/torneos/{torneo.pk}/enfrentamientos_pendientes/')
        self.assertEqual(respuesta.data['pendientes_por_programar'], 5)

    def test_operador_no_puede_crear_torneo_403(self):
        respuesta = self.como('Operador').post('/api/torneos/', self.datos())
        self.assertEqual(respuesta.status_code, 403)

    def test_filtro_por_estado_y_busqueda(self):
        self.crear_torneo(nombre='Copa Abierta')
        self.torneo_en_curso(nombre='Liga Jugándose')
        cliente = self.como('Consulta')
        respuesta = cliente.get('/api/torneos/', {'estado': 'en_curso'})
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['nombre'], 'Liga Jugándose')
        respuesta = cliente.get('/api/torneos/', {'search': 'Copa'})
        self.assertEqual(respuesta.data['count'], 1)
