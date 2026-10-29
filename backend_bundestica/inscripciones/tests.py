from backend_bundestica.pruebas_base import PruebaBase
from inscripciones.models import Inscripcion


class InscripcionesTests(PruebaBase):

    def setUp(self):
        self.torneo = self.crear_torneo(maximo_equipos=3)
        self.equipo_a = self.crear_equipo('Alfa')
        self.equipo_b = self.crear_equipo('Beta')
        self.equipo_c = self.crear_equipo('Gamma')
        self.equipo_d = self.crear_equipo('Delta')

    def inscribir_por_api(self, equipo, torneo=None):
        return self.como('Administrador').post('/api/inscripciones/', {
            'torneo': (torneo or self.torneo).pk, 'equipo': equipo.pk,
        })

    def test_inscribir_equipo_con_sus_jugadores(self):
        respuesta = self.inscribir_por_api(self.equipo_a)
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(len(respuesta.data['inscripcion']['jugadores']), 5)
        self.assertEqual(respuesta.data['estado_torneo'], 'INSCRIPCIONES')

    def test_al_llenar_el_cupo_el_torneo_pasa_a_en_curso(self):
        self.inscribir_por_api(self.equipo_a)
        self.inscribir_por_api(self.equipo_b)
        respuesta = self.inscribir_por_api(self.equipo_c)
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data['estado_torneo'], 'EN_CURSO')
        self.torneo.refresh_from_db()
        self.assertEqual(self.torneo.estado, 'EN_CURSO')
        self.assertEqual(self.torneo.cantidad_partidos, 3)

    def test_no_superar_el_maximo_400(self):
        for equipo in (self.equipo_a, self.equipo_b, self.equipo_c):
            self.inscribir_por_api(equipo)
        respuesta = self.inscribir_por_api(self.equipo_d)
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Inscripcion.objects.filter(torneo=self.torneo).count(), 3)

    def test_equipo_duplicado_400(self):
        self.inscribir_por_api(self.equipo_a)
        respuesta = self.inscribir_por_api(self.equipo_a)
        self.assertEqual(respuesta.status_code, 400)

    def test_plantilla_minima_400(self):
        incompleto = self.crear_equipo('Incompleto', jugadores=3)
        respuesta = self.inscribir_por_api(incompleto)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('equipo', respuesta.data)

    def test_torneos_disponibles(self):
        lleno, _ = self.torneo_en_curso(nombre='Ya lleno')
        self.crear_torneo(nombre='Exigente', minimo_jugadores_por_equipo=8)
        self.inscribir(self.torneo, self.equipo_a)

        cliente = self.como('Consulta')
        todos = cliente.get('/api/inscripciones/torneos_disponibles/')
        nombres = {t['nombre'] for t in todos.data['torneos']}
        self.assertEqual(nombres, {'Liga de Pruebas', 'Exigente'})

        para_alfa = cliente.get('/api/inscripciones/torneos_disponibles/', {'equipo': self.equipo_a.pk})
        self.assertEqual(para_alfa.data['cantidad'], 0)     # ya inscrito / no cumple mínimo

        para_beta = cliente.get('/api/inscripciones/torneos_disponibles/', {'equipo': self.equipo_b.pk})
        self.assertEqual([t['nombre'] for t in para_beta.data['torneos']], ['Liga de Pruebas'])

    def test_inscripciones_cerradas_400(self):
        torneo, _ = self.torneo_en_curso(nombre='Cerrado')
        respuesta = self.inscribir_por_api(self.equipo_c, torneo)
        self.assertEqual(respuesta.status_code, 400)

    def test_retirar_equipo_antes_de_iniciar(self):
        self.inscribir(self.torneo, self.equipo_a)
        inscripcion = Inscripcion.objects.get(torneo=self.torneo, equipo=self.equipo_a)
        respuesta = self.como('Administrador').delete(f'/api/inscripciones/{inscripcion.pk}/')
        self.assertEqual(respuesta.status_code, 204)

    def test_no_retirar_equipo_de_torneo_iniciado_409(self):
        torneo, equipos = self.torneo_en_curso(nombre='Iniciado')
        inscripcion = Inscripcion.objects.get(torneo=torneo, equipo=equipos[0])
        respuesta = self.como('Administrador').delete(f'/api/inscripciones/{inscripcion.pk}/')
        self.assertEqual(respuesta.status_code, 409)

    def test_no_mover_inscripcion_a_otro_torneo_400(self):
        otro = self.crear_torneo(nombre='Otro torneo')
        self.inscribir(self.torneo, self.equipo_a)
        inscripcion = Inscripcion.objects.get(torneo=self.torneo)
        respuesta = self.como('Administrador').patch(
            f'/api/inscripciones/{inscripcion.pk}/', {'torneo': otro.pk}
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_filtro_por_torneo(self):
        otro = self.crear_torneo(nombre='Paralelo')
        self.inscribir(self.torneo, self.equipo_a, self.equipo_b)
        self.inscribir(otro, self.equipo_c)
        respuesta = self.como('Consulta').get('/api/inscripciones/', {'torneo': self.torneo.pk})
        self.assertEqual(respuesta.data['count'], 2)

    def test_operador_no_inscribe_403(self):
        respuesta = self.como('Operador').post('/api/inscripciones/', {
            'torneo': self.torneo.pk, 'equipo': self.equipo_a.pk,
        })
        self.assertEqual(respuesta.status_code, 403)
