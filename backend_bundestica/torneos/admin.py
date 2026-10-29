from urllib.parse import urlencode

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from rest_framework.exceptions import APIException

from backend_bundestica.reglas import aplanar_mensajes

from .models import Torneo
from .servicios import enfrentamientos_pendientes, poner_en_curso


def enlace_programar(torneo, local=None, visitante=None):
    parametros = {'torneo': torneo.pk}
    if local is not None:
        parametros.update(equipo_local=local.pk, equipo_visitante=visitante.pk)
    return reverse('admin:partidos_partido_add') + '?' + urlencode(parametros)


@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado', 'fecha_inicio', 'fecha_fin', 'vueltas',
                    'inscritos', 'avance', 'campeon']
    list_filter = ['estado', 'vueltas']
    search_fields = ['nombre']
    actions = ['iniciar_torneos']

    campos_editables = [
        'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'maximo_equipos',
        'minimo_jugadores_por_equipo', 'vueltas', 'puntos_victoria', 'puntos_empate', 'puntos_derrota',
    ]
    campos_calculados = ['estado', 'cantidad_partidos', 'campeon', 'equipos_del_torneo', 'partidos_pendientes']

    def get_fields(self, request, obj=None):
        return self.campos_editables + (self.campos_calculados if obj else [])

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.estado != Torneo.Estado.INSCRIPCIONES:
            return self.campos_editables + self.campos_calculados
        return self.campos_calculados

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campeon').annotate(
            num_inscritos=Count('inscripciones', distinct=True),
            num_jugados=Count('partidos', filter=Q(partidos__estado='FINALIZADO'), distinct=True),
        )

    @admin.display(description='Inscritos')
    def inscritos(self, torneo):
        return f'{torneo.num_inscritos} / {torneo.maximo_equipos}'

    @admin.display(description='Partidos jugados')
    def avance(self, torneo):
        if torneo.estado == Torneo.Estado.INSCRIPCIONES:
            return '—'
        return f'{torneo.num_jugados} / {torneo.cantidad_partidos}'

    @admin.display(description='Equipos inscritos')
    def equipos_del_torneo(self, torneo):
        equipos = [i.equipo.nombre for i in torneo.inscripciones.select_related('equipo')]
        enlace = reverse('admin:inscripciones_inscripcionportorneo_change', args=[torneo.pk])
        texto = ', '.join(equipos) or 'Ninguno todavía'
        return format_html('{}<br><a href="{}">Inscribir / ver equipos</a>', texto, enlace)

    @admin.display(description='Enfrentamientos por programar')
    def partidos_pendientes(self, torneo):
        if torneo.estado != Torneo.Estado.EN_CURSO:
            return 'Se habilitan cuando el torneo está EN CURSO (al llenarse el cupo).'
        pendientes = enfrentamientos_pendientes(torneo)
        if not pendientes:
            return 'Todos los enfrentamientos ya están programados.'
        return format_html_join(
            format_html('<br>'), '{} (local) vs {} — <a href="{}">Programar</a>',
            ((l.nombre, v.nombre, enlace_programar(torneo, l, v)) for l, v in pendientes),
        )

    def save_model(self, request, torneo, form, change):
        super().save_model(request, torneo, form, change)
        inscritos = torneo.inscripciones.count()
        if torneo.estado == Torneo.Estado.INSCRIPCIONES and inscritos >= 2 and inscritos == torneo.maximo_equipos:
            poner_en_curso(torneo)
            messages.success(request, f'El torneo quedó lleno y pasó a EN CURSO: '
                                      f'se deben jugar {torneo.cantidad_partidos} partidos.')

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.estado != Torneo.Estado.INSCRIPCIONES:
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description='Iniciar torneo sin llenar el cupo (mínimo 2 equipos)')
    def iniciar_torneos(self, request, queryset):
        for torneo in queryset:
            if torneo.estado != Torneo.Estado.INSCRIPCIONES:
                messages.warning(request, f'"{torneo.nombre}" ya estaba iniciado.')
                continue
            try:
                with transaction.atomic():
                    poner_en_curso(Torneo.objects.select_for_update().get(pk=torneo.pk))
                messages.success(request, f'"{torneo.nombre}" pasó a EN CURSO.')
            except APIException as error:
                messages.error(request, f'"{torneo.nombre}": ' + ' '.join(aplanar_mensajes(error.detail)))
