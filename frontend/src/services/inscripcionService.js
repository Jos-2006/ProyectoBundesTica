// Peticiones para trabajar con inscripciones.
// Estas operaciones reutilizan el cliente de la API y no consultan datos guardados en el navegador.
import { listarTodo, crear, actualizar, eliminar } from './servicioBase.js';

// La ruta del recurso inscripciones se define una sola vez para las cuatro acciones.
const ruta = '/inscripciones/';

// Recupera los inscripciones registrados en Django para completar listados y selectores.
export const listInscripciones = () => listarTodo(ruta);

// Envía el formulario de inscripción con POST y devuelve la respuesta del backend.
export const addInscripcion = (datos) => crear(ruta, datos);

// Modifica un inscripción por su ID utilizando la petición PATCH.
export const updateInscripcion = (id, datos) => actualizar(ruta, id, datos);

// Solicita eliminar un inscripción; Django comprueba si la regla de negocio lo permite.
export const deleteInscripcion = (id) => eliminar(ruta, id);
