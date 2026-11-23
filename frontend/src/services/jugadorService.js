// Peticiones para administrar jugadores.
// Estas operaciones reutilizan el cliente de la API y no consultan datos guardados en el navegador.
import { listarTodo, crear, actualizar, eliminar } from './servicioBase.js';

// La ruta del recurso jugadores se define una sola vez para las cuatro acciones.
const ruta = '/jugadores/';

// Recupera los jugadores registrados en Django para completar listados y selectores.
export const listJugadores = () => listarTodo(ruta);

// Envía el formulario de jugador con POST y devuelve la respuesta del backend.
export const addJugador = (datos) => crear(ruta, datos);

// Modifica un jugador por su ID utilizando la petición PATCH.
export const updateJugador = (id, datos) => actualizar(ruta, id, datos);

// Solicita eliminar un jugador; Django comprueba si la regla de negocio lo permite.
export const deleteJugador = (id) => eliminar(ruta, id);
