// Peticiones para administrar partidos.
// Estas operaciones reutilizan el cliente de la API y no consultan datos guardados en el navegador.
import { listarTodo, crear, actualizar, eliminar } from './servicioBase.js';

// La ruta del recurso partidos se define una sola vez para las cuatro acciones.
const ruta = '/partidos/';

// Recupera los partidos registrados en Django para completar listados y selectores.
export const listPartidos = () => listarTodo(ruta);

// Envía el formulario de partido con POST y devuelve la respuesta del backend.
export const addPartido = (datos) => crear(ruta, datos);

// Modifica un partido por su ID utilizando la petición PATCH.
export const updatePartido = (id, datos) => actualizar(ruta, id, datos);

// Solicita eliminar un partido; Django comprueba si la regla de negocio lo permite.
export const deletePartido = (id) => eliminar(ruta, id);
