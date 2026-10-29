from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from equipos.models import Equipo
from torneos.models import Torneo
from torneos.servicios import poner_en_curso

from .models import Inscripcion, InscripcionPorTorneo


class CampoEquipos(forms.ModelMultipleChoiceField):
    def label_from_instance(self, equipo):
        return f'{equipo.nombre}  ({equipo.cantidad_jugadores} jugadores)'


class FormularioInscribirEquipos(forms.ModelForm):
    """Se marcan los equipos que participan en el torneo."""

    equipos = CampoEquipos(
        queryset=Equipo.objects.annotate(cantidad_jugadores=Count('jugadores')).order_by('nombre'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Equipos inscritos',
    )

    class Meta:
        model = InscripcionPorTorneo
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        torneo = self.instance
        campo = self.fields['equipos']
        campo.initial = list(torneo.inscripciones.values_list('equipo_id', flat=True))
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            campo.disabled = True
            campo.help_text = 'Las inscripciones de este torneo están cerradas.'
        else:
            campo.help_text = (
                f'Marque los equipos a inscribir. Máximo {torneo.maximo_equipos} equipos; cada uno '
                f'necesita al menos {torneo.minimo_jugadores_por_equipo} jugadores. Al completar el cupo '
                'el torneo pasa automáticamente a EN CURSO.'
            )

    def clean_equipos(self):
        torneo = self.instance
        equipos = list(self.cleaned_data['equipos'])
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            return equipos

        errores = []
        if len(equipos) > torneo.maximo_equipos:
            errores.append(
                f'Marcó {len(equipos)} equipos pero el torneo admite como máximo {torneo.maximo_equipos}.'
            )
        cortos = [e for e in equipos if e.cantidad_jugadores < torneo.minimo_jugadores_por_equipo]
        for equipo in cortos:
            errores.append(
                f'{equipo.nombre} tiene {equipo.cantidad_jugadores} jugador(es); el torneo exige al menos '
                f'{torneo.minimo_jugadores_por_equipo}.'
            )
        if errores:
            raise ValidationError(errores)
        return equipos


@admin.register(InscripcionPorTorneo)
class InscribirEquiposAdmin(admin.ModelAdmin):
    """Lista los torneos creados; adentro se marcan los equipos a inscribir."""

    form = FormularioInscribirEquipos
    list_display = ['nombre', 'estado', 'inscritos', 'cupos_disponibles',
                    'minimo_jugadores_por_equipo', 'vueltas', 'fecha_inicio', 'fecha_fin']
    list_filter = ['estado']
    search_fields = ['nombre']
    readonly_fields = ['nombre', 'estado', 'fecha_inicio', 'fecha_fin', 'maximo_equipos',
                       'minimo_jugadores_por_equipo', 'vueltas', 'siguiente_paso']
    fields = ['nombre', 'estado', 'fecha_inicio', 'fecha_fin', 'maximo_equipos',
              'minimo_jugadores_por_equipo', 'vueltas', 'equipos', 'siguiente_paso']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_inscritos=Count('inscripciones'))

    @admin.display(description='Inscritos')
    def inscritos(self, torneo):
        return f'{torneo.num_inscritos} / {torneo.maximo_equipos}'

    @admin.display(description='Cupos disponibles')
    def cupos_disponibles(self, torneo):
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            return 'Cerrado'
        return torneo.maximo_equipos - torneo.num_inscritos

    @admin.display(description='Siguiente paso')
    def siguiente_paso(self, torneo):
        if torneo.estado == Torneo.Estado.INSCRIPCIONES:
            return 'Inscriba equipos hasta llenar el cupo.'
        enlace = reverse('admin:torneos_torneo_change', args=[torneo.pk])
        return format_html(
            'Torneo {}. <a href="{}">Ver enfrentamientos por programar</a>',
            torneo.get_estado_display().lower(), enlace,
        )

    def has_add_permission(self, request):
        return False        # los torneos se crean en "Torneos"

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, torneo, form, change):
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            return
        torneo = Torneo.objects.select_for_update().get(pk=torneo.pk)
        marcados = {e.pk for e in form.cleaned_data['equipos']}
        actuales = set(torneo.inscripciones.values_list('equipo_id', flat=True))

        Inscripcion.objects.filter(torneo=torneo, equipo_id__in=actuales - marcados).delete()
        Inscripcion.objects.bulk_create(
            [Inscripcion(torneo=torneo, equipo_id=pk) for pk in marcados - actuales]
        )

        inscritos = len(marcados)
        if inscritos == torneo.maximo_equipos:
            poner_en_curso(torneo)
            messages.success(
                request,
                f'Cupo completo ({inscritos}/{torneo.maximo_equipos}). "{torneo.nombre}" pasó a EN CURSO: '
                f'se deben jugar {torneo.cantidad_partidos} partidos. Ya puede programarlos en Partidos.',
            )
        else:
            messages.info(
                request,
                f'Inscritos {inscritos}/{torneo.maximo_equipos}. '
                f'Quedan {torneo.maximo_equipos - inscritos} cupo(s).',
            )

    def message_user(self, request, message, *args, **kwargs):
        # Se omite el mensaje genérico "se modificó con éxito"; ya se muestra uno propio.
        if any(t in str(message) for t in ('con éxito', 'correctamente', 'successfully')):
            return
        super().message_user(request, message, *args, **kwargs)


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    """Listado de consulta. Para inscribir use "Inscribir equipos (por torneo)"."""

    list_display = ['torneo', 'equipo', 'estado_del_torneo', 'fecha_inscripcion']
    list_filter = ['torneo', 'torneo__estado']
    search_fields = ['torneo__nombre', 'equipo__nombre']

    @admin.display(description='Estado del torneo')
    def estado_del_torneo(self, inscripcion):
        return inscripcion.torneo.get_estado_display()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
