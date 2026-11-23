# Frontend de BundesTica

Para el segundo proyecto hicimos la parte que usa la persona encargada de organizar el torneo. Desde la interfaz puede revisar qué equipos están inscritos, buscar jugadores, programar los partidos y registrar sus marcadores. El inicio muestra los conteos que devuelve la API y sirve para entrar a los módulos.

Usamos React con Vite, Bootstrap para la interfaz, React Router para cambiar de pantalla y Axios para hablar con Django. Los formularios y las tablas consultan la misma API que desarrollamos para el primer proyecto.

## Cómo correr el frontend

Ocupamos Node.js 24 y npm. Primero levantamos Django con MySQL siguiendo el README de la raíz del proyecto. Luego abrimos otra terminal de PowerShell desde la raíz y ejecutamos:

```powershell
cd frontend
npm  install
npm  run dev
```

Abrimos la dirección que imprime Vite, normalmente [http://localhost:5173](http://localhost:5173). Podemos comprobar la compilación con `npm.cmd run build` desde la carpeta `frontend`.

## Conexión con Django y CORS

Cuando abrimos un módulo, React hace las peticiones a `/api`. En desarrollo, Vite recibe esas peticiones y las pasa a Django, que normalmente está en `http://127.0.0.1:8000`. Por ejemplo, la pantalla de Equipos consulta `/api/equipos/`.

Como el navegador hace las peticiones al mismo origen desde el que abrió React, con el proxy de Vite no hace falta configurar CORS en Django para el desarrollo local. Si en otro ambiente el navegador llama directamente a Django desde un origen distinto, el backend debe permitir el origen exacto del frontend en su configuración CORS.

El archivo `.env.example` muestra los valores que usamos en local:

```env
VITE_API_URL=/api
VITE_BACKEND_URL=http://127.0.0.1:8000
```

Si Django está en otro puerto, copiamos `.env.example` a `.env.local` dentro de `frontend`, cambiamos `VITE_BACKEND_URL` y reiniciamos Vite. Las variables `VITE_` son visibles desde el navegador.

## Qué se puede hacer en la interfaz

| Pantalla | Para qué la usamos |
|---|---|
| Inicio | Ver los conteos que devuelve la API y entrar a los módulos. |
| Equipos y Jugadores | Registrar plantillas, asignar los jugadores a un equipo y buscar o filtrar registros. |
| Torneos e Inscripciones | Configurar el torneo, inscribir equipos, revisar los cupos y consultar las posiciones. |
| Partidos y Resultados | Programar los encuentros y cargar los marcadores. |
| Estadísticas | Consultar la tabla final y los goleadores de torneos terminados. |

## Probar los perfiles

En Django usamos cuentas ficticias, como `admin_prueba`, `operador_prueba` y `consulta_prueba`, asignadas a los grupos `Administrador`, `Operador` y `Consulta`, respectivamente. Con Administrador podemos crear y editar un equipo. Con Operador podemos gestionar partidos y resultados. Con Consulta podemos abrir los listados y revisar los datos. Cada cuenta se configura en la instalación local.

## Dónde está cada parte del código

- `src/pages/` contiene las pantallas y sus listados.
- `src/components/` contiene los formularios, los filtros y la navegación.
- `src/services/` contiene las operaciones que hacen las pantallas contra la API.
- `src/api/client.js` configura Axios y añade el token a las solicitudes.
- `src/auth/` maneja la sesión y el acceso a las rutas privadas.
- `src/styles.css` contiene los estilos generales y los colores.

## Matriz de pantallas y endpoints

| Pantalla | Acción | Método y ruta |
|---|---|---|
| Iniciar sesión | Pedir el token y cargar el perfil | `POST /api/auth/token/`, `GET /api/auth/me/` |
| Inicio | Consultar los totales de equipos, jugadores, torneos, inscripciones, partidos y resultados | `GET /api/equipos/`, `GET /api/jugadores/`, `GET /api/torneos/`, `GET /api/inscripciones/`, `GET /api/partidos/`, `GET /api/goles/` |
| Equipos | Listar, buscar, filtrar, ordenar y paginar | `GET /api/equipos/` |
| Equipos | Crear, editar y eliminar | `POST /api/equipos/`, `PATCH /api/equipos/{id}/`, `DELETE /api/equipos/{id}/` |
| Jugadores | Listar, buscar, filtrar, ordenar y paginar | `GET /api/jugadores/` |
| Jugadores | Crear, editar y eliminar | `POST /api/jugadores/`, `PATCH /api/jugadores/{id}/`, `DELETE /api/jugadores/{id}/` |
| Torneos | Listar, buscar, filtrar, ordenar y paginar | `GET /api/torneos/` |
| Torneos | Crear, editar y eliminar | `POST /api/torneos/`, `PATCH /api/torneos/{id}/`, `DELETE /api/torneos/{id}/` |
| Torneos | Iniciar, revisar posiciones y consultar enfrentamientos pendientes | `POST /api/torneos/{id}/iniciar/`, `GET /api/torneos/{id}/tabla/`, `GET /api/torneos/{id}/enfrentamientos_pendientes/` |
| Inscripciones | Listar y consultar jugadores inscritos | `GET /api/inscripciones/`. La plantilla viene en el registro. |
| Inscripciones | Consultar torneos disponibles para un equipo | `GET /api/inscripciones/torneos_disponibles/?equipo={id}` |
| Inscripciones | Crear, editar y retirar inscripciones | `POST /api/inscripciones/`, `PATCH /api/inscripciones/{id}/`, `DELETE /api/inscripciones/{id}/` |
| Partidos | Listar y consultar los equipos inscritos para programar el encuentro | `GET /api/partidos/`, `GET /api/inscripciones/` |
| Partidos | Programar, editar y eliminar | `POST /api/partidos/`, `PATCH /api/partidos/{id}/`, `DELETE /api/partidos/{id}/` |
| Resultados | Listar marcadores y consultar partidos programados y jugadores | `GET /api/goles/`, `GET /api/partidos/`, `GET /api/jugadores/` |
| Resultados | Registrar, editar y eliminar marcadores | `POST /api/goles/`, `PATCH /api/goles/{id}/`, `DELETE /api/goles/{id}/` |
| Estadísticas | Elegir un torneo finalizado, ver la tabla final y consultar los goleadores | `GET /api/estadisticas/torneos/`, `GET /api/estadisticas/torneos/{id}/posiciones/`, `GET /api/estadisticas/torneos/{id}/goleadores/` |
| Salir | Borrar la sesión del navegador | Acción local de React |

Los selectores de equipos y torneos también reutilizan `GET /api/equipos/` y `GET /api/torneos/`. En los listados, acciones como Actualizar y Siguiente reutilizan el mismo `GET` con los parámetros que estén seleccionados.

## Matriz de permisos

| Acción | Administrador | Operador | Consulta |
|---|---|---|---|
| Consultar los módulos y las estadísticas | Sí | Sí | Sí |
| Gestionar equipos, jugadores, torneos e inscripciones | Sí | — | — |
| Programar partidos y gestionar marcadores | Sí | Sí | — |

Los permisos de escritura se aplican junto con las reglas de negocio. Por ejemplo, editar una inscripción depende de que el torneo siga abierto.

## Datos de la API que usa React

El login recibe un JSON con `username` y `password` y devuelve `token`. Para el resto de las solicitudes, Axios envía el encabezado `Authorization: Token <token>`. El perfil devuelve `username`, `roles` y `permisos`. Al cerrar sesión, React borra el token del navegador. El backend no lo revoca con esa acción.

| Código | Cuándo se usa |
|---|---|
| `200`, `201`, `204` | Consulta o edición correcta, creación y eliminación, respectivamente. |
| `400` | Los datos no cumplen una validación. |
| `401` / `403` | Falta autenticación o el perfil no tiene autorización para esa acción. |
| `404` / `409` | El registro no existe o la operación entra en conflicto con una regla del sistema. |

### Ejemplos de solicitudes y respuestas

Para buscar equipos de Puntarenas con jugadores y ordenar los resultados por nombre, usamos:

```text
GET /api/equipos/?ciudad=Puntarenas&con_jugadores=true&ordering=nombre&page=1&page_size=10
```

Un listado paginado sin coincidencias devuelve esta estructura:

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

Cuando hay coincidencias, `results` contiene las filas de la página. `count` representa el total del listado filtrado. Por defecto se muestran 10 registros y `page_size` permite solicitar hasta 100.

Para crear un equipo con una cuenta Administrador, enviamos un `POST /api/equipos/` con un cuerpo como este:

```json
{
  "nombre": "Equipo de prueba",
  "entrenador": "Entrenador de prueba",
  "ciudad": "Puntarenas"
}
```

### Parámetros y campos por recurso

Las listas pueden incluir `page` y `page_size`. En la matriz de permisos de arriba se indica quién puede consultar o escribir en cada módulo.

#### Equipos

`/api/equipos/` GET (todos) y POST (Administrador); `/api/equipos/{id}/` GET (todos), PATCH/PUT/DELETE (Administrador).

- Entrada POST/PATCH: `nombre` (3 o más caracteres, nombre no repetido), `entrenador` opcional, `ciudad` opcional.
- Respuesta: `id`, `nombre`, `entrenador`, `ciudad`, `fecha_registro`, `cantidad_jugadores`, `torneos_ganados`, `jugadores` (lista con `id`, `nombre`, `numero_camiseta`, `posicion`).
- Parámetros GET: `search` en nombre/entrenador/ciudad; `ciudad` (coincidencia exacta), `con_jugadores=true|false`; `ordering=nombre|-nombre|-cantidad_jugadores|fecha_registro`; `page`, `page_size`.
- Regla: no se puede eliminar un equipo que haya tenido inscripciones; conflicto 409.

#### Jugadores

`/api/jugadores/` GET (todos), POST (Administrador); `/api/jugadores/{id}/` GET (todos), PATCH/PUT/DELETE (Administrador).

- Entrada POST/PATCH: `nombre`, `identificacion` única normalizada, `numero_camiseta` entre 1 y 99, `posicion` (`POR`, `DEF`, `MED`, `DEL`), `equipo` (ID de Equipo).
- Respuesta: `id`, esos campos, `posicion_nombre`, `nombre_equipo`, `goles_totales`.
- Parámetros GET: `search` (nombre, identificación, equipo), `equipo`, `torneo`, `posicion`, `numero_camiseta`, `identificacion`, `ordering=nombre|numero_camiseta|-goles_totales`, `page`, `page_size`.
- Reglas: jugador en un solo equipo; camiseta única por equipo; plantillas bloqueadas en torneo en curso, restricciones al cambio de equipo.

#### Torneos

`/api/torneos/` GET (todos) y POST (Administrador); `/api/torneos/{id}/` GET (todos), PATCH/PUT/DELETE (Administrador).

- Entrada POST/PATCH: `nombre`, `descripcion`, `fecha_inicio` y `fecha_fin` en formato `YYYY-MM-DD`, `maximo_equipos` (2–20), `minimo_jugadores_por_equipo` (1–30), `vueltas` (1 o 2), `puntos_victoria`, `puntos_empate`, `puntos_derrota` (`victoria > empate >= derrota`).
- Respuesta: campos de entrada más `id`, `vueltas_nombre`, `estado`, `estado_nombre`, `equipos_inscritos`, `cupos_disponibles`, `cantidad_partidos`, `partidos_jugados`, `partidos_restantes`, `partidos_si_se_llena`, `campeon`, `nombre_campeon`, `fecha_creacion`.
- Parámetros GET: `search`, `estado`, `fecha_desde`, `fecha_hasta`, `campeon`, `con_cupos`, `ordering=nombre|fecha_inicio|-fecha_inicio`, `page`, `page_size`.
- Acciones GET `/api/torneos/{id}/tabla/` devuelve `torneo`, `estado`, `partidos_jugados`, `partidos_totales`, `campeon`, `tabla` de posiciones.
- GET `/api/torneos/{id}/enfrentamientos_pendientes/` devuelve `torneo`, `estado`, `pendientes_por_programar`, `enfrentamientos` con equipos local/visitante.
- POST `/api/torneos/{id}/iniciar/` devuelve `mensaje` y `torneo` actualizado; exige mínimo 2 equipos inscritos.
- Reglas: estado inicial INSCRIPCIONES; al llenar cupo pasa a EN_CURSO; solo se edita o elimina antes de empezar.

#### Inscripciones

`/api/inscripciones/` GET (todos) y POST (Administrador); `/api/inscripciones/{id}/` GET (todos), PATCH/PUT/DELETE (Administrador).

- Entrada POST: `torneo` (ID), `equipo` (ID). PATCH: cambiar `equipo` durante inscripciones abiertas; no se puede cambiar de torneo.
- Respuesta de listado/detalle: `id`, `torneo`, `nombre_torneo`, `estado_torneo`, `equipo`, `nombre_equipo`, `fecha_inscripcion`, `jugadores` (lista de la plantilla).
- **Respuesta especial de POST:** `{ "mensaje": "...", "estado_torneo": "...", "inscripcion": { ... } }`. Los GET usan los campos de listado descritos arriba.
- Parámetros GET: `search`, `torneo`, `equipo`, `estado_torneo`, `ordering=fecha_inscripcion|equipo__nombre`, `page`, `page_size`.
- GET `/api/inscripciones/torneos_disponibles/?equipo=ID`: `{ "equipo": "...", "cantidad": 2, "torneos": [{"id":1,"nombre":"...", "cupos_disponibles":2, ...}] }`.
- Reglas: se inscriben EQUIPOS, plantilla mínima y cupos, sin duplicados, torneo abierto. Al llenar el cupo, comienza.

#### Partidos

`/api/partidos/` GET (todos) y POST (Administrador, Operador); `/api/partidos/{id}/` GET (todos), PATCH/PUT/DELETE (Administrador, Operador).

- Entrada: `torneo` (ID en curso), `equipo_local` y `equipo_visitante` (IDs de inscritos distintos), `fecha` (`YYYY-MM-DD`).
- Respuesta: `id`, `torneo`, `nombre_torneo`, `fecha`, `estado` (`PROGRAMADO` o `FINALIZADO`), `equipo_local`, `nombre_local`, `equipo_visitante`, `nombre_visitante`, `marcador`, `resultado`, `ganador`, `perdedor`.
- Parámetros GET: `search`, `torneo`, `estado`, `equipo`, `fecha_desde`, `fecha_hasta`, `ordering=fecha|-fecha`, `page`, `page_size`.
- Reglas: equipos inscritos; no programar repetidos según las vueltas; un partido con resultado no se puede modificar ni eliminar.

#### Resultados (ruta `/api/goles/`)

`/api/goles/` GET (todos) y POST (Administrador, Operador); `/api/goles/{id}/` GET (todos), PATCH/PUT/DELETE (Administrador, Operador).

- Entrada POST: `partido` (ID programado), `goles_local`, `goles_visitante` (0–50), `anotadores` opcionales con `jugador`, `minuto` (1–130), `tipo` (`NORMAL`, `PENAL`, `AUTOGOL`).
- PATCH: `goles_local`, `goles_visitante`, `anotadores`. El partido de un resultado registrado no se cambia.
- Respuesta GET: `id`, `partido`, `torneo`, `fecha`, `equipo_local`, `equipo_visitante`, `goles_local`, `goles_visitante`, `marcador`, `resultado`, `empate`, `ganador`, `perdedor`, `anotadores`, `fecha_registro`.
- **Respuesta especial de POST:** `{ "mensaje": "...", "torneo_finalizado": false, "resultado": { ... } }` y `campeon` cuando termina el torneo.
- Parámetros GET: `torneo`, `partido`, `equipo`, `ganador`, `empate`, `ordering=partido__fecha|-partido__fecha`, `page`, `page_size`.
- Reglas: Django valida marcadores, anotadores y actualización de clasificación y campeón.

#### Estadísticas

- `GET /api/estadisticas/torneos/`: lista paginada de torneos FINALIZADOS con `torneo_id`, `torneo`, `fecha_inicio`, `fecha_fin`, `vueltas`, `equipos`, `partidos_jugados`, `campeon`.
- `GET /api/estadisticas/torneos/{id}/posiciones/`: ficha del torneo, criterio de desempate y tabla con puntos, goles, promedios y porcentajes.
- `GET /api/estadisticas/torneos/{id}/goleadores/`: `torneo`, `nota`, `goleadores` con jugador, equipo, goles, penales y partidos con gol.
- `GET /api/estadisticas/torneos/{id}/resumen/`: promedios de goles, victorias, empates, récords, máximo goleador, etc.
- `GET /api/estadisticas/partidos/`: resultados de partidos en torneos finalizados, paginados. Solo lectura para todos los roles.
