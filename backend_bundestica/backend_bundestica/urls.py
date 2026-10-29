from django.contrib import admin
from django.urls import include, path

from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from equipos.views import EquipoViewSet, JugadorViewSet
from estadisticas.views import EstadisticaTorneoViewSet, PartidoJugadoViewSet
from inscripciones.views import InscripcionViewSet
from partidos.views import PartidoViewSet, ResultadoViewSet
from torneos.views import TorneoViewSet


enrutador = DefaultRouter()

enrutador.register('equipos', EquipoViewSet, basename='equipo')
enrutador.register('jugadores', JugadorViewSet, basename='jugador')
enrutador.register('torneos', TorneoViewSet, basename='torneo')
enrutador.register('inscripciones', InscripcionViewSet, basename='inscripcion')
enrutador.register('partidos', PartidoViewSet, basename='partido')
enrutador.register('goles', ResultadoViewSet, basename='gol')
enrutador.register('estadisticas/partidos', PartidoJugadoViewSet, basename='estadistica-partido')
enrutador.register('estadisticas/torneos', EstadisticaTorneoViewSet, basename='estadistica-torneo')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', obtain_auth_token, name='obtener_token'),
    path('api/', include(enrutador.urls)),
]
