// La pantalla de jugadores usa el formulario general.
import PaginaRegistros from './PaginaRegistros.jsx';

// Abre el mantenimiento de jugadores; sus campos y relaciones están definidos en configuracion.js.
export default function Jugadores() {

    // No se crea un CRUD diferente: el nombre del módulo indica qué servicios y campos se usarán.
    return <PaginaRegistros modulo="jugadores" />;
}
