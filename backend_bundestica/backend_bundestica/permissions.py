
from rest_framework.permissions import SAFE_METHODS, BasePermission


ADMINISTRADOR = 'Administrador'
OPERADOR = 'Operador'
CONSULTA = 'Consulta'

TODOS_LOS_ROLES = (ADMINISTRADOR, OPERADOR, CONSULTA)
SOLO_ADMINISTRADOR = (ADMINISTRADOR,)
ADMINISTRADOR_Y_OPERADOR = (ADMINISTRADOR, OPERADOR)


def roles_del_usuario(usuario):

    if not usuario or not usuario.is_authenticated:
        return set()

    roles = set(usuario.groups.values_list('name', flat=True))

    if usuario.is_superuser:
        roles.add(ADMINISTRADOR)

    return roles


class PermisoPorRol(BasePermission):

    message = 'Tu rol no tiene permiso para realizar esta operación.'

    def has_permission(self, request, view):

        # Sin autenticación DRF responde 401 automáticamente.
        if not request.user or not request.user.is_authenticated:
            return False

        roles_por_accion = getattr(view, 'roles_por_accion', {})
        accion = getattr(view, 'action', None)

        if accion in roles_por_accion:
            permitidos = roles_por_accion[accion]
        elif request.method in SAFE_METHODS:
            permitidos = getattr(view, 'roles_lectura', TODOS_LOS_ROLES)
        else:
            permitidos = getattr(view, 'roles_escritura', SOLO_ADMINISTRADOR)

        return bool(roles_del_usuario(request.user) & set(permitidos))
