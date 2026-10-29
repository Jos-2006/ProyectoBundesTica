from rest_framework import serializers


class RelacionConOpciones(serializers.PrimaryKeyRelatedField):
    """
    Campo de relación que en el formulario (API navegable / OPTIONS) solo
    ofrece las opciones válidas (por ejemplo, torneos con inscripciones
    abiertas), pero acepta cualquier id existente para que la regla de
    negocio responda con un mensaje claro en vez de "clave inválida".
    """

    def __init__(self, opciones=None, **kwargs):
        self.opciones = opciones
        super().__init__(**kwargs)

    def get_choices(self, cutoff=None):
        consulta = self.opciones.all() if self.opciones is not None else self.get_queryset()
        if cutoff is not None:
            consulta = consulta[:cutoff]
        return {self.to_representation(item): self.display_value(item) for item in consulta}
