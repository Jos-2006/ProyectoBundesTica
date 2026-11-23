// Aquí se listan los marcadores y se pueden guardar resultados.
import {useCallback, useEffect, useMemo, useState} from 'react';
import {getError} from '../api/client.js';
import {useAuth} from '../auth/AuthContext.jsx';
import {consultarPagina} from '../services/servicioBase.js';
import {addResultado, updateResultado, deleteResultado} from '../services/resultadoService.js';
import {listPartidos} from '../services/partidoService.js';
import {listJugadores} from '../services/jugadorService.js';
import {listTorneos} from '../services/torneoService.js';
import {listEquipos} from '../services/equipoService.js';
import FormResultado from '../components/FormResultado.jsx';

// Esta pantalla administra los marcadores, pero usa las rutas de goles y no una ruta inexistente de resultados.
export default function Resultados() {
    const {puedeEditar} = useAuth();

    // Los usuarios de consulta ven las tablas; los autorizados pueden registrar, corregir o borrar marcadores.
    const puedeEscribir = puedeEditar('resultados');

    // Aquí guardamos los resultados paginados que devuelve Django.
    const [registros, setRegistros] = useState([]);

    // Las listas de partidos y jugadores llenan los selectores del formulario.
    const [partidos, setPartidos] = useState([]);
    const [jugadores, setJugadores] = useState([]);
    const [torneos, setTorneos] = useState([]);
    const [equipos, setEquipos] = useState([]);
    const [editando, setEditando] = useState(null);

    // Los controles de torneo, equipo y empate se envían como filtros reales al backend.
    const [filtros, setFiltros] = useState({torneo:'',equipo:'',empate:''});
    const [ordenamiento, setOrdenamiento] = useState('');

    // Se controla el número de página junto con el total y los enlaces de navegación.
    const [pagina, setPagina] = useState(1);
    const [total, setTotal] = useState(0);
    const [siguiente, setSiguiente] = useState(null);
    const [anterior, setAnterior] = useState(null);

    // El estado de carga impide confundir una petición pendiente con una tabla vacía.
    const [cargando, setCargando] = useState(true);
    const [guardando, setGuardando] = useState(false);
    const [error, setError] = useState('');
    const [exito, setExito] = useState('');

    // La tabla se consulta por página y con los filtros que eligió el usuario.
    // Solicitamos a Django una página de resultados según los filtros seleccionados.
    const cargar = useCallback(async () => {
        setCargando(true);
        setError('');
        try {

            // La API recibe la página actual y el máximo de diez registros.
            const parametros = {page:pagina,page_size:10};

            // Solo mandamos filtros que el usuario haya seleccionado.
            for (const [nombre, valor] of Object.entries(filtros)) {
                if (valor !== '') parametros[nombre] = valor;
            }
            if (ordenamiento) parametros.ordering = ordenamiento;

            // El recurso existente para estos marcadores es /goles/, no /resultados/.
            const datos = await consultarPagina('/goles/', parametros);
            setRegistros(datos.registros);
            setTotal(datos.total);
            setSiguiente(datos.siguiente);
            setAnterior(datos.anterior);
        } catch(e) {setError(getError(e));}
        finally {setCargando(false);}
    }, [filtros, ordenamiento, pagina]);

    // Cargamos a la vez partidos, jugadores, torneos y equipos para preparar el formulario y los filtros.
    const cargarOpciones = useCallback(async () => {
        try {
            const [p,j,t,e] = await Promise.all([listPartidos(),listJugadores(),listTorneos(),listEquipos()]);
            setPartidos(p);setJugadores(j);setTorneos(t);setEquipos(e);
        } catch(e) {setError(getError(e));}
    }, []);

    // Cuando cambian los filtros o la página se actualiza la tabla desde la API.
    useEffect(()=>{cargar();},[cargar]);

    // Las opciones del formulario se consultan cuando se abre la pantalla.
    useEffect(()=>{cargarOpciones();},[cargarOpciones]);

    // Solo mostramos partidos programados que estén en un torneo en curso.
    // Solo se consideran partidos programados de torneos en curso para registrar un marcador nuevo.
    const disponibles = useMemo(() => partidos.filter(p =>
        p.estado === 'PROGRAMADO' && torneos.some(t =>
            Number(t.id) === Number(p.torneo) && t.estado === 'EN_CURSO'
        )
    ), [partidos, torneos]);

    // Revisamos el estado del torneo del resultado para saber si deben bloquearse sus acciones.
    function torneoFinalizado(resultado) {
        const partido = partidos.find(p => Number(p.id) === Number(resultado.partido));
        const torneo = torneos.find(t => Number(t.id) === Number(partido?.torneo));
        return torneo?.estado === 'FINALIZADO';
    }

    // Al elegir un filtro nuevo regresamos a la primera página del listado.
    function cambiarFiltro(nombre, valor) {
        setPagina(1);
        setFiltros(actual=>({...actual,[nombre]:valor}));
    }

    // Para editar se envían los cambios, y para registrar se envía todo el resultado.
    // Este método utiliza PATCH para corregir un marcador existente y POST para registrar uno nuevo.
    async function guardar(datos) {
        setGuardando(true);setError('');setExito('');
        try {
            if (editando) {

                // Al editar enviamos únicamente el marcador y los anotadores que realmente correspondan.
                const cambios = {
                    goles_local: datos.goles_local,
                    goles_visitante: datos.goles_visitante
                };

                // No sustituimos la lista de anotadores a menos que el formulario haya enviado ese campo.
                if (datos.anotadores !== undefined) cambios.anotadores = datos.anotadores;
                await updateResultado(editando.id, cambios);
            } else {
                await addResultado(datos);
            }

            // Después de la respuesta exitosa se recargan tanto los marcadores como las listas relacionadas.
            setExito('Resultado guardado correctamente.');
            setEditando(null);
            await Promise.all([cargar(),cargarOpciones()]);
            return true;
        } catch(e) {setError(getError(e));return false;}
        finally {setGuardando(false);}
    }

    // Pedimos permiso al usuario antes de borrar un resultado que afectará las estadísticas.
    async function borrar(registro) {
        if (!window.confirm('¿Eliminar este resultado? Se actualizarán las estadísticas.')) return;
        setError('');setExito('');
        try {
            await deleteResultado(registro.id);
            setExito('Resultado eliminado.');
            await Promise.all([cargar(),cargarOpciones()]);
        } catch(e) {setError(getError(e));}
    }

    // El formulario se muestra solo si el perfil puede escribir; los demás usuarios conservan la consulta.
    return <>
        <div className="module-header"><div className="module-header-icon"><i className="bi bi-flag-fill"/></div><div>
            <h1>Resultados de Partidos y goles</h1>
            <p>Consulta los marcadores y registra los resultados de tus partidos.</p>
        </div></div>
        {error && <div className="alert alert-danger">{error}</div>}
        {exito && <div className="alert alert-success">{exito}</div>}
        {puedeEscribir ? <FormResultado registro={editando}
            partidos={editando ? [...disponibles,...partidos.filter(p=>p.id===editando.partido)] : disponibles}
            jugadores={jugadores} guardar={guardar} cancelar={()=>setEditando(null)} guardando={guardando}/>
            : <div className="alert alert-secondary">Estás en modo consulta. No puedes modificar marcadores con este usuario.</div>}
        <section className="card record-list-card border-0 shadow-sm"><div className="card-body p-4">
            <div className="panel-heading"><span className="panel-heading-icon"><i className="bi bi-list-check"/></span><div><h2>Marcadores de partidos registrados</h2><small>{total} resultados encontrados</small></div></div>
            <div className="result-filter-panel row g-2 mb-3">
                <div className="col-md-3"><label className="form-label">Torneo</label>
                    <select className="form-select" value={filtros.torneo} onChange={e=>cambiarFiltro('torneo',e.target.value)}>
                        <option value="">Todos</option>{torneos.map(t=><option key={t.id} value={t.id}>{t.nombre}</option>)}
                    </select></div>
                <div className="col-md-3"><label className="form-label">Equipo</label>
                    <select className="form-select" value={filtros.equipo} onChange={e=>cambiarFiltro('equipo',e.target.value)}>
                        <option value="">Todos</option>{equipos.map(e=><option key={e.id} value={e.id}>{e.nombre}</option>)}
                    </select></div>
                <div className="col-md-2"><label className="form-label">Empate</label>
                    <select className="form-select" value={filtros.empate} onChange={e=>cambiarFiltro('empate',e.target.value)}>
                        <option value="">Todos</option><option value="true">Sí</option><option value="false">No</option>
                    </select></div>
                <div className="col-md-3"><label className="form-label">Ordenar</label>
                    <select className="form-select" value={ordenamiento} onChange={e=>{setPagina(1);setOrdenamiento(e.target.value);}}>
                        <option value="">Más recientes</option><option value="partido__fecha">Fecha ascendente</option><option value="-partido__fecha">Fecha descendente</option>
                    </select></div>
                <div className="col-md-1 d-flex align-items-end"><button className="btn btn-outline-secondary" onClick={()=>{setFiltros({torneo:'',equipo:'',empate:''});setOrdenamiento('');setPagina(1);}}>Limpiar</button></div>
            </div>
            {cargando ? <p role="status" className="text-secondary"><i className="bi bi-arrow-repeat me-2"/>Cargando resultados...</p> : <div className="table-responsive"><table className="table table-hover align-middle">
                <thead><tr><th>ID</th><th>Torneo</th><th>Fecha</th><th>Marcador</th><th>Resultado</th>{puedeEscribir&&<th>Acciones</th>}</tr></thead>
                <tbody>{registros.map(r=><tr key={r.id}><td>{r.id}</td><td>{r.torneo}</td><td>{r.fecha}</td><td>{r.marcador}</td><td>{r.resultado}</td>
                    {puedeEscribir&&<td>{torneoFinalizado(r) ?
                        <span className="text-secondary small">Torneo finalizado</span> : <>
                        <button className="btn btn-outline-primary btn-sm me-1" onClick={()=>{setEditando(r);window.scrollTo(0,0);}}><i className="bi bi-pencil-square me-1"/>Editar</button>
                        <button className="btn btn-outline-danger btn-sm" onClick={()=>borrar(r)}><i className="bi bi-trash me-1"/>Eliminar</button></>}</td>}</tr>)}
                    {!registros.length&&<tr><td colSpan={puedeEscribir?6:5} className="empty-message">No hay resultados que coincidan.</td></tr>}
                </tbody>
            </table></div>}
            <nav className="pagination-bar" aria-label="Paginación resultados">
                <button className="btn btn-outline-secondary btn-sm" disabled={!anterior||cargando} onClick={()=>setPagina(n=>Math.max(1,n-1))}>Anterior</button>
                <span className="pagination-label">Página <strong>{pagina}</strong> de {Math.max(1,Math.ceil(total/10))}</span>
                <button className="btn btn-outline-secondary btn-sm" disabled={!siguiente||cargando} onClick={()=>setPagina(n=>n+1)}>Siguiente</button>
            </nav>
        </div></section>
    </>;
}
