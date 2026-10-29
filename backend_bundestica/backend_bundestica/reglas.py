

from django.core.exceptions import ValidationError as ErrorDjango


def aplanar_mensajes(detalle):
    if isinstance(detalle, dict):
        mensajes = []
        for valor in detalle.values():
            mensajes.extend(aplanar_mensajes(valor))
        return mensajes
    if isinstance(detalle, (list, tuple)):
        mensajes = []
        for valor in detalle:
            mensajes.extend(aplanar_mensajes(valor))
        return mensajes
    return [str(detalle)]


def como_error_django(excepcion):
    return ErrorDjango(aplanar_mensajes(getattr(excepcion, 'detail', str(excepcion))))
