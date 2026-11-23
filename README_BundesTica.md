# BundesTica

BundesTica es el proyecto que hicimos para organizar torneos de fútbol. En la primera entrega construimos la API con Django REST Framework y MySQL. En esta segunda parte agregamos una interfaz en React para usar el sistema desde el navegador.

El flujo empieza al registrar los equipos y sus jugadores. Después se crea un torneo y se inscriben los equipos que cumplen con el mínimo de jugadores. Cuando el torneo está en curso se pueden programar los partidos y registrar los marcadores. Con esos resultados el sistema actualiza la tabla de posiciones y determina el campeón al finalizar.

## Cómo está organizado

- `backend_bundestica/` contiene la API, las migraciones y las reglas de negocio.
- `frontend/` contiene las pantallas, formularios y llamadas a la API.

## Qué ocupamos para correrlo

- Python 3.13 y pip.
- MySQL en ejecución y una cuenta con acceso a la base de datos.
- Node.js 24 y npm.
- Dos terminales de PowerShell, una para Django y otra para React.

## 1. Crear la base de datos

En MySQL Workbench ejecutamos:

```sql
CREATE DATABASE IF NOT EXISTS Bundestica
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Si la base ya existe, este comando conserva sus datos.

## 2. Levantar Django

Desde la raíz del proyecto, ejecutamos en la primera terminal:

```powershell
cd backend_bundestica
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

$env:USE_MYSQL = "True"
$env:MYSQL_DATABASE = "Bundestica"
$env:MYSQL_USER = "root"
$env:MYSQL_HOST = "localhost"
$env:MYSQL_PORT = "3306"
$claveMySQL = Read-Host "Contraseña de MySQL" -AsSecureString
$env:MYSQL_PASSWORD = [System.Net.NetworkCredential]::new("", $claveMySQL).Password

python manage.py check
python manage.py migrate
```

Si usamos otro nombre de base, usuario o puerto, cambiamos los valores antes de migrar. `backend_bundestica/.env.example` sirve de referencia para las variables que lee Django. Estas variables se configuran en la terminal que ejecuta el servidor.

Para crear la primera cuenta, en esa misma terminal ejecutamos:

```powershell
python manage.py createsuperuser
```

En una base destinada a pruebas, podemos cargar equipos, jugadores y torneos de ejemplo:

```powershell
python manage.py cargar_datos_demo
```

Finalmente, iniciamos Django y dejamos la terminal abierta:

```powershell
 python manage.py runserver
```

## 3. Levantar React
Antes de todo verificamos que tengamos node y npm
node -v
npm -v

Desde la raíz del proyecto, abrimos la segunda terminal y ejecutamos:

```powershell
cd frontend
npm install
npm run dev
```

Entramos a la dirección que muestra Vite, normalmente [http://localhost:5173](http://localhost:5173). El backend queda en [http://127.0.0.1:8000](http://127.0.0.1:8000). 

## Cuentas de prueba

Entramos al [panel de Django](http://127.0.0.1:8000/admin/) con el superusuario y creamos los grupos `Administrador`, `Operador` y `Consulta`. Creamos una cuenta activa para cada grupo y le asignamos únicamente su grupo. Las cuentas de prueba pueden funcionar sin acceso al panel de Django y con la opción Superusuario desmarcada.

| Usuario de ejemplo | Grupo | Qué puede hacer |
|---|---|---|
|usuario=`admin_prueba` contraseña='admin1234@@@' | Administrador | Gestiona equipos, jugadores, torneos, inscripciones, partidos y resultados. |
| usuario= `operador_prueba` contraseña= 'operador123@@'| Operador | Consulta los módulos y gestiona los partidos y sus resultados. |
| usuario= `consulta_prueba` contraseña= 'consulta123@@' | Consulta | Consulta listados y estadísticas. |

Cada operación sigue sujeta al estado del torneo y a las reglas de Django. Las contraseñas se definen en cada instalación.


## Cierre de sesión

React borra el token del navegador al salir. El backend no tiene un endpoint de revocación en este flujo, por lo que ese token puede seguir siendo válido para la API.
