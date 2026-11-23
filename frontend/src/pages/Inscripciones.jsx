// En esta pantalla se registran equipos en los torneos.
import PaginaRegistros from './PaginaRegistros.jsx';

// Presenta las inscripciones de equipos y sus selectores de torneo.
export default function Inscripciones() {

    // No se crea un CRUD diferente: el nombre del módulo indica qué servicios y campos se usarán.
    return <PaginaRegistros modulo="inscripciones" />;
}
