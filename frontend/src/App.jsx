// Aquí dejo las rutas que llevan a las pantallas del sistema.
import {BrowserRouter, Navigate, Route, Routes} from 'react-router-dom';
import {AuthProvider, useAuth} from './auth/AuthContext.jsx';
import ProtectedRoute from './auth/ProtectedRoute.jsx';
import AppLayout from './components/AppLayout.jsx';
import LoginPage from './pages/LoginPage.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Equipos from './pages/Equipos.jsx';
import Jugadores from './pages/Jugadores.jsx';
import Torneos from './pages/Torneos.jsx';
import Inscripciones from './pages/Inscripciones.jsx';
import Partidos from './pages/Partidos.jsx';
import Resultados from './pages/Resultados.jsx';
import Estadisticas from './pages/Estadisticas.jsx';

// Evitamos mostrar el formulario de acceso a alguien que ya inició sesión.
function LoginRoute() {
    const {isAuthenticated, verificando} = useAuth();
    if (verificando) return <p className="p-5 text-center">Verificando sesión...</p>;
    return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />;
}

// Aquí quedan reunidas las rutas para que el sistema cambie de pantalla sin recargar el navegador.
export default function App() {

    // Primero colocamos el contexto de sesión, luego el enrutador y finalmente las pantallas protegidas.
    return <AuthProvider><BrowserRouter><Routes>
        <Route path="/login" element={<LoginRoute />}/>
        <Route element={<ProtectedRoute />}><Route element={<AppLayout />}>
            <Route path="/dashboard" element={<Dashboard />}/>
            <Route path="/equipos" element={<Equipos />}/>
            <Route path="/jugadores" element={<Jugadores />}/>
            <Route path="/torneos" element={<Torneos />}/>
            <Route path="/inscripciones" element={<Inscripciones />}/>
            <Route path="/partidos" element={<Partidos />}/>
            <Route path="/resultados" element={<Resultados />}/>
            <Route path="/estadisticas" element={<Estadisticas />}/>
        </Route></Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />}/>
    </Routes></BrowserRouter></AuthProvider>;
}
