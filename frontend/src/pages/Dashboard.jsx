// El inicio muestra un resumen para entrar rápido a cada módulo.
import {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {getError} from '../api/client.js';
import {consultarPagina} from '../services/servicioBase.js';

// Cada módulo muestra su total obtenido de la API.
// Cada elemento define el nombre del módulo, su ruta en React y la ruta real usada para obtener el total.
const modulos = [
    ['Equipos', 'equipos', '/equipos', null, 'bi-shield-fill', 'Clubes registrados'],
    ['Jugadores', 'jugadores', '/jugadores', null, 'bi-people-fill', 'Plantillas disponibles'],
    ['Torneos', 'torneos', '/torneos', null, 'bi-trophy-fill', 'Competiciones'],
    ['Inscripciones', 'inscripciones', '/inscripciones', null, 'bi-person-check-fill', 'Equipos participantes'],
    ['Partidos', 'partidos', '/partidos', null, 'bi-calendar2-event-fill', 'Encuentros programados'],
    ['Resultados', 'resultados', '/resultados', '/goles', 'bi-flag-fill', 'Marcadores guardados']
];

// Esta es la primera pantalla del sistema después de iniciar sesión.
export default function Dashboard() {

    // Los contadores empiezan vacíos porque siempre se obtienen de registros reales de Django.
    const [datos, setDatos] = useState(null);
    const [error, setError] = useState('');

    // Las cantidades siguen llegando desde Django, no hay datos de ejemplo.
    // Al abrir el Dashboard pedimos los totales de todos los módulos en paralelo.
    useEffect(() => {

        // Para contar registros usamos páginas pequeñas; no hace falta descargar todas las filas.
        Promise.all(modulos.map(async ([,clave,ruta,rutaApi]) => {
            const pagina = await consultarPagina(`${rutaApi || ruta}/`, {page:1,page_size:1});

            // Se devuelve el total asociado al módulo para mostrarlo en su tarjeta.
            return [clave,pagina.total];
        })).then(valores=>setDatos(Object.fromEntries(valores))).catch(e=>setError(getError(e)));
    }, []);

    // Primero se presenta el acceso a torneos y después los enlaces al resto del sistema.
    return <>
        <section className="dashboard-hero">
            <div className="dashboard-intro">
                <h1>Bienvenido a <br/>Bundestica</h1>
                <p>Gestiona tus torneos, sus partidos y resultados.</p>
                <Link className="btn hero-button" to="/torneos">Ver torneos <i className="bi bi-arrow-up-right" aria-hidden="true"/></Link>
            </div>
            <div className="pitch-art" aria-hidden="true"><div className="pitch-lines"><span/><span/></div></div>
        </section>
        <section className="dashboard-modules" aria-labelledby="titulo-modulos">
            <h2 id="titulo-modulos">Módulos de las pagina</h2>
            <p>Contamos con estos modulos a tu disposición</p>
            {error && <div className="alert alert-danger" role="alert">{error}</div>}
            <div className="module-directory">
                {modulos.map(([titulo,campo,ruta,,icono,descripcion])=>
                    <Link className="module-entry" to={ruta} key={campo}>
                        <span className="entry-icon"><i className={`bi ${icono}`} aria-hidden="true"/></span>
                        <span className="entry-text"><strong>{titulo}</strong><small>{descripcion}</small></span>
                        <span className="entry-value" aria-label={`Total: ${datos ? datos[campo] : 'sin datos'}`}>{datos ? datos[campo] : '—'}</span>
                        <i className="bi bi-arrow-right" aria-hidden="true"/>
                    </Link>
                )}
            </div>
        </section>
    </>;
}
