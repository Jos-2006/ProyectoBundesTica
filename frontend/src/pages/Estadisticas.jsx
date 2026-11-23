// Esta página consulta las posiciones y goleadores de los torneos finalizados.
import {useEffect, useState} from 'react';
import {getError} from '../api/client.js';
import {listEstadisticas, detalleEstadistica} from '../services/consultaService.js';
import {TablaDatos} from './PaginaRegistros.jsx';

// Esta pantalla consulta estadísticas calculadas por Django; no hace cálculos locales de posiciones.
export default function Estadisticas() {

    // Guardamos los torneos disponibles para consultarlos desde el selector.
    const [torneos, setTorneos] = useState([]);
    const [id, setId] = useState('');

    // La tabla y los goleadores se mantienen separados para mostrarlos en secciones distintas.
    const [posiciones, setPosiciones] = useState(null);
    const [goleadores, setGoleadores] = useState(null);

    // También se informa si la consulta tarda o devuelve un error de red.
    const [error, setError] = useState('');
    const [cargando, setCargando] = useState(true);

    // Apenas se abre la pantalla cargamos los torneos con estadísticas disponibles.
    useEffect(() => {
        listEstadisticas().then(setTorneos).catch(error => setError(getError(error)))
            .finally(() => setCargando(false));
    }, []);

    // Al elegir un torneo pedimos posiciones y goleadores al backend.
    async function consultar() {
        setError('');

        // Limpiamos el resultado anterior para no mezclar dos torneos diferentes.
        setPosiciones(null);
        setGoleadores(null);
        try {

            // Las dos consultas se realizan al mismo tiempo para mostrar los datos del mismo torneo.
            const [tabla, anotadores] = await Promise.all([
                detalleEstadistica(id, 'posiciones'),
                detalleEstadistica(id, 'goleadores')
            ]);
            setPosiciones(tabla);
            setGoleadores(anotadores);
        } catch (error) {
            setError(getError(error));
        }
    }

    // El usuario elige un torneo y consulta las dos tablas, sin modificar la información.
    return <>
        <header className="module-header">
            <div className="module-header-icon"><i className="bi bi-bar-chart-fill" aria-hidden="true"/></div>
            <div><h1>Estadísticas</h1><p>Consulta las posiciones de los equipos y los goleadores por torneo.</p></div>
        </header>
        <div className="module-note"><i className="bi bi-info-circle-fill" aria-hidden="true"/><span>Aqui solo se pueden ver los torneos finalizados,
             si quieres ver los demás torneos  abre el módulo de Torneos.</span></div>
        {error && <div className="alert alert-danger" role="alert">{error}</div>}
        {cargando && <p role="status">Cargando estadísticas...</p>}
        <section className="card mb-4"><div className="card-body">
            <label htmlFor="torneo-finalizado" className="form-label">Selecciona un Torneo finalizado</label>
            <div className="d-flex gap-2">
                <select id="torneo-finalizado" className="form-select" value={id} onChange={evento => setId(evento.target.value)}>
                    <option value="">Seleccionar torneo...</option>
                    {torneos.map(torneo => <option key={torneo.torneo_id} value={torneo.torneo_id}>{torneo.torneo}</option>)}
                </select>
                <button className="btn btn-primary" disabled={!id} onClick={consultar}>Consultar</button>
            </div>
        </div></section>
        {!cargando && torneos.length === 0 && <p className="alert alert-info">Todavía no hay torneos finalizados.</p>}
        {posiciones && <section className="card mb-3"><div className="card-body">
            <h2 className="h5">Tabla final del torneo {posiciones.torneo}</h2>
            <TablaDatos datos={posiciones.tabla}/>
        </div></section>}
        {goleadores && <section className="card mb-3"><div className="card-body">
            <h2 className="h5">Goleadores del torneo</h2><p>{goleadores.nota}</p>
            <TablaDatos datos={goleadores.goleadores}/>
        </div></section>}
    </>;
}
