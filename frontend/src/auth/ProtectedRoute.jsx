// Si no hay sesión, mandamos al usuario a la pantalla de acceso.
import {Navigate, Outlet} from 'react-router-dom';
import {useAuth} from './AuthContext.jsx';

// Esta comprobación se ejecuta antes de mostrar las pantallas privadas.
export default function ProtectedRoute() {
    const {isAuthenticated, verificando} = useAuth();

    // Mientras Django confirma la sesión no enviamos al usuario al login por error.
    if (verificando) return <p className="p-5 text-center" role="status">Verificando sesión con Django...</p>;

    // Cuando hay sesión válida se abre la ruta solicitada; de lo contrario se vuelve al acceso.
    return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
