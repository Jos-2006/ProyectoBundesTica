"""
Aqui se configura una clase base de todas las vistas, permisos, paginación y manejo de errores.
"""

from rest_framework.filters import OrderingFilter, SearchFilter

from .excepciones import manejador_excepciones
from .filtros import FiltroPorParametros
from .paginacion import PaginacionEstandar
from .permissions import PermisoPorRol


class ConfiguracionApi:

    permission_classes = [PermisoPorRol]
    pagination_class = PaginacionEstandar
    filter_backends = [FiltroPorParametros, SearchFilter, OrderingFilter]

    def get_exception_handler(self):
        return manejador_excepciones
