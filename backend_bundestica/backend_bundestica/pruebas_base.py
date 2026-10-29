"""Utilidades compartidas por las pruebas automatizadas de todos los módulos."""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from equipos.models import Equipo, Jugador
from inscripciones.models import Inscripcion
from partidos.models import Partido
from torneos.models import Torneo
from torneos.servicios import poner_en_curso


HOY = timezone.localdate()


class PruebaBase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {}
        for rol in ('Administrador', 'Operador', 'Consulta'):
            grupo = Group.objects.create(name=rol)
            usuario = User.objects.create_user(username=rol.lower(), password='Prueba12345!')
            usuario.groups.add(grupo)
            cls.usuarios[rol] = usuario

    # ------------------------------------------------------------------ #
    def como(self, rol):
        """Autentica el cliente de pruebas con el token del rol indicado."""
        token, _ = Token.objects.get_or_create(user=self.usuarios[rol])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return self.client

    def crear_equipo(self, nombre, jugadores=5):
        equipo = Equipo.objects.create(nombre=nombre)
        for numero in range(1, jugadores + 1):
            Jugador.objects.create(
                nombre=f'{nombre} J{numero}',
                identificacion=f'ID{equipo.pk:04d}{numero:03d}',
                numero_camiseta=numero,
                equipo=equipo,
            )
        return equipo

    def crear_torneo(self, **datos):
        valores = {
            'nombre': 'Liga de Pruebas',
            'fecha_inicio': HOY - timedelta(days=10),
            'fecha_fin': HOY + timedelta(days=120),
            'maximo_equipos': 4,
            'minimo_jugadores_por_equipo': 5,
        }
        valores.update(datos)
        return Torneo.objects.create(**valores)

    def inscribir(self, torneo, *equipos):
        for equipo in equipos:
            Inscripcion.objects.create(torneo=torneo, equipo=equipo)

    def torneo_en_curso(self, cantidad_equipos=2, **datos):
        """Torneo lleno (cupo = cantidad de equipos) y por lo tanto EN_CURSO."""
        datos.setdefault('maximo_equipos', cantidad_equipos)
        torneo = self.crear_torneo(**datos)
        prefijo = datos.get('nombre', 'Liga')[:4]
        equipos = [self.crear_equipo(f'{prefijo} {letra}') for letra in 'ABCDEFGH'[:cantidad_equipos]]
        self.inscribir(torneo, *equipos)
        poner_en_curso(torneo)
        torneo.refresh_from_db()
        return torneo, equipos

    def crear_partido(self, torneo, local, visitante, fecha=None):
        return Partido.objects.create(
            torneo=torneo, equipo_local=local, equipo_visitante=visitante, fecha=fecha or HOY,
        )

    def registrar(self, partido, goles_local, goles_visitante, anotadores=None, rol='Operador'):
        datos = {'partido': partido.pk, 'goles_local': goles_local, 'goles_visitante': goles_visitante}
        if anotadores is not None:
            datos['anotadores'] = anotadores
        return self.como(rol).post('/api/goles/', datos, format='json')

    def goleador(self, equipo):
        return equipo.jugadores.order_by('numero_camiseta').first()
