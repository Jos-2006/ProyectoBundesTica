// En esta página se programan y consultan los partidos.
import PaginaRegistros from './PaginaRegistros.jsx';

// Utiliza la pantalla compartida para programar y consultar partidos.
export default function Partidos() {

    // No se crea un CRUD diferente: el nombre del módulo indica qué servicios y campos se usarán.
    return <PaginaRegistros modulo="partidos" />;
}
