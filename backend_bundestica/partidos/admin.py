from urllib.parse import urlencode

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from rest_framework.exceptions import APIException

from backend_bundestica.reglas import como_error_django
from equipos.models import Equipo, Jugador
from estadisticas.servicios import recalcular_tabla
from torneos.models import Torneo

from . import servicios
from .models import Anotador, Partido, Resultado


def entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


# =========================================================================== #
# PARTIDOS: quién se enfrenta en cada torneo
# =========================================================================== #
class FormularioPartido(forms.ModelForm):

    class Meta:
        model = Partido
        fields = ['torneo', 'equipo_local', 'equipo_visitante', 'fecha']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'torneo' not in self.fields:      # vista de solo lectura (partido ya jugado)
            return

        # Solo torneos EN CURSO (con el cupo lleno) admiten partidos.
        torneos = Torneo.objects.filter(estado=Torneo.Estado.EN_CURSO)
        if self.instance.pk:
            torneos = torneos | Torneo.objects.filter(pk=self.instance.torneo_id)
        self.fields['torneo'].queryset = torneos
        self.fields['torneo'].help_text = 'Solo aparecen torneos EN CURSO (con el cupo de equipos lleno).'

        # Si ya se sabe el torneo, solo se ofrecen sus equipos inscritos.
        torneo_id = entero(self.data.get('torneo') or self.initial.get('torneo') or self.instance.torneo_id)
        if torneo_id:
            equipos = Equipo.objects.filter(inscripciones__torneo_id=torneo_id)
            ayuda = 'Solo equipos inscritos en este torneo.'
        else:
            equipos = Equipo.objects.filter(inscripciones__torneo__estado=Torneo.Estado.EN_CURSO).distinct()
            ayuda = 'Debe estar inscrito en el torneo elegido.'
        opciones = [('', '---------')] + [(e.pk, e.nombre) for e in equipos.order_by('nombre')]
        for campo in ('equipo_local', 'equipo_visitante'):
            # Se muestran solo los equipos válidos, pero se acepta cualquiera para
            # poder responder con un mensaje claro si no está inscrito.
            self.fields[campo].queryset = Equipo.objects.all()
            self.fields[campo].choices = opciones
            self.fields[campo].help_text = ayuda

    def clean(self):
        datos = super().clean()
        torneo, local, visitante, fecha = (datos.get(c) for c in self.Meta.fields)
        if self.instance.pk and self.instance.estado == Partido.Estado.FINALIZADO:
            raise ValidationError('Este partido ya tiene resultado; no se puede modificar.')
        if local and visitante and local == visitante:
            return datos        # lo informa la restricción "un equipo no juega contra sí mismo"
        if torneo and local and visitante and fecha:
            try:
                servicios.validar_partido(
                    torneo, local, visitante, fecha,
                    partido_actual=self.instance if self.instance.pk else None,
                )
            except APIException as error:
                raise como_error_django(error)
        return datos


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    form = FormularioPartido
    list_display = ['torneo', 'fecha', 'equipo_local', 'marcador', 'equipo_visitante',
                    'resultado_del_partido', 'goles']
    list_filter = ['torneo', 'estado']
    search_fields = ['equipo_local__nombre', 'equipo_visitante__nombre', 'torneo__nombre']
    date_hierarchy = 'fecha'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'torneo', 'equipo_local', 'equipo_visitante', 'resultado__ganador',
        )

    def get_changeform_initial_data(self, request):
        datos = super().get_changeform_initial_data(request)
        datos.setdefault('fecha', timezone.localdate())
        return datos

    def resultado_de(self, partido):
        return getattr(partido, 'resultado', None) if partido.estado == Partido.Estado.FINALIZADO else None

    @admin.display(description='Marcador')
    def marcador(self, partido):
        r = self.resultado_de(partido)
        return f'{r.goles_local} - {r.goles_visitante}' if r else 'vs'

    @admin.display(description='Resultado')
    def resultado_del_partido(self, partido):
        r = self.resultado_de(partido)
        return r.descripcion if r else 'Pendiente'

    @admin.display(description='Goles')
    def goles(self, partido):
        r = self.resultado_de(partido)
        if r:
            return format_html('<a href="{}">Ver / corregir</a>',
                               reverse('admin:partidos_resultado_change', args=[r.pk]))
        enlace = reverse('admin:partidos_resultado_add') + '?' + urlencode({'partido': partido.pk})
        return format_html('<a href="{}">Registrar goles</a>', enlace)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.estado == Partido.Estado.FINALIZADO:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.estado == Partido.Estado.FINALIZADO:
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        con_resultado = queryset.filter(estado=Partido.Estado.FINALIZADO).count()
        queryset.filter(estado=Partido.Estado.PROGRAMADO).delete()
        if con_resultado:
            messages.warning(request, f'{con_resultado} partido(s) con resultado no se eliminaron.')


# =========================================================================== #
# GOLES: se elige un partido, se pone el marcador y el sistema decide el ganador
# =========================================================================== #
class CampoPartido(forms.ModelChoiceField):
    def label_from_instance(self, partido):
        return f'{partido.torneo.nombre}: {partido.equipo_local.nombre} vs {partido.equipo_visitante.nombre} ({partido.fecha})'


class FormularioResultado(forms.ModelForm):

    partido = CampoPartido(queryset=Partido.objects.none())

    class Meta:
        model = Resultado
        fields = ['partido', 'goles_local', 'goles_visitante']
        labels = {'goles_local': 'Goles del local', 'goles_visitante': 'Goles del visitante'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'partido' not in self.fields:     # vista de solo lectura (torneo finalizado)
            return
        partidos = Partido.objects.select_related('torneo', 'equipo_local', 'equipo_visitante')
        if self.instance.pk:
            self.fields['partido'].queryset = partidos.filter(pk=self.instance.partido_id)
            self.fields['partido'].disabled = True
        else:
            self.fields['partido'].queryset = partidos.filter(
                estado=Partido.Estado.PROGRAMADO,
                torneo__estado=Torneo.Estado.EN_CURSO,
                fecha__lte=timezone.localdate(),
            ).order_by('torneo__nombre', 'fecha')
            self.fields['partido'].help_text = (
                'Solo aparecen partidos sin resultado, de torneos en curso, cuya fecha ya llegó.'
            )

    def clean(self):
        datos = super().clean()
        partido = datos.get('partido')
        goles_local, goles_visitante = datos.get('goles_local'), datos.get('goles_visitante')
        if partido is None or goles_local is None or goles_visitante is None:
            return datos

        if self.instance.pk:
            if partido.torneo.estado != Torneo.Estado.EN_CURSO:
                raise ValidationError('El torneo ya finalizó; sus resultados no se pueden modificar.')
        elif partido.estado == Partido.Estado.FINALIZADO:
            raise ValidationError('Este partido ya tiene resultado.')

        try:
            servicios.validar_marcador(partido, goles_local, goles_visitante, None)
        except APIException as error:
            raise como_error_django(error)
        return datos


class FormsetGoleadores(BaseInlineFormSet):
    """Si se detallan goleadores, deben ser de los dos equipos y cuadrar con el marcador."""

    def clean(self):
        super().clean()
        resultado = self.instance
        partido = getattr(resultado, 'partido', None) if resultado.partido_id else None
        if partido is None or any(self.errors) or None in (resultado.goles_local, resultado.goles_visitante):
            return

        filas = [
            f.cleaned_data for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('jugador')
        ]
        if not filas:
            return

        conteo = {partido.equipo_local_id: 0, partido.equipo_visitante_id: 0}
        for fila in filas:
            jugador = fila['jugador']
            if jugador.equipo_id not in conteo:
                raise ValidationError(f'{jugador.nombre} no juega en ninguno de los dos equipos del partido.')
            if fila.get('tipo') == Anotador.Tipo.AUTOGOL:
                otro = [pk for pk in conteo if pk != jugador.equipo_id][0]
                conteo[otro] += 1
            else:
                conteo[jugador.equipo_id] += 1

        indicado = (resultado.goles_local, resultado.goles_visitante)
        detallado = (conteo[partido.equipo_local_id], conteo[partido.equipo_visitante_id])
        if indicado != detallado:
            raise ValidationError(
                f'Los goleadores no cuadran con el marcador: el marcador es {indicado[0]}-{indicado[1]} '
                f'pero los goleadores suman {detallado[0]}-{detallado[1]} (un autogol suma al rival). '
                'Corrija la lista o déjela vacía.'
            )


class CampoJugador(forms.ModelChoiceField):
    def label_from_instance(self, jugador):
        return f'{jugador.nombre} #{jugador.numero_camiseta} ({jugador.equipo.nombre})'


class GoleadoresEnLinea(admin.TabularInline):
    model = Anotador
    formset = FormsetGoleadores
    fields = ['jugador', 'minuto', 'tipo']
    extra = 3

    def get_formset(self, request, obj=None, **kwargs):
        self.partido_actual = obj.partido if obj else Partido.objects.filter(
            pk=entero(request.GET.get('partido') or request.POST.get('partido'))
        ).first()
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'jugador' and hasattr(campo.widget, 'can_add_related'):
            # Sin los íconos de editar/añadir/borrar/ver jugador en cada fila.
            campo.widget.can_add_related = campo.widget.can_change_related = False
            campo.widget.can_delete_related = campo.widget.can_view_related = False
        return campo

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'jugador':
            jugadores = Jugador.objects.select_related('equipo').order_by('equipo__nombre', 'numero_camiseta')
            partido = getattr(self, 'partido_actual', None)
            if partido:
                jugadores = jugadores.filter(equipo_id__in=[partido.equipo_local_id, partido.equipo_visitante_id])
            return CampoJugador(queryset=jugadores, label='Jugador')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    form = FormularioResultado
    inlines = [GoleadoresEnLinea]
    list_display = ['partido_jugado', 'torneo', 'marcador', 'resultado', 'ganador', 'perdedor']
    list_filter = ['partido__torneo', 'empate']
    readonly_fields = ['resultado_calculado']

    def get_fields(self, request, obj=None):
        campos = ['partido', 'goles_local', 'goles_visitante']
        return campos + (['resultado_calculado'] if obj else [])

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'partido__torneo', 'partido__equipo_local', 'partido__equipo_visitante', 'ganador', 'perdedor',
        )

    @admin.display(description='Partido')
    def partido_jugado(self, r):
        return f'{r.partido.equipo_local.nombre} vs {r.partido.equipo_visitante.nombre} ({r.partido.fecha})'

    @admin.display(description='Torneo')
    def torneo(self, r):
        return r.partido.torneo.nombre

    @admin.display(description='Marcador')
    def marcador(self, r):
        return f'{r.goles_local} - {r.goles_visitante}'

    @admin.display(description='Resultado')
    def resultado(self, r):
        return r.descripcion

    @admin.display(description='Resultado')
    def resultado_calculado(self, r):
        if r.empate:
            return 'Empatado'
        return f'Ganó {r.ganador.nombre} — Perdió {r.perdedor.nombre}'

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.partido.torneo.estado != Torneo.Estado.EN_CURSO:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.partido.torneo.estado != Torneo.Estado.EN_CURSO:
            return False
        return super().has_delete_permission(request, obj)

    # --- Guardado ------------------------------------------------------- #
    def save_model(self, request, resultado, form, change):
        partido = resultado.partido
        resultado.ganador, resultado.perdedor, resultado.empate = servicios.calcular_ganador(
            partido, resultado.goles_local, resultado.goles_visitante,
        )
        resultado.save()
        if partido.estado != Partido.Estado.FINALIZADO:
            partido.estado = Partido.Estado.FINALIZADO
            partido.save(update_fields=['estado'])

    def save_formset(self, request, form, formset, change):
        partido = form.instance.partido
        for goleador in formset.save(commit=False):
            if goleador.tipo == Anotador.Tipo.AUTOGOL:
                goleador.equipo_id = (partido.equipo_visitante_id
                                      if goleador.jugador.equipo_id == partido.equipo_local_id
                                      else partido.equipo_local_id)
            else:
                goleador.equipo_id = goleador.jugador.equipo_id
            goleador.save()
        for eliminado in formset.deleted_objects:
            eliminado.delete()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        resultado = form.instance
        recalcular_tabla(resultado.partido.torneo)
        campeon = servicios.cerrar_torneo_si_termino(resultado.partido.torneo_id)

        p = resultado.partido
        messages.success(
            request,
            f'{p.equipo_local.nombre} {resultado.goles_local} - {resultado.goles_visitante} '
            f'{p.equipo_visitante.nombre}: {resultado.descripcion}.',
        )
        if campeon is not None:
            messages.success(
                request,
                f'¡Todos los equipos se enfrentaron! El torneo "{p.torneo.nombre}" terminó. '
                f'Campeón: {campeon.nombre}.',
            )

    def message_user(self, request, message, *args, **kwargs):
        if any(t in str(message) for t in ('con éxito', 'correctamente', 'successfully')):
            return
        super().message_user(request, message, *args, **kwargs)

    # --- Eliminación: el partido vuelve a quedar pendiente --------------- #
    def delete_model(self, request, resultado):
        servicios.eliminar_resultado(resultado)

    def delete_queryset(self, request, queryset):
        for resultado in queryset.filter(partido__torneo__estado=Torneo.Estado.EN_CURSO):
            servicios.eliminar_resultado(resultado)
