from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

class PruebasPerfilUsuario(APITestCase):
    # Comprobamos que la API responda 401 cuando falta el token.
    def test_sin_token_devuelve_401(self):
        respuesta = self.client.get('/api/auth/me/')
        self.assertEqual(respuesta.status_code, 401)

    # Comprobamos que el perfil Consulta tenga acceso de solo lectura.
    def test_perfil_consulta_solo_lectura(self):
        usuario = get_user_model().objects.create_user(username='consulta_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Consulta')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        respuesta = self.client.get('/api/auth/me/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(any(respuesta.data['permisos'].values()))

    # Verificamos que el Operador pueda gestionar partidos.
    def test_perfil_operador_puede_partidos(self):
        usuario = get_user_model().objects.create_user(username='operador_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Operador')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        permisos = self.client.get('/api/auth/me/').data['permisos']
        self.assertTrue(permisos['partidos'])
        self.assertTrue(permisos['resultados'])
        self.assertFalse(permisos['equipos'])

    # Comprobamos que el superusuario tenga acceso a las operaciones autorizadas.
    def test_superusuario_puede_todos(self):
        usuario = get_user_model().objects.create_superuser(username='admin_prueba', password='clave_segura_123')
        self.client.force_authenticate(user=usuario)
        permisos = self.client.get('/api/auth/me/').data['permisos']
        self.assertTrue(all(permisos.values()))

    # Probamos que el inicio de sesión genere un token de Django.
    def test_token_real_de_django(self):
        get_user_model().objects.create_user(username='acceso_prueba', password='clave_segura_123')
        respuesta = self.client.post('/api/auth/token/', {
            'username': 'acceso_prueba', 'password': 'clave_segura_123'
        }, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('token', respuesta.data)

    # Comprobamos que el Operador no pueda registrar equipos.
    def test_operador_no_puede_registrar_equipos(self):
        usuario = get_user_model().objects.create_user(username='operador_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Operador')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        respuesta = self.client.post('/api/equipos/', {'nombre':'Equipo prueba'}, format='json')
        self.assertEqual(respuesta.status_code, 403)

    # Probamos que el perfil Consulta pueda listar equipos.
    def test_consulta_puede_listar_equipos(self):
        usuario = get_user_model().objects.create_user(username='consulta_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Consulta')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        respuesta = self.client.get('/api/equipos/')
        self.assertEqual(respuesta.status_code, 200)
