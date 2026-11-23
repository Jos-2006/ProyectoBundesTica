// Estos métodos consultan datos especiales como tablas y estadísticas.
import { api } from '../api/client.js';
import { listarTodo } from './servicioBase.js';

// Consultamos los torneos que todavía aceptan al equipo elegido para una inscripción.
export async function torneosDisponibles(equipo) {
    const {data} = await api.get('/inscripciones/torneos_disponibles/', {params: equipo ? {equipo} : {}});
    return data.torneos || [];
}

// Se envía la orden de comenzar un torneo; la API comprueba si cumple sus condiciones.
export async function iniciarTorneo(id) {
    const {data} = await api.post(`/torneos/${id}/iniciar/`);
    return data;
}

// Traemos la tabla del torneo directamente del backend.
export async function tablaTorneo(id) {
    const {data} = await api.get(`/torneos/${id}/tabla/`);
    return data;
}

// Recuperamos las parejas que todavía necesitan un partido programado.
export async function enfrentamientosTorneo(id) {
    const {data} = await api.get(`/torneos/${id}/enfrentamientos_pendientes/`);
    return data;
}

// Consultamos los torneos que tienen estadísticas disponibles.
export const listEstadisticas = () => listarTodo('/estadisticas/torneos/');

// Pedimos los datos estadísticos de partidos que el backend ofrece.
export const listPartidosJugados = () => listarTodo('/estadisticas/partidos/');

// El argumento opcion permite consultar posiciones, goleadores o resumen del mismo torneo.
export async function detalleEstadistica(id, opcion) {
    const {data} = await api.get(`/estadisticas/torneos/${id}/${opcion}/`);
    return data;
}
