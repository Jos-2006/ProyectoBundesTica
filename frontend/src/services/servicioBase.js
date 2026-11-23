// Aquí se concentran las peticiones que usan los distintos módulos.
import { api } from '../api/client.js';

// Carga una página real del backend. Devuelve tanto registros como metadatos.
// Esta función sirve para los listados que trabajan con paginación y filtros de Django REST Framework.
export async function consultarPagina(ruta, parametros = {}) {

    // Los parámetros se pasan en la URL, pero Axios se encarga de construirla correctamente.
    const { data } = await api.get(ruta, { params: parametros });

    // Algunos endpoints devuelven una lista directa; la adaptamos al mismo formato de salida.
    if (Array.isArray(data)) return { registros: data, total: data.length, siguiente: null, anterior: null };

    // Si la respuesta no tiene una lista reconocible, avisamos en vez de mostrar datos incorrectos.
    if (!data || typeof data !== 'object' || !Array.isArray(data.results || data.resultados)) {
        throw new Error(`Django devolvió un listado con formato inesperado en ${ruta}.`);
    }

    // Entregamos registros y datos de navegación con nombres iguales para todas las pantallas.
    return {
        registros: data.results || data.resultados || [],
        total: data.count ?? data.total ?? 0,
        siguiente: data.next ?? null,
        anterior: data.previous ?? null
    };
}

// Se usa solo para desplegables y totales del dashboard, NO como paginación de listados.
// Este método se reserva para llenar desplegables, porque reúne las páginas necesarias de un recurso.
export async function listarTodo(ruta, parametros = {}) {
    let pagina = 1;
    let registros = [];

    // Avanzamos página por página hasta que Django deje de indicar que hay más resultados.
    while (true) {
        const datos = await consultarPagina(ruta, { ...parametros, page: pagina, page_size: 100 });
        registros = [...registros, ...datos.registros];
        if (!datos.siguiente) return registros;
        pagina++;

        // El límite evita una consulta interminable si el servidor devolviera una paginación incorrecta.
        if (pagina > 100) throw new Error('Se alcanzó el máximo de páginas permitidas.');
    }
}

// Los registros nuevos se guardan mediante POST y se devuelve lo que confirmó Django.
export async function crear(ruta, registro) {
    const { data } = await api.post(ruta, registro);
    return data;
}

// PATCH modifica los campos enviados del registro identificado por su ID.
export async function actualizar(ruta, id, registro) {
    const { data } = await api.patch(`${ruta}${id}/`, registro);
    return data;
}

// DELETE solicita la eliminación del registro; cualquier restricción la decide Django.
export async function eliminar(ruta, id) {
    await api.delete(`${ruta}${id}/`);
}
