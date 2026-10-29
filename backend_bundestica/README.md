# Bundestica – Sistema de gestión de torneos de fútbol

## Descripción del proyecto

Bundestica es un sistema desarrollado con Django, Django REST Framework y MySQL, diseñado para facilitar la organización y administración de torneos de fútbol.

La aplicación permite registrar equipos y jugadores, gestionar inscripciones, programar partidos y guardar los resultados de cada encuentro. Los torneos se desarrollan mediante el formato de liga, donde todos los equipos se enfrentan entre sí, ya sea a una sola vuelta o con partidos de ida y vuelta.

El sistema verifica que los equipos cumplan con los requisitos de inscripción y, cuando se completa el cupo de participantes, el torneo cambia automáticamente a EN CURSO. Una vez registrados todos los resultados, el torneo pasa a FINALIZADO y se determina el campeón.

La información técnica más detallada se encuentra en el archivo DOCUMENTACION.md.

## 1. Requisitos

Para ejecutar el proyecto se necesitan las siguientes herramientas:

- Python 3.13.
- MySQL 8.0 o superior.
- Django y Django REST Framework.
- Las dependencias incluidas en requirements.txt.

## 2. Instalación

Primero se debe descargar el proyecto y acceder a la carpeta backend_bundestica.

Después, se crea un entorno virtual con el siguiente comando:

`python -m venv .venv`

Para activarlo en Windows:

`.venv\Scripts\activate`

Finalmente, se instalan las dependencias:

`pip install -r requirements.txt`

Si ocurre algún problema durante la instalación de mysqlclient, se recomienda actualizar pip y volver a intentarlo.

## 3. Configuración de la base de datos

El proyecto trabaja con MySQL y utiliza una base de datos llamada Bundestica. La conexión se encuentra configurada en el archivo settings.py, con el usuario root, contraseña root y puerto 3306.

Para crear la base de datos se utiliza:

`CREATE DATABASE Bundestica CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`

Para activar MySQL desde PowerShell:

`$env:USE_MYSQL="True"`


## 4. Migraciones y usuarios

Una vez configurada la base de datos, se deben ejecutar las migraciones para crear las tablas necesarias:

`python manage.py migrate`

Después, se crea el usuario administrador:

`python manage.py createsuperuser`

El proyecto también permite generar información de prueba mediante:

`python manage.py cargar_datos_demo`

Este comando crea cuatro equipos, veinticuatro jugadores y dos torneos para comprobar el funcionamiento del sistema.

## 5. Roles y permisos

Bundestica maneja tres tipos de usuarios, cada uno con diferentes responsabilidades.

**Administrador:** tiene acceso completo al sistema. Puede gestionar equipos, jugadores, torneos, inscripciones, partidos y resultados.

**Operador:** se encarga de programar los encuentros y registrar los marcadores de los partidos.

**Consulta:** únicamente puede visualizar la información y las estadísticas, sin realizar modificaciones.

Los roles se configuran mediante los grupos del panel de administración de Django. El superusuario tiene los mismos permisos que un administrador.

## 6. Ejecución del sistema

Para iniciar el servidor se utiliza:

`python manage.py runserver`

La aplicación estará disponible en:

http://127.0.0.1:8000/

Para trabajar con la API desde Postman es necesario obtener un token de autenticación mediante la ruta:

`POST /api/auth/token/`

Se envían el nombre de usuario y la contraseña. Después, el token obtenido debe incluirse en las solicitudes para que el sistema pueda identificar al usuario y verificar sus permisos.

## 7. Pruebas automatizadas

El proyecto cuenta con pruebas que permiten comprobar el funcionamiento de las diferentes operaciones y reglas del sistema.

Para ejecutarlas se utiliza:

`python manage.py test`

Según la documentación del proyecto, se realizaron 100 pruebas satisfactoriamente. Estas incluyen la gestión de registros, validación de permisos, manejo de errores, filtros, paginación y funcionamiento del panel administrativo.

Los resultados se encuentran en el archivo evidencias/resultado_pruebas.txt.

## 8. Funcionamiento de los torneos

El proceso de administración de un torneo se desarrolla de la siguiente manera:

1. **Registro de equipos y jugadores:** se crean los equipos y se asignan sus jugadores. Cada jugador puede pertenecer solamente a un equipo.

2. **Creación del torneo:** se establece el nombre, las fechas, el número máximo de equipos, el mínimo de jugadores y la cantidad de vueltas.

3. **Inscripciones:** se registran los equipos que cumplen con los requisitos. Cuando se completa el cupo, el torneo comienza automáticamente.

4. **Programación de partidos:** se organizan los enfrentamientos entre equipos inscritos, evitando partidos repetidos que no correspondan al formato del torneo.

5. **Registro de resultados:** se ingresan los goles de ambos equipos y el sistema determina automáticamente al ganador o si ocurrió un empate. También permite registrar los goleadores.

6. **Finalización:** cuando todos los partidos correspondientes tienen sus resultados registrados, el torneo finaliza y se determina el campeón.

7. **Estadísticas:** se pueden consultar las posiciones, puntos, victorias, empates, derrotas y goles de los equipos.

Todas estas operaciones pueden realizarse desde el panel de administración de Django o mediante la API REST utilizando Postman.

### Principales rutas de la API

| Función | Ruta |
|---|---|
| Registrar equipos | POST /api/equipos/ |
| Registrar jugadores | POST /api/jugadores/ |
| Crear torneos | POST /api/torneos/ |
| Inscribir equipos | POST /api/inscripciones/ |
| Programar partidos | POST /api/partidos/ |
| Registrar resultados | POST /api/goles/ |
| Consultar posiciones | GET /api/torneos/{id}/tabla/ |
| Consultar estadísticas finales | GET /api/estadisticas/torneos/{id}/posiciones/ |

## 9. Limitaciones del sistema

Actualmente, Bundestica solo permite organizar torneos de liga, por lo que no incluye competiciones de eliminación directa.

El sistema tampoco registra tarjetas, sustituciones ni asistencias. Además, los jugadores de un equipo no pueden modificarse mientras este participa en un torneo en curso.

Los resultados pueden corregirse mientras el torneo está activo, pero quedan bloqueados cuando finaliza. Tampoco se permite registrar marcadores de partidos cuya fecha todavía no ha llegado.

Para los desempates se consideran los puntos, la diferencia de goles, los goles a favor, los partidos ganados y finalmente el nombre del equipo.

## Conclusión

Bundestica es una herramienta que permite administrar torneos de fútbol de manera organizada y sencilla. Gracias a sus funciones automatizadas, facilita el control de participantes, partidos, resultados y estadísticas.

Su desarrollo con Django y Django REST Framework permite gestionar la información tanto desde un panel administrativo como mediante una API REST, ofreciendo una solución funcional para la organización de competiciones deportivas.