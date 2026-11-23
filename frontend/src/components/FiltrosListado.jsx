// Estos filtros permiten buscar y ordenar los registros de cada módulo.
// Las opciones del filtro se toman de los campos que ya usa el backend.
// Declaramos qué filtros acepta cada módulo para enviar esos parámetros a Django.
export const filtrosDisponibles = {
    equipos: [
        {nombre:'ciudad', etiqueta:'Ciudad'},
        {nombre:'con_jugadores', etiqueta:'Con jugadores', opciones:[['true','Sí'],['false','No']]}
    ],
    jugadores: [
        {nombre:'equipo', etiqueta:'Equipo', relacion:'equipos'},
        {nombre:'posicion', etiqueta:'Posición', opciones:[['POR','Portero'],['DEF','Defensa'],['MED','Mediocampista'],['DEL','Delantero']]},
    ],
    torneos: [
        {nombre:'estado', etiqueta:'Estado', opciones:[['INSCRIPCIONES','Inscripciones'],['EN_CURSO','En curso'],['FINALIZADO','Finalizado']]},
        {nombre:'con_cupos', etiqueta:'Con cupos', opciones:[['true','Sí'],['false','No']]},
        {nombre:'fecha_desde', etiqueta:'Desde', tipo:'date'},
        {nombre:'fecha_hasta', etiqueta:'Hasta', tipo:'date'}
    ],
    inscripciones: [
        {nombre:'torneo', etiqueta:'Torneo', relacion:'torneos'},
        {nombre:'equipo', etiqueta:'Equipo', relacion:'equipos'},
        {nombre:'estado_torneo', etiqueta:'Estado', opciones:[['INSCRIPCIONES','Inscripciones'],['EN_CURSO','En curso'],['FINALIZADO','Finalizado']]}
    ],
    partidos: [
        {nombre:'torneo', etiqueta:'Torneo', relacion:'torneos'},
        {nombre:'estado', etiqueta:'Estado', opciones:[['PROGRAMADO','Programado'],['FINALIZADO','Finalizado']]},
        {nombre:'fecha_desde', etiqueta:'Desde', tipo:'date'},
        {nombre:'fecha_hasta', etiqueta:'Hasta', tipo:'date'}
    ]
};
// Los valores guardados aquí corresponden a los campos de ordenamiento que recibe la API.
export const ordenesDisponibles = {
    equipos:[['nombre','Nombre A-Z'],['-nombre','Nombre Z-A'],['-cantidad_jugadores','Más jugadores']],
    jugadores:[['nombre','Nombre A-Z'],['numero_camiseta','Número camiseta'],['-goles_totales','Más goles']],
    torneos:[['nombre','Nombre'],['fecha_inicio','Inicio más antiguo'],['-fecha_inicio','Inicio más reciente']],
    inscripciones:[['-fecha_inscripcion','Más recientes'],['equipo__nombre','Nombre de equipo']],
    partidos:[['fecha','Fecha ascendente'],['-fecha','Fecha descendente']]
};
// El componente solo recoge lo que el usuario selecciona; la búsqueda real se realiza en el servidor.
export default function FiltrosListado({modulo, filtros, cambiar, busqueda, setBusqueda, ordenamiento, setOrdenamiento, opciones, limpiar}) {
    // Se muestran únicamente los controles que tienen sentido para el módulo actual.
    const filtrosModulo = filtrosDisponibles[modulo] || [];
    // El buscador, los selectores y el botón Limpiar comparten la misma distribución en todas las pantallas.
    return <div className="filter-panel row g-2 mb-3">
        <div className="col-md-4"><label className="form-label" htmlFor="buscar-listado">Buscar</label>
            <input id="buscar-listado" className="form-control" value={busqueda} onChange={e=>setBusqueda(e.target.value)} placeholder="Nombre o palabra clave" /></div>
        {filtrosModulo.map(campo=><div className="col-md-3" key={campo.nombre}>
            <label className="form-label" htmlFor={`filtro-${campo.nombre}`}>{campo.etiqueta}</label>
            {campo.opciones || campo.relacion ? <select className="form-select" id={`filtro-${campo.nombre}`} value={filtros[campo.nombre] || ''} onChange={e=>cambiar(campo.nombre,e.target.value)}>
                <option value="">Todos</option>
                {(campo.opciones || (opciones[campo.relacion] || []).map(x=>[x.id,x.nombre])).map(([valor,nombre])=><option key={valor} value={valor}>{nombre}</option>)}
            </select> : <input type={campo.tipo || 'text'} className="form-control" id={`filtro-${campo.nombre}`} value={filtros[campo.nombre] || ''} onChange={e=>cambiar(campo.nombre,e.target.value)} />}
        </div>)}
        <div className="col-md-3"><label className="form-label" htmlFor="orden-listado">Ordenar por</label>
            <select id="orden-listado" className="form-select" value={ordenamiento} onChange={e=>setOrdenamiento(e.target.value)}>
                <option value="">Orden predeterminado</option>
                {(ordenesDisponibles[modulo]||[]).map(([valor,nombre])=><option key={valor} value={valor}>{nombre}</option>)}
            </select></div>
        <div className="col-md-2 d-flex align-items-end"><button type="button" className="btn btn-outline-secondary filter-clear w-100" onClick={limpiar}><i className="bi bi-x-circle me-1"/>Limpiar</button></div>
    </div>;
}
