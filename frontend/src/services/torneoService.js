// Peticiones para administrar torneos.
// Estas operaciones reutilizan el cliente de la API y no consultan datos guardados en el navegador.
import { listarTodo, crear, actualizar, eliminar } from './servicioBase.js';

// La ruta del recurso torneos se define una sola vez para las cuatro acciones.
const ruta = '/torneos/';

// Recupera los torneos registrados en Django para completar listados y selectores.
export const listTorneos = () => listarTodo(ruta);

// Envía el formulario de torneo con POST y devuelve la respuesta del backend.
export const addTorneo = (datos) => crear(ruta, datos);

// Modifica un torneo por su ID utilizando la petición PATCH.
export const updateTorneo = (id, datos) => actualizar(ruta, id, datos);

// Solicita eliminar un torneo; Django comprueba si la regla de negocio lo permite.
export const deleteTorneo = (id) => eliminar(ruta, id);
