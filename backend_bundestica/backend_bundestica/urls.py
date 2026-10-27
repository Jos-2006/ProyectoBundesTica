from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from torneos.views import TorneoViewSet
from equipos.views import EquipoViewSet, JugadorViewSet
from inscripciones.views import TorneoEquipoViewSet, TorneoJugadorViewSet
from partidos.views import PartidoViewSet, GolViewSet
from estadisticas.views import TablaPosicionesView, TablaGoleadoresView

router = DefaultRouter()
router.register(r'torneos', TorneoViewSet)
router.register(r'equipos', EquipoViewSet)
router.register(r'jugadores', JugadorViewSet)
router.register(r'inscripciones-equipos', TorneoEquipoViewSet)
router.register(r'inscripciones-jugadores', TorneoJugadorViewSet)
router.register(r'partidos', PartidoViewSet)
router.register(r'goles', GolViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    path('api/', include(router.urls)),
    path('api/torneos/<int:torneo_id>/tabla-posiciones/', TablaPosicionesView.as_view(), name='tabla_posiciones'),
    path('api/torneos/<int:torneo_id>/tabla-goleadores/', TablaGoleadoresView.as_view(), name='tabla_goleadores'),
]