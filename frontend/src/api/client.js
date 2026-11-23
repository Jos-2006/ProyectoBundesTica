// En este archivo se prepara Axios para hablar con la API.
import axios from 'axios';

// La dirección base se configura una sola vez para todos los servicios.
// Todas las pantallas usan esta misma conexión. Si cambia la dirección de la API, se configura aquí y no en cada servicio.
export const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api',
    timeout: 15000
});

// Enviamos el token de sesión cuando el usuario ya inició sesión.
// Antes de enviar una petición se revisa si hay una sesión iniciada; el backend recibe el token en la cabecera Authorization.
api.interceptors.request.use(configuracion => {
    const token = sessionStorage.getItem('bundestica_token');
    if (token) configuracion.headers.Authorization = `Token ${token}`;
    return configuracion;
});

// Si Django responde 401, avisamos al contexto de autenticación para que cierre una sesión que ya no sirve.
api.interceptors.response.use(
    respuesta => respuesta,
    error => {
        if (error.response?.status === 401 && sessionStorage.getItem('bundestica_token')) {
            window.dispatchEvent(new Event('bundestica-sesion-expirada'));
        }
        return Promise.reject(error);
    }
);

// Pasamos los errores a mensajes más fáciles de entender en pantalla.
// Recibimos el error de Axios y lo convertimos en un texto corto que se pueda mostrar en un aviso de Bootstrap.
export function getError(error) {

    // Cuando ni siquiera hay respuesta HTTP, normalmente el servidor está apagado o la conexión falló.
    if (!error.response) {
        if (!error.isAxiosError && error.message) return error.message;
        return 'No se pudo conectar con Django. Comprueba que esté ejecutándose en el puerto 8000.';
    }

    // El código HTTP ayuda a distinguir una validación, falta de permisos o un error interno.
    const codigo = error.response.status;
    const titulos = {
        400: 'Datos inválidos', 401: 'Sesión no válida', 403: 'Sin permisos',
        404: 'Ruta o registro no encontrado', 405: 'Método HTTP no permitido',
        409: 'Conflicto con una regla de negocio', 500: 'Error interno de Django'
    };

    // Revisamos el contenido devuelto por Django sin asumir que todos los errores tienen el mismo formato.
    const datos = error.response.data;
    const tipo = error.response.headers?.['content-type'] || '';

    // Si la API devuelve una página HTML de error, no la mostramos completa dentro de la interfaz.
    if (tipo.includes('text/html') || (typeof datos === 'string' && /<!doctype html|<html/i.test(datos))) {
        return `${titulos[codigo] || `Error HTTP ${codigo}`}. Comprueba que la URL exista en el backend.`;
    }
    let detalle = '';
    if (typeof datos === 'string') detalle = datos.slice(0, 400);
    else if (Array.isArray(datos)) detalle = datos.map(String).join(', ');

    // Los errores de un serializer pueden venir separados por campo; los juntamos para que el usuario los entienda.
    else if (datos && typeof datos === 'object') {
        detalle = Object.entries(datos).map(([campo, mensaje]) => {
            const etiqueta = ['detail','non_field_errors','mensaje'].includes(campo) ? '' : `${campo}: `;
            const valor = Array.isArray(mensaje) ? mensaje.join(', ') :
                typeof mensaje === 'object' ? JSON.stringify(mensaje) : String(mensaje);
            return etiqueta + valor;
        }).join(' | ');
    }
    return `${titulos[codigo] || `Error HTTP ${codigo}`}${detalle ? ': ' + detalle : ''}`;
}
