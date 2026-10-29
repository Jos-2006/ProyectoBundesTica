from backend_bundestica.pruebas_base import PruebaBase
from equipos.models import Equipo, Jugador


class CrudEquiposTests(PruebaBase):

    def test_crear_equipo(self):
        respuesta = self.como('Administrador').post('/api/equipos/', {'nombre': 'Nuevo FC', 'ciudad': 'Esparza'})
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertTrue(Equipo.objects.filter(nombre='Nuevo FC').exists())

    def test_listar_equipos_paginado(self):
        for numero in range(12):
            Equipo.objects.create(nombre=f'Equipo {numero:02d}')
        respuesta = self.como('Consulta').get('/api/equipos/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 12)
        self.assertEqual(len(respuesta.data['results']), 10)
        self.assertIsNotNone(respuesta.data['next'])

    def test_modificar_equipo(self):
        equipo = Equipo.objects.create(nombre='Viejo')
        respuesta = self.como('Administrador').patch(f'/api/equipos/{equipo.pk}/', {'nombre': 'Renovado'})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        equipo.refresh_from_db()
        self.assertEqual(equipo.nombre, 'Renovado')

    def test_eliminar_equipo(self):
        equipo = Equipo.objects.create(nombre='Temporal')
        respuesta = self.como('Administrador').delete(f'/api/equipos/{equipo.pk}/')
        self.assertEqual(respuesta.status_code, 204)

    def test_equipo_inexistente_404(self):
        respuesta = self.como('Consulta').get('/api/equipos/99999/')
        self.assertEqual(respuesta.status_code, 404)

    def test_nombre_duplicado_400(self):
        Equipo.objects.create(nombre='Unico')
        respuesta = self.como('Administrador').post('/api/equipos/', {'nombre': 'unico'})
        self.assertEqual(respuesta.status_code, 400)

    def test_no_eliminar_equipo_inscrito_409(self):
        torneo = self.crear_torneo()
        equipo = self.crear_equipo('Inscrito')
        self.inscribir(torneo, equipo)
        respuesta = self.como('Administrador').delete(f'/api/equipos/{equipo.pk}/')
        self.assertEqual(respuesta.status_code, 409)


class JugadoresTests(PruebaBase):

    def setUp(self):
        self.equipo = self.crear_equipo('Local', jugadores=2)

    def test_crear_jugador(self):
        respuesta = self.como('Administrador').post('/api/jugadores/', {
            'nombre': 'Nuevo', 'identificacion': '1-1111-1111',
            'numero_camiseta': 7, 'posicion': 'DEL', 'equipo': self.equipo.pk,
        })
        self.assertEqual(respuesta.status_code, 201, respuesta.data)

    def test_camiseta_repetida_en_post_400(self):
        respuesta = self.como('Administrador').post('/api/jugadores/', {
            'nombre': 'Copia', 'identificacion': '2-2222-2222',
            'numero_camiseta': 1, 'equipo': self.equipo.pk,
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('numero_camiseta', respuesta.data)

    def test_camiseta_repetida_en_patch_400(self):
        jugador = self.equipo.jugadores.get(numero_camiseta=2)
        respuesta = self.como('Administrador').patch(f'/api/jugadores/{jugador.pk}/', {'numero_camiseta': 1})
        self.assertEqual(respuesta.status_code, 400)

    def test_camiseta_fuera_de_rango_400(self):
        respuesta = self.como('Administrador').post('/api/jugadores/', {
            'nombre': 'Cero', 'identificacion': '3-3333-3333',
            'numero_camiseta': 100, 'equipo': self.equipo.pk,
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_plantilla_congelada_en_torneo_en_curso_400(self):
        torneo, equipos = self.torneo_en_curso()
        respuesta = self.como('Administrador').post('/api/jugadores/', {
            'nombre': 'Refuerzo', 'identificacion': '4-4444-4444',
            'numero_camiseta': 30, 'equipo': equipos[0].pk,
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_jugador_no_puede_estar_en_dos_equipos_400(self):
        otro = self.crear_equipo('Otro', jugadores=0)
        existente = self.equipo.jugadores.first()
        respuesta = self.como('Administrador').post('/api/jugadores/', {
            'nombre': 'Mismo jugador', 'identificacion': existente.identificacion,
            'numero_camiseta': 20, 'equipo': otro.pk,
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('identificacion', respuesta.data)

    def test_identificacion_se_compara_normalizada_400(self):
        cliente = self.como('Administrador')
        primero = cliente.post('/api/jugadores/', {
            'nombre': 'Original', 'identificacion': '1-2345-6789',
            'numero_camiseta': 30, 'equipo': self.equipo.pk,
        })
        self.assertEqual(primero.status_code, 201, primero.data)
        self.assertEqual(primero.data['identificacion'], '123456789')
        otro = self.crear_equipo('Rival', jugadores=0)
        copia = cliente.post('/api/jugadores/', {
            'nombre': 'Copia', 'identificacion': '1 2345 6789',
            'numero_camiseta': 31, 'equipo': otro.pk,
        })
        self.assertEqual(copia.status_code, 400)

    def test_no_dejar_equipo_inscrito_bajo_el_minimo_409(self):
        torneo = self.crear_torneo(minimo_jugadores_por_equipo=2)
        self.inscribir(torneo, self.equipo)          # tiene justo 2 jugadores
        jugador = self.equipo.jugadores.first()
        respuesta = self.como('Administrador').delete(f'/api/jugadores/{jugador.pk}/')
        self.assertEqual(respuesta.status_code, 409)

    def test_filtros_combinados_y_busqueda(self):
        Jugador.objects.create(nombre='Delantero Estrella', identificacion='X-1', numero_camiseta=9,
                               posicion='DEL', equipo=self.equipo)
        otro = self.crear_equipo('Visita', jugadores=0)
        Jugador.objects.create(nombre='Delantero Visita', identificacion='X-2', numero_camiseta=9,
                               posicion='DEL', equipo=otro)
        cliente = self.como('Consulta')

        respuesta = cliente.get('/api/jugadores/', {'equipo': self.equipo.pk, 'posicion': 'del'})
        self.assertEqual(respuesta.data['count'], 1)

        respuesta = cliente.get('/api/jugadores/', {'search': 'Delantero'})
        self.assertEqual(respuesta.data['count'], 2)

        respuesta = cliente.get('/api/jugadores/', {'equipo': 'abc'})
        self.assertEqual(respuesta.status_code, 400)


class PermisosTests(PruebaBase):

    def test_sin_token_401(self):
        respuesta = self.client.get('/api/equipos/')
        self.assertEqual(respuesta.status_code, 401)

    def test_token_invalido_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token no-existe')
        respuesta = self.client.get('/api/equipos/')
        self.assertEqual(respuesta.status_code, 401)

    def test_consulta_puede_leer_pero_no_crear_403(self):
        cliente = self.como('Consulta')
        self.assertEqual(cliente.get('/api/equipos/').status_code, 200)
        self.assertEqual(cliente.post('/api/equipos/', {'nombre': 'No'}).status_code, 403)

    def test_operador_no_elimina_equipos_403(self):
        equipo = Equipo.objects.create(nombre='Protegido')
        respuesta = self.como('Operador').delete(f'/api/equipos/{equipo.pk}/')
        self.assertEqual(respuesta.status_code, 403)
