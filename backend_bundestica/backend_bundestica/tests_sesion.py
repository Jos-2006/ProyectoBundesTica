from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

class PruebasPerfilUsuario(APITestCase):
    def test_sin_token_devuelve_401(self):
        respuesta = self.client.get('/api/auth/me/')
        self.assertEqual(respuesta.status_code, 401)

    def test_perfil_consulta_solo_lectura(self):
        usuario = get_user_model().objects.create_user(username='consulta_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Consulta')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        respuesta = self.client.get('/api/auth/me/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(any(respuesta.data['permisos'].values()))

    def test_perfil_operador_puede_partidos(self):
        usuario = get_user_model().objects.create_user(username='operador_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Operador')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        permisos = self.client.get('/api/auth/me/').data['permisos']
        self.assertTrue(permisos['partidos'])
        self.assertTrue(permisos['resultados'])
        self.assertFalse(permisos['equipos'])

    def test_superusuario_puede_todos(self):
        usuario = get_user_model().objects.create_superuser(username='admin_prueba', password='clave_segura_123')
        self.client.force_authenticate(user=usuario)
        permisos = self.client.get('/api/auth/me/').data['permisos']
        self.assertTrue(all(permisos.values()))

    def test_token_real_de_django(self):
        get_user_model().objects.create_user(username='acceso_prueba', password='clave_segura_123')
        respuesta = self.client.post('/api/auth/token/', {
            'username': 'acceso_prueba', 'password': 'clave_segura_123'
        }, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('token', respuesta.data)

    def test_operador_no_puede_registrar_equipos(self):
        usuario = get_user_model().objects.create_user(username='operador_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Operador')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        respuesta = self.client.post('/api/equipos/', {'nombre':'Equipo prueba'}, format='json')
        self.assertEqual(respuesta.status_code, 403)

    def test_consulta_puede_listar_equipos(self):
        usuario = get_user_model().objects.create_user(username='consulta_prueba', password='clave_segura_123')
        grupo, _ = Group.objects.get_or_create(name='Consulta')
        usuario.groups.add(grupo)
        self.client.force_authenticate(user=usuario)
        respuesta = self.client.get('/api/equipos/')
        self.assertEqual(respuesta.status_code, 200)
