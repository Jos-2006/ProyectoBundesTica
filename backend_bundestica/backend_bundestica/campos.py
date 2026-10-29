from rest_framework import serializers


class RelacionConOpciones(serializers.PrimaryKeyRelatedField):
    """
    Esto nos va a permitir mostrar en el formulario solo opciones validas, pero antes de todo valida los id para brindar una respuesta clara
    """

    def __init__(self, opciones=None, **kwargs):
        self.opciones = opciones
        super().__init__(**kwargs)

    def get_choices(self, cutoff=None):
        consulta = self.opciones.all() if self.opciones is not None else self.get_queryset()
        if cutoff is not None:
            consulta = consulta[:cutoff]
        return {self.to_representation(item): self.display_value(item) for item in consulta}
