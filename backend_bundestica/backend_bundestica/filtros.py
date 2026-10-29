from datetime import date

from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend

#Aqui lo que hacemos es definir los diferentes filtros que tenemos en el codigo.

def convertir_valor(nombre, valor, tipo):

    if tipo == 'entero':
        try:
            return int(valor)
        except (TypeError, ValueError):
            raise ValidationError({nombre: 'Debe ser un número entero.'})

    if tipo == 'fecha':
        try:
            return date.fromisoformat(valor)
        except (TypeError, ValueError):
            raise ValidationError({nombre: 'Debe tener formato AAAA-MM-DD.'})

    if tipo == 'booleano':
        valor_normalizado = str(valor).strip().lower()
        if valor_normalizado in ('true', '1', 'si', 'sí'):
            return True
        if valor_normalizado in ('false', '0', 'no'):
            return False
        raise ValidationError({nombre: 'Debe ser true o false.'})

    if tipo == 'mayusculas':
        return str(valor).strip().upper()

    return str(valor).strip()


class FiltroPorParametros(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):

        campos = getattr(view, 'campos_filtro', {})

        for nombre, (consulta, tipo) in campos.items():

            valor = request.query_params.get(nombre)

            if valor in (None, ''):
                continue

            valor_convertido = convertir_valor(nombre, valor, tipo)

            # Un filtro puede delegarse a un método de la vista
            # (por ejemplo, "equipo" en partidos: local O visitante).
            if consulta.startswith('metodo:'):
                metodo = getattr(view, consulta.split(':', 1)[1])
                queryset = metodo(queryset, valor_convertido)
            else:
                queryset = queryset.filter(**{consulta: valor_convertido})

        return queryset
