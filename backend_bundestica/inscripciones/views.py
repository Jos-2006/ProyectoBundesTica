from django.db import transaction
from django.db.models import Count, F

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from backend_bundestica.excepciones import Conflicto
from backend_bundestica.api import ConfiguracionApi
from backend_bundestica.permissions import SOLO_ADMINISTRADOR, TODOS_LOS_ROLES
from equipos.models import Equipo
from torneos.models import Torneo
from torneos.servicios import poner_en_curso

from .models import Inscripcion
from .serializers import InscripcionSerializer


class InscripcionViewSet(ConfiguracionApi, viewsets.ModelViewSet):
    """
    Inscripción de EQUIPOS en torneos (los jugadores van con su equipo).

    - Respeta el máximo de equipos del torneo.
    - Exige el mínimo de jugadores por equipo definido en el torneo.
    - Cuando se llena el cupo, el torneo pasa solo a EN_CURSO.

    GET /api/inscripciones/torneos_disponibles/[?equipo=ID]
        Torneos con inscripciones abiertas y cupo (si se manda ?equipo,
        solo aquellos donde ese equipo sí se puede inscribir).

    Filtros:   ?torneo=1  ?equipo=2  ?estado_torneo=INSCRIPCIONES
    Búsqueda:  ?search=texto (nombre de torneo o equipo)
    Orden:     ?ordering=fecha_inscripcion | equipo__nombre
    """

    serializer_class = InscripcionSerializer
    roles_lectura = TODOS_LOS_ROLES
    roles_escritura = SOLO_ADMINISTRADOR

    search_fields = ['torneo__nombre', 'equipo__nombre']
    ordering_fields = ['fecha_inscripcion', 'equipo__nombre', 'torneo__nombre']
    ordering = ['torneo_id', 'fecha_inscripcion']
    campos_filtro = {
        'torneo': ('torneo_id', 'entero'),
        'equipo': ('equipo_id', 'entero'),
        'estado_torneo': ('torneo__estado', 'mayusculas'),
    }

    def get_queryset(self):
        # Consulta ORM: select_related (FK) + prefetch_related (plantilla).
        return Inscripcion.objects.select_related('torneo', 'equipo').prefetch_related('equipo__jugadores')

    def bloquear_torneo(self, torneo_id):
        # Evita que dos inscripciones simultáneas superen el cupo.
        return Torneo.objects.select_for_update().get(pk=torneo_id)

    @transaction.atomic
    def perform_create(self, serializer):
        torneo = self.bloquear_torneo(serializer.validated_data['torneo'].pk)
        # Se vuelve a comprobar con el torneo bloqueado (carrera entre peticiones).
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            raise ValidationError({'torneo': 'Las inscripciones de este torneo están cerradas.'})
        if torneo.inscripciones.count() >= torneo.maximo_equipos:
            raise ValidationError({'torneo': 'El torneo ya alcanzó su máximo de equipos.'})
        serializer.save()

        # Se llenó el cupo: se cierran inscripciones y el torneo empieza.
        if torneo.inscripciones.count() == torneo.maximo_equipos:
            poner_en_curso(torneo)

    def create(self, request, *args, **kwargs):
        respuesta = super().create(request, *args, **kwargs)
        torneo = Torneo.objects.get(pk=respuesta.data['torneo'])
        inscritos = torneo.inscripciones.count()
        if torneo.estado == Torneo.Estado.EN_CURSO:
            mensaje = (f'Equipo inscrito. El torneo llenó su cupo ({inscritos}/{torneo.maximo_equipos}) '
                       f'y pasó a EN_CURSO: se deben jugar {torneo.cantidad_partidos} partidos.')
        else:
            mensaje = (f'Equipo inscrito ({inscritos}/{torneo.maximo_equipos}). '
                       f'Quedan {torneo.maximo_equipos - inscritos} cupo(s).')
        respuesta.data['estado_torneo'] = torneo.estado
        respuesta.data = {
            'mensaje': mensaje,
            'estado_torneo': torneo.estado,
            'inscripcion': respuesta.data,
        }
        return respuesta

    @action(detail=False, methods=['get'])
    def torneos_disponibles(self, request):
        torneos = (
            Torneo.objects.filter(estado=Torneo.Estado.INSCRIPCIONES)
            .annotate(inscritos=Count('inscripciones'))
            .filter(inscritos__lt=F('maximo_equipos'))
            .order_by('fecha_inicio', 'nombre')
        )

        equipo = None
        equipo_id = request.query_params.get('equipo')
        if equipo_id:
            if not equipo_id.isdigit():
                raise ValidationError({'equipo': 'Debe ser un número entero.'})
            equipo = Equipo.objects.annotate(cantidad=Count('jugadores')).filter(pk=equipo_id).first()
            if equipo is None:
                raise ValidationError({'equipo': 'El equipo no existe.'})
            torneos = torneos.exclude(inscripciones__equipo=equipo).filter(
                minimo_jugadores_por_equipo__lte=equipo.cantidad
            )

        datos = [
            {
                'id': t.id,
                'nombre': t.nombre,
                'fecha_inicio': t.fecha_inicio,
                'fecha_fin': t.fecha_fin,
                'vueltas': t.get_vueltas_display(),
                'equipos_inscritos': t.inscritos,
                'maximo_equipos': t.maximo_equipos,
                'cupos_disponibles': t.maximo_equipos - t.inscritos,
                'minimo_jugadores_por_equipo': t.minimo_jugadores_por_equipo,
            }
            for t in torneos
        ]
        return Response({
            'equipo': equipo.nombre if equipo else None,
            'cantidad': len(datos),
            'torneos': datos,
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def perform_update(self, serializer):
        self.bloquear_torneo(serializer.instance.torneo_id)
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, inscripcion):
        torneo = self.bloquear_torneo(inscripcion.torneo_id)
        if torneo.estado != Torneo.Estado.INSCRIPCIONES:
            raise Conflicto('No se puede retirar un equipo de un torneo que ya inició.')
        inscripcion.delete()
