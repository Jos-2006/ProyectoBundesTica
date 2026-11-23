// Los campos de cada pantalla se mantienen en este objeto.
// Cada módulo indica qué datos se piden y qué columnas aparecen.
// En vez de repetir formularios, cada módulo define aquí sus campos, valores iniciales y columnas.
export const configuracion = {

    // Equipos: nombre obligatorio y datos adicionales como entrenador y ciudad.
    equipos: { titulo:'Equipo', inicial:{nombre:'',entrenador:'',ciudad:''}, campos:[
        {nombre:'nombre',etiqueta:'Nombre del equipo'},{nombre:'entrenador',etiqueta:'Entrenador',obligatorio:false},{nombre:'ciudad',etiqueta:'Ciudad',obligatorio:false}],
        columnas:[['nombre','Nombre'],['entrenador','Entrenador'],['ciudad','Ciudad'],['cantidad_jugadores','Jugadores'],['torneos_ganados','Torneos ganados']] },

    // Jugadores: camiseta, posición y equipo se capturan con los tipos apropiados.
    jugadores: { titulo:'Jugador', inicial:{nombre:'',identificacion:'',numero_camiseta:1,posicion:'MED',equipo:''}, campos:[
        {nombre:'nombre',etiqueta:'Nombre'},{nombre:'identificacion',etiqueta:'Identificación'},{nombre:'numero_camiseta',etiqueta:'Camiseta (1 a 99)',tipo:'number',minimo:1,maximo:99},
        {nombre:'posicion',etiqueta:'Posición',tipo:'select',opciones:[{valor:'POR',etiqueta:'Portero'},{valor:'DEF',etiqueta:'Defensa'},{valor:'MED',etiqueta:'Mediocampista'},{valor:'DEL',etiqueta:'Delantero'}]},
        {nombre:'equipo',etiqueta:'Equipo',tipo:'select',numero:true}],
        columnas:[['nombre','Nombre'],['identificacion','Identificación'],['numero_camiseta','Camiseta'],['posicion_nombre','Posición'],['nombre_equipo','Equipo'],['goles_totales','Goles']] },

    // Torneos: los cupos, fechas, vueltas y puntos se mantienen de acuerdo con los campos del backend.
    torneos: { titulo:'Torneo', inicial:{nombre:'',descripcion:'',fecha_inicio:'',fecha_fin:'',maximo_equipos:8,minimo_jugadores_por_equipo:5,vueltas:1,puntos_victoria:3,puntos_empate:1,puntos_derrota:0}, campos:[
        {nombre:'nombre',etiqueta:'Nombre'},{nombre:'descripcion',etiqueta:'Descripción',tipo:'textarea',obligatorio:false,ancho:'col-md-12'},
        {nombre:'fecha_inicio',etiqueta:'Fecha de inicio',tipo:'date'},{nombre:'fecha_fin',etiqueta:'Fecha final',tipo:'date'},
        {nombre:'maximo_equipos',etiqueta:'Máximo de equipos (2-20)',tipo:'number',minimo:2,maximo:20},
        {nombre:'minimo_jugadores_por_equipo',etiqueta:'Mínimo de jugadores por equipo (1-30)',tipo:'number',minimo:1,maximo:30},
        {nombre:'vueltas',etiqueta:'Vueltas',tipo:'select',numero:true,opciones:[{valor:1,etiqueta:'Solo ida'},{valor:2,etiqueta:'Ida y vuelta'}]},
        {nombre:'puntos_victoria',etiqueta:'Puntos victoria',tipo:'number',minimo:0},{nombre:'puntos_empate',etiqueta:'Puntos empate',tipo:'number',minimo:0},{nombre:'puntos_derrota',etiqueta:'Puntos derrota',tipo:'number',minimo:0}],
        columnas:[['nombre','Nombre'],['estado_nombre','Estado'],['fecha_inicio','Inicio'],['fecha_fin','Final'],['equipos_inscritos','Inscritos'],['cupos_disponibles','Cupos'],['partidos_restantes','Partidos restantes'],['nombre_campeon','Campeón']] },

    // Una inscripción relaciona a un equipo con el torneo, no a jugadores individuales.
    inscripciones: {titulo:'Inscripción',inicial:{torneo:'',equipo:''},campos:[{nombre:'equipo',etiqueta:'Equipo',tipo:'select',numero:true},{nombre:'torneo',etiqueta:'Torneo con cupos disponibles',tipo:'select',numero:true}],
        columnas:[['nombre_torneo','Torneo'],['nombre_equipo','Equipo'],['estado_torneo','Estado'],['fecha_inscripcion','Fecha']]},

    // Para programar partidos se selecciona un torneo y los dos equipos que se enfrentarán.
    partidos: {titulo:'Partido',inicial:{torneo:'',equipo_local:'',equipo_visitante:'',fecha:''},campos:[
        {nombre:'torneo',etiqueta:'Torneo en curso',tipo:'select',numero:true},
        {nombre:'equipo_local',etiqueta:'Equipo local',tipo:'select',numero:true},
        {nombre:'equipo_visitante',etiqueta:'Equipo visitante',tipo:'select',numero:true},
        {nombre:'fecha',etiqueta:'Fecha del partido',tipo:'date'}],
        columnas:[['nombre_torneo','Torneo'],['nombre_local','Local'],['nombre_visitante','Visitante'],['fecha','Fecha'],['estado','Estado'],['marcador','Marcador']]}
};
