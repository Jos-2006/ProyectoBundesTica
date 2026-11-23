// Peticiones para agregar, editar, listar y eliminar equipos.
// Estas operaciones reutilizan el cliente de la API y no consultan datos guardados en el navegador.
import { listarTodo, crear, actualizar, eliminar } from './servicioBase.js';

// La ruta del recurso equipos se define una sola vez para las cuatro acciones.
const ruta = '/equipos/';

// Recupera los equipos registrados en Django para completar listados y selectores.
export const listEquipos = () => listarTodo(ruta);

// Envía el formulario de equipo con POST y devuelve la respuesta del backend.
export const addEquipo = (datos) => crear(ruta, datos);

// Modifica un equipo por su ID utilizando la petición PATCH.
export const updateEquipo = (id, datos) => actualizar(ruta, id, datos);

// Solicita eliminar un equipo; Django comprueba si la regla de negocio lo permite.
export const deleteEquipo = (id) => eliminar(ruta, id);
