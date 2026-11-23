"""Identidad y permisos del usuario para mostrar las acciones correctas en React.

Esta vista es de solo lectura. No cambia reglas, modelos ni permisos existentes.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import (
    ADMINISTRADOR_Y_OPERADOR, SOLO_ADMINISTRADOR,
    roles_del_usuario,
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    roles = roles_del_usuario(request.user)
    administrador = bool(roles.intersection(SOLO_ADMINISTRADOR))
    operador = bool(roles.intersection(ADMINISTRADOR_Y_OPERADOR))
    return Response({
        'username': request.user.get_username(),
        'roles': sorted(roles),
        'permisos': {
            'equipos': administrador,
            'jugadores': administrador,
            'torneos': administrador,
            'inscripciones': administrador,
            'partidos': operador,
            'resultados': operador,
        },
    })
