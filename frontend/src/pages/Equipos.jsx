// La pantalla de equipos reutiliza el listado general.
import PaginaRegistros from './PaginaRegistros.jsx';

// Muestra el módulo de equipos utilizando el formulario y la tabla compartidos.
export default function Equipos() {

    // No se crea un CRUD diferente: el nombre del módulo indica qué servicios y campos se usarán.
    return <PaginaRegistros modulo="equipos" />;
}
