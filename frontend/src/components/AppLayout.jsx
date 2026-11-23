// Este es el menú que se muestra mientras el usuario está dentro del sistema.
import { NavLink, Outlet,useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';

// Cada enlace abre un módulo de la aplicación.
// Los enlaces del menú se definen en un mismo lugar para evitar rutas duplicadas.
const secciones = [
    ['/dashboard', 'Inicio', 'bi-grid-1x2-fill'],
    ['/equipos', 'Equipos', 'bi-shield-fill'],
    ['/jugadores', 'Jugadores', 'bi-people-fill'],
    ['/torneos', 'Torneos', 'bi-trophy-fill'],
    ['/inscripciones', 'Inscripciones', 'bi-person-check-fill'],
    ['/partidos', 'Partidos', 'bi-calendar2-event-fill'],
    ['/resultados', 'Resultados', 'bi-flag-fill'],
    ['/estadisticas', 'Estadísticas', 'bi-bar-chart-fill']
];

// Este componente envuelve todas las pantallas privadas y les deja el mismo encabezado.
export default function AppLayout() {

    // Mostramos el usuario y sus roles tal como los devolvió Django.
    const {username, roles, logout} = useAuth();
    const navigate = useNavigate();
    const { pathname } = useLocation();

    // La parte de la URL sirve para aplicar el estilo del módulo que se está consultando.
    const moduloActual = pathname.split('/')[1];

    // Al pulsar Salir se borra la sesión y se vuelve directamente al formulario de ingreso.
    function salir() { logout(); navigate('/login', {replace:true}); }

    // El menú permanece visible, mientras Outlet coloca dentro la página seleccionada.
    return <div className="app-shell">
        <header className="app-header">
            <div className="header-inner">
                <NavLink to="/dashboard" className="brand">
                    <span className="brand-mark"><i className="bi bi-crosshair2" aria-hidden="true"/></span>BundesTica
                </NavLink>
                <div className="account">
                    <div className="user-info"><strong>{username}</strong><small>{roles.join(', ') || 'Sin perfil'}</small></div>
                    <button className="btn btn-logout" onClick={salir} aria-label="Cerrar sesión">
                        <i className="bi bi-box-arrow-right" aria-hidden="true"/><span className="d-none d-sm-inline">Salir</span>
                    </button>
                </div>
            </div>
            <nav className="section-nav" aria-label="Secciones">
                {secciones.map(([ruta,nombre,icono]) =>
                    <NavLink key={ruta} to={ruta} className="section-link">
                        <i className={`bi ${icono}`} aria-hidden="true"/><span>{nombre}</span>
                    </NavLink>
                )}
            </nav>
        </header>
        <main className="page-content container-fluid" data-modulo={moduloActual}>
            <Outlet />
        </main>
    </div>;
}
