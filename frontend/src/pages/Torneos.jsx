// La pantalla de torneos utiliza el listado general.
import PaginaRegistros from './PaginaRegistros.jsx';

// Reutiliza la página general para registrar torneos y consultar sus acciones especiales.
export default function Torneos() {

    // No se crea un CRUD diferente: el nombre del módulo indica qué servicios y campos se usarán.
    return <PaginaRegistros modulo="torneos" />;
}
