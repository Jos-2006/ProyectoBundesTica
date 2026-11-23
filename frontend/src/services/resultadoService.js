// Peticiones para guardar y consultar marcadores.
// Estas operaciones reutilizan el cliente de la API y no consultan datos guardados en el navegador.
import { listarTodo, crear, actualizar, eliminar } from './servicioBase.js';

// La ruta del recurso resultados se define una sola vez para las cuatro acciones.
const ruta = '/goles/';

// Recupera los resultados registrados en Django para completar listados y selectores.
export const listResultados = () => listarTodo(ruta);

// Envía el formulario de resultado con POST y devuelve la respuesta del backend.
export const addResultado = (datos) => crear(ruta, datos);

// Modifica un resultado por su ID utilizando la petición PATCH.
export const updateResultado = (id, datos) => actualizar(ruta, id, datos);

// Solicita eliminar un resultado; Django comprueba si la regla de negocio lo permite.
export const deleteResultado = (id) => eliminar(ruta, id);
