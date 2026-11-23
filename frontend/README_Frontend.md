# Frontend de BundesTica

Para el segundo proyecto hicimos la parte que usa la persona encargada de organizar el torneo. Desde la interfaz puede revisar qué equipos están inscritos, buscar jugadores, programar los partidos y registrar sus marcadores. El inicio muestra los conteos que devuelve la API y sirve para entrar a los módulos.

Usamos React con Vite, Bootstrap para la interfaz, React Router para cambiar de pantalla y Axios para hablar con Django. Los formularios y las tablas consultan la misma API que desarrollamos para el primer proyecto.

## Cómo correr el frontend

Primero levantamos Django como se explica en el [README principal](../README.md). Con Node.js 24 instalado, abrimos otra terminal de PowerShell desde la raíz del proyecto:

```powershell
cd frontend
npm install
npm  run dev
```

Abrimos la dirección que imprime Vite, normalmente [http://localhost:5173](http://localhost:5173).



## Qué se puede hacer en la interfaz

| Pantalla | Para qué la usamos |
|---|---|
| Inicio | Ver los conteos que devuelve la API y entrar a los módulos. |
| Equipos y Jugadores | Registrar plantillas, asignar los jugadores a un equipo y buscar o filtrar registros. |
| Torneos e Inscripciones | Configurar el torneo, inscribir equipos, revisar los cupos y consultar las posiciones. |
| Partidos y Resultados | Programar los encuentros y cargar los marcadores. |
| Estadísticas | Consultar la tabla final y los goleadores de torneos terminados. |

## Probar los perfiles

Usamos las [cuentas de prueba del README principal](../README.md#cuentas-de-prueba). Con el Administrador podemos crear y editar un equipo. Con el Operador podemos gestionar partidos y resultados. Con Consulta podemos abrir los listados y revisar los datos.


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

El login recibe un JSON con `username` y `password` y devuelve `token`. Para el resto de las solicitudes, Axios envía el encabezado `Authorization: Token <token>`. El perfil devuelve `username`, `roles` y `permisos`.


| Código | Cuándo se usa |
|---|---|
| `200`, `201`, `204` | Consulta o edición correcta, creación y eliminación, respectivamente. |
| `400` | Los datos no cumplen una validación. |
| `401` / `403` | Falta autenticación o el perfil no tiene autorización para esa acción. |
| `404` / `409` | El registro no existe o la operación entra en conflicto con una regla del sistema. |
