"""
Manejo de errores.

- 400: datos inválidos o regla de negocio incumplida.
- 401: no se envió token o es inválido.
- 403: el rol del usuario no permite la operación.
- 404: el recurso no existe.
- 405: método no permitido en ese recurso.
- 409: conflicto con el estado actual (registro protegido, acción repetida).
- 500: error interno. Nunca se devuelve la traza al cliente.
"""

import logging

from django.core.exceptions import ValidationError as ErrorValidacionDjango
from django.db import IntegrityError
from django.db.models import ProtectedError, RestrictedError

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


registro = logging.getLogger('bundestica')


class Conflicto(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'La operación entra en conflicto con el estado actual del recurso.'
    default_code = 'conflicto'


def manejador_excepciones(excepcion, contexto):

    if isinstance(excepcion, ErrorValidacionDjango):
        detalle = (
            excepcion.message_dict
            if hasattr(excepcion, 'error_dict')
            else {'detail': excepcion.messages}
        )
        return Response(detalle, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(excepcion, (ProtectedError, RestrictedError)):
        return Response(
            {'detail': 'No se puede eliminar: el registro está siendo usado por otros datos '
                       '(partidos, goles, inscripciones, etc.).'},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(excepcion, IntegrityError):
        return Response(
            {'detail': 'La operación viola una restricción de integridad (dato duplicado o '
                       'relación inválida).'},
            status=status.HTTP_409_CONFLICT,
        )

    respuesta = exception_handler(excepcion, contexto)

    if respuesta is None:
        registro.exception('Error no controlado en la API')
        return Response(
            {'detail': 'Error interno del servidor.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return respuesta
