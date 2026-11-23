// Esta pantalla se reutiliza en los cinco módulos con CRUD.
import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { getError } from '../api/client.js';
import { configuracion } from '../configuracion.js';
import FormRegistro from '../components/FormRegistro.jsx';
import FiltrosListado from '../components/FiltrosListado.jsx';
import { consultarPagina } from '../services/servicioBase.js';
import { listEquipos, addEquipo, updateEquipo, deleteEquipo } from '../services/equipoService.js';
import { listJugadores, addJugador, updateJugador, deleteJugador } from '../services/jugadorService.js';
import { listTorneos, addTorneo, updateTorneo, deleteTorneo } from '../services/torneoService.js';
import { listInscripciones, addInscripcion, updateInscripcion, deleteInscripcion } from '../services/inscripcionService.js';
import { listPartidos, addPartido, updatePartido, deletePartido } from '../services/partidoService.js';
import { iniciarTorneo, torneosDisponibles, tablaTorneo, enfrentamientosTorneo } from '../services/consultaService.js';

// Relacionamos cada módulo con sus cuatro operaciones: listar, crear, actualizar y eliminar.
const servicios = {
    equipos:[listEquipos,addEquipo,updateEquipo,deleteEquipo],
    jugadores:[listJugadores,addJugador,updateJugador,deleteJugador],
    torneos:[listTorneos,addTorneo,updateTorneo,deleteTorneo],
    inscripciones:[listInscripciones,addInscripcion,updateInscripcion,deleteInscripcion],
    partidos:[listPartidos,addPartido,updatePartido,deletePartido]
};

// Las listas vacías evitan errores mientras se cargan los selectores.
const inicialOpciones={equipos:[],torneos:[],inscripciones:[]};

// Las rutas de cada recurso están concentradas aquí para no escribirlas en varios métodos.
const rutas={equipos:'/equipos/',jugadores:'/jugadores/',torneos:'/torneos/',inscripciones:'/inscripciones/',partidos:'/partidos/'};

// El texto del encabezado es una guía rápida para el usuario de cada pantalla.
const ayudaModulos = {
    equipos:['bi-shield-fill','Organiza los equipos participantes y sus entrenadores.'],
    jugadores:['bi-people-fill','Registra jugadores y asígnalos a su equipo.'],
    torneos:['bi-trophy-fill','Crea torneos y revisa sus posiciones y encuentros.'],
    inscripciones:['bi-person-check-fill','Inscríbe equipos completos en los torneos disponibles.'],
    partidos:['bi-calendar2-event-fill','Programa los encuentros de los torneos en curso.']
};

// Una sola página maneja los cinco CRUD; la propiedad modulo indica qué datos debe utilizar.
export default function PaginaRegistros({modulo}) {

    // Tomamos los campos, títulos y columnas definidos para ese módulo.
    const config=configuracion[modulo];
    const {puedeEditar} = useAuth();

    // El rol del usuario decide si aparecen las acciones de edición, aunque Django sigue validando los permisos.
    const puedeEscribir = puedeEditar(modulo);

    // Guardamos la tabla y el registro seleccionado para editar.
    const [registros,setRegistros]=useState([]);const [editando,setEditando]=useState(null);
    const [opciones,setOpciones]=useState(inicialOpciones);

    // La búsqueda y los filtros se mantienen en estado para repetir la consulta al cambiarlos.
    const [busqueda,setBusqueda]=useState('');const [filtros,setFiltros]=useState({});
    const [ordenamiento,setOrdenamiento]=useState(''); const [pagina,setPagina]=useState(1);

    // La API informa el total y los enlaces de página anterior y siguiente.
    const [total,setTotal]=useState(0); const [siguiente,setSiguiente]=useState(null);
    const [anterior,setAnterior]=useState(null); const [cargando,setCargando]=useState(true);

    // Estos estados permiten desactivar botones y mostrar mensajes de éxito o error.
    const [guardando,setGuardando]=useState(false);const [error,setError]=useState('');const [exito,setExito]=useState('');

    // Aquí conservamos el torneo seleccionado al consultar su tabla de posiciones.
    const [seleccion,setSeleccion]=useState(null);const [tabla,setTabla]=useState(null);
    const [pendientes,setPendientes]=useState(null);

    // Este registro se utiliza para consultar los jugadores que pertenecen a una inscripción.
    const [plantilla,setPlantilla]=useState(null);

    // Guardamos el equipo seleccionado para pedir a Django sus torneos disponibles.
    const [equipoInscripcion,setEquipoInscripcion]=useState('');

    // Sirve para mostrar solo equipos inscritos en el torneo elegido al programar un partido.
    const [torneoPartido,setTorneoPartido]=useState('');

    // Traemos únicamente la página que el usuario está viendo.
    // Esta función construye la consulta de la página actual y actualiza la tabla con la respuesta del servidor.
    const recargar=useCallback(async()=>{
        setCargando(true);setError('');
        try {

            // Enviamos filtros, número de página y cantidad de registros como parámetros de la API.
            const parametros={...filtros,page:pagina,page_size:10};

            // La búsqueda se manda solo cuando hay texto; se eliminan espacios sobrantes.
            if(busqueda.trim()) parametros.search=busqueda.trim();
            if(ordenamiento) parametros.ordering=ordenamiento;

            // consultarPagina también devuelve el total y la información necesaria para los botones Anterior y Siguiente.
            const datos=await consultarPagina(rutas[modulo],parametros);
            setRegistros(datos.registros);setTotal(datos.total);
            setSiguiente(datos.siguiente);setAnterior(datos.anterior);
        } catch(e){setError(getError(e));}finally{setCargando(false);}
    },[modulo, filtros, pagina, busqueda, ordenamiento]);

    // Los selectores necesitan las opciones de equipos, torneos e inscripciones.
    // Los desplegables se llenan con equipos, torneos e inscripciones existentes; no se usan arreglos simulados.
    const cargarOpciones=useCallback(async()=>{
        try {
            const equipos = await listEquipos();

            // Para nuevas inscripciones se solicitan solamente torneos que el backend considera disponibles.
            const torneos = modulo==='inscripciones' ? await torneosDisponibles() : await listTorneos();

            // Al programar un encuentro también necesitamos conocer qué equipos están inscritos.
            const inscripciones = modulo==='partidos' ? await listInscripciones() : [];
            setOpciones({equipos,torneos,inscripciones});
        } catch(e){setError(getError(e));}
    },[modulo]);

    // Los cambios en página, búsqueda, orden o filtros hacen que React vuelva a consultar los registros.
    useEffect(()=>{recargar();},[recargar]);

    // Al cambiar de módulo se recargan los selectores y se limpia cualquier edición que quedó abierta.
    useEffect(()=>{cargarOpciones();setEditando(null);setSeleccion(null);setTabla(null);setPendientes(null);setPlantilla(null);},[cargarOpciones]);

    useEffect(()=>{

        // El cambio de equipo solo se consulta cuando estamos en Inscripciones y existe un equipo seleccionado.
        if(modulo!=='inscripciones'||!equipoInscripcion)return;
        torneosDisponibles(equipoInscripcion).then(torneos=>setOpciones(a=>({...a,torneos}))).catch(e=>setError(getError(e)));
    },[modulo,equipoInscripcion]);

    // Volvemos a la página uno para no dejar al usuario en una página que ya no corresponde.
    function cambiarFiltro(nombre, valor){setPagina(1);setFiltros(actual=>({...actual,[nombre]:valor}));}

    // El texto nuevo se aplica a la siguiente petición de búsqueda.
    function cambiarBusqueda(valor){setPagina(1);setBusqueda(valor);}

    // La ordenación queda guardada y se envía como ordering al servidor.
    function cambiarOrden(valor){setPagina(1);setOrdenamiento(valor);}

    // Restauramos los controles y solicitamos de nuevo el listado general.
    function limpiarFiltros(){setPagina(1);setFiltros({});setBusqueda('');setOrdenamiento('');}

    // Los equipos y torneos ofrecidos por cada selector dependen del módulo y de las relaciones existentes.
    const opcionesCampos={
        equipo:opciones.equipos,

        // Equipo local: filtramos los equipos que pertenecen al torneo elegido.
        equipo_local: modulo==='partidos' ? opciones.equipos.filter(e=>opciones.inscripciones.some(i=>Number(i.torneo)===Number(torneoPartido || editando?.torneo) && Number(i.equipo)===Number(e.id))) : [],

        // Equipo visitante: se aplica la misma comprobación de inscripción.
        equipo_visitante: modulo==='partidos' ? opciones.equipos.filter(e=>opciones.inscripciones.some(i=>Number(i.torneo)===Number(torneoPartido || editando?.torneo) && Number(i.equipo)===Number(e.id))) : [],

        // Al editar una inscripción conservamos su torneo; al programar partidos solo usamos torneos en curso.
        torneo: modulo==='inscripciones'&&editando
            ? [{id:editando.torneo,nombre:editando.nombre_torneo},...opciones.torneos.filter(t=>t.id!==editando.torneo)]
            : modulo==='partidos'
                ? opciones.torneos.filter(t=>t.estado==='EN_CURSO')
                : opciones.torneos
    };

    // Guardamos desde el mismo formulario, ya sea un registro nuevo o editado.
    // Se usa la misma acción para crear y editar. El método elegido depende de si hay un registro seleccionado.
    async function guardar(datos){setGuardando(true);setError('');setExito('');
        try{

            // El torneo de una inscripción ya existente no se vuelve a enviar porque esa relación no debe alterarse.
            if(editando){if(modulo==='inscripciones')delete datos.torneo;await servicios[modulo][2](editando.id,datos);setExito('Registro actualizado correctamente.');}
            else{await servicios[modulo][1](datos);setExito('Registro creado correctamente.');}

            // Tras guardar se cierran los formularios y se actualizan tanto la tabla como los selectores.
            setEditando(null);setEquipoInscripcion('');setTorneoPartido('');await recargar();await cargarOpciones();return true;
        }catch(e){setError(getError(e));return false;}finally{setGuardando(false);}
    }

    // Pedimos confirmación antes de eliminar para evitar clics accidentales.
    // Antes del DELETE se solicita confirmación y después se actualiza la página visible.
    async function borrar(registro){if(!window.confirm(`¿Eliminar el registro #${registro.id}?`))return;
        setError('');setExito('');try{await servicios[modulo][3](registro.id);setExito('Registro eliminado.');

            // Si se borró el último registro de una página posterior, regresamos a la anterior.
            if (registros.length===1&&pagina>1) setPagina(n=>n-1);
            else await recargar();
            await cargarOpciones();}catch(e){setError(getError(e));}
    }

    // Esta acción solo se usa cuando el usuario puede iniciar el torneo.
    // Esta acción envía al backend la orden de iniciar un torneo después de pedir confirmación.
    async function comenzar(torneo){if(!window.confirm(`¿Iniciar el torneo ${torneo.nombre}? Se cerrarán las inscripciones.`))return;
        try{const datos=await iniciarTorneo(torneo.id);setExito(datos.mensaje||'Torneo iniciado.');await recargar();await cargarOpciones();}catch(e){setError(getError(e));}
    }

    // Consultamos la tabla de posiciones del torneo seleccionado sin alterar los datos.
    async function verTabla(torneo){try{setTabla(await tablaTorneo(torneo.id));setSeleccion(torneo);}catch(e){setError(getError(e));}}

    // Pedimos a Django los enfrentamientos que todavía faltan por programar.
    async function verPendientes(torneo){try{setPendientes(await enfrentamientosTorneo(torneo.id));setSeleccion(torneo);}catch(e){setError(getError(e));}}

    // Debajo del encabezado se muestran mensajes, formulario, filtros y listado según el módulo y el perfil.
    return <>
        <div className="module-header"><div className="module-header-icon"><i className={`bi ${ayudaModulos[modulo][0]}`}/></div><div>
            
            <h1>{modulo[0].toUpperCase()+modulo.slice(1)}</h1>
            <p>{ayudaModulos[modulo][1]}</p>
        </div></div>
        {modulo==='inscripciones'&&<div className="module-note"><i className="bi bi-info-circle-fill"/><span>Solo puede inscribir equipos a torneos que esten en curso, y que cumpla con las reglas del torneo.</span></div>}
        {modulo==='torneos'&&<div className="module-note"><i className="bi bi-info-circle-fill"/><span>Los torneos empiezan con inscripciones abiertas.este iniciara cuando se llenen los cupos para los equipos.</span></div>}
        {modulo==='partidos'&&<div className="module-note"><i className="bi bi-info-circle-fill"/><span>Elige un torneo en curso y dos equipos inscritos para programar el partido.</span></div>}
        {error&&<div className="alert alert-danger">{error}</div>}{exito&&<div className="alert alert-success">{exito}</div>}
        {!puedeEscribir && <div className="alert alert-secondary">Estás en modo consulta. Puedes ver la información, pero no realizar cambios.</div>}
        {puedeEscribir && <div onChangeCapture={e=>{if(modulo==='inscripciones'&&e.target.name==='equipo')setEquipoInscripcion(e.target.value);if(modulo==='partidos'&&e.target.name==='torneo')setTorneoPartido(e.target.value);}}>
            <FormRegistro key={modulo} titulo={config.titulo} inicial={config.inicial} campos={config.campos}
                registro={editando} opciones={opcionesCampos} guardar={guardar} cancelar={()=>setEditando(null)} guardando={guardando}/>
        </div>}
        <section className="card record-list-card border-0 shadow-sm"><div className="card-body p-4">
            <div className="d-flex justify-content-between align-items-center gap-2 flex-wrap mb-3"><div className="panel-heading mb-0"><span className="panel-heading-icon"><i className="bi bi-list-ul"/></span><div><h2>Registros</h2><small>{total} encontrados</small></div></div>
                <button className="btn btn-outline-primary" onClick={recargar}><i className="bi bi-arrow-clockwise me-2"/>Actualizar</button>
            </div>
            <FiltrosListado modulo={modulo} filtros={filtros} cambiar={cambiarFiltro} busqueda={busqueda}
                setBusqueda={cambiarBusqueda} ordenamiento={ordenamiento} setOrdenamiento={cambiarOrden}
                opciones={opciones} limpiar={limpiarFiltros}/>
            {cargando?<p role="status" className="text-secondary"><i className="bi bi-arrow-repeat me-2"/>Cargando registros...</p>:<div className="table-responsive"><table className="table table-hover align-middle"><thead className="table-light"><tr>
                <th>ID</th>{config.columnas.map(([clave,nombre])=><th key={clave}>{nombre}</th>)}<th>Acciones</th></tr></thead>
                <tbody>{registros.map(registro=><tr key={registro.id}><td>#{registro.id}</td>{config.columnas.map(([clave])=><td key={clave}>{registro[clave]===null||registro[clave]===undefined?'—':(['estado','estado_nombre','estado_torneo'].includes(clave) ? <span className="status-badge" data-estado={registro.estado || registro.estado_torneo || registro[clave]}>{String(registro[clave]).replaceAll('_',' ')}</span> : String(registro[clave]))}</td>)}
                <td><div className="d-flex gap-1 flex-wrap">
                    {puedeEscribir&&(modulo!=='torneos'||registro.estado==='INSCRIPCIONES')&&(modulo!=='partidos'||registro.estado==='PROGRAMADO')&&(modulo!=='inscripciones'||registro.estado_torneo==='INSCRIPCIONES')&&<button className="btn btn-outline-primary btn-sm" onClick={()=>{setEditando(registro);if(modulo==='partidos')setTorneoPartido(registro.torneo);window.scrollTo(0,0);}}><i className="bi bi-pencil-square me-1"/>Editar</button>}
                    {puedeEscribir&&(modulo!=='torneos'||registro.estado==='INSCRIPCIONES')&&(modulo!=='partidos'||registro.estado==='PROGRAMADO')&&(modulo!=='inscripciones'||registro.estado_torneo==='INSCRIPCIONES')&&<button className="btn btn-outline-danger btn-sm" onClick={()=>borrar(registro)}><i className="bi bi-trash me-1"/>Eliminar</button>}
                    {modulo==='inscripciones'&&<button className="btn btn-outline-secondary btn-sm" onClick={()=>setPlantilla(registro)}><i className="bi bi-people me-1"/>Ver jugadores</button>}
                    {modulo==='torneos'&&<>
                        {puedeEscribir&&registro.estado==='INSCRIPCIONES'&&<button className="btn btn-outline-success btn-sm" onClick={()=>comenzar(registro)}><i className="bi bi-play-fill me-1"/>Iniciar</button>}
                        <button className="btn btn-outline-secondary btn-sm" onClick={()=>verTabla(registro)}><i className="bi bi-list-ol me-1"/>Tabla</button>
                        <button className="btn btn-outline-secondary btn-sm" onClick={()=>verPendientes(registro)}><i className="bi bi-clock-history me-1"/>Pendientes</button>
                    </>}
                </div></td></tr>)}{!registros.length&&<tr><td colSpan={config.columnas.length+2} className="empty-message">No se encontraron registros.</td></tr>}</tbody></table></div>}
            <nav className="pagination-bar" aria-label="Paginación">
                <button className="btn btn-outline-secondary btn-sm" disabled={!anterior || cargando} onClick={()=>setPagina(n=>Math.max(1,n-1))}>Anterior</button>
                <span className="pagination-label">Página <strong>{pagina}</strong> de {Math.max(1,Math.ceil(total/10))}</span>
                <button className="btn btn-outline-secondary btn-sm" disabled={!siguiente || cargando} onClick={()=>setPagina(n=>n+1)}>Siguiente</button>
            </nav>
        </div></section>
        {modulo==='inscripciones'&&plantilla&&<section className="card mt-4"><div className="card-body">
            <div className="d-flex justify-content-between align-items-center"><h2 className="h5">Jugadores de {plantilla.nombre_equipo} · {plantilla.nombre_torneo}</h2>
            <button className="btn btn-outline-secondary btn-sm" onClick={()=>setPlantilla(null)}>Cerrar</button></div>
            <p className="small text-secondary">Los jugadores de este equipo participan juntos en el torneo.</p>
            <TablaDatos datos={plantilla.jugadores}/></div></section>}
        {modulo==='torneos'&&tabla&&<section className="card mt-4"><div className="card-body"><h2 className="h5">Posiciones: {tabla.torneo}</h2><p>Estado: {tabla.estado} · Partidos: {tabla.partidos_jugados}/{tabla.partidos_totales}</p><TablaDatos datos={tabla.tabla}/></div></section>}
        {modulo==='torneos'&&pendientes&&<section className="card mt-4"><div className="card-body"><h2 className="h5">Enfrentamientos pendientes: {pendientes.torneo}</h2><p>Por programar: {pendientes.pendientes_por_programar}</p><TablaDatos datos={pendientes.enfrentamientos?.map(p=>({local:p.equipo_local.nombre,visitante:p.equipo_visitante.nombre}))}/></div></section>}
    </>;
}

// Dibujamos una tabla sencilla para listas que llegan con columnas distintas, como posiciones o jugadores.
export function TablaDatos({datos=[]}){
    if(!datos?.length)return <p className="text-secondary">No hay información para mostrar.</p>;

    // Tomamos los nombres de las columnas a partir del primer registro recibido.
    const claves=Object.keys(datos[0]);
    return <div className="table-responsive"><table className="table table-striped table-sm"><thead><tr>{claves.map(k=><th key={k}>{k.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{datos.map((fila,i)=><tr key={i}>{claves.map(k=><td key={k}>{fila[k]===null?'—':typeof fila[k]==='object'?JSON.stringify(fila[k]):String(fila[k])}</td>)}</tr>)}</tbody></table></div>;
}
