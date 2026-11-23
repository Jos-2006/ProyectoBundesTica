// Aquí se mantiene la sesión y se consultan los permisos del usuario.
import {createContext, useCallback, useContext, useEffect, useState} from 'react';
import {api, getError} from '../api/client.js';

// Creamos un espacio compartido para que las pantallas puedan conocer la sesión sin pasarse datos entre ellas.
const AuthContext = createContext(null);

export function AuthProvider({children}) {
    // El token se recupera de la sesión del navegador cuando se vuelve a cargar la aplicación.
    const [token, setToken] = useState(() => sessionStorage.getItem('bundestica_token'));
    // Aquí se guarda lo que Django informa del usuario y sus permisos de acceso.
    const [perfil, setPerfil] = useState(null);
    const [verificando, setVerificando] = useState(Boolean(sessionStorage.getItem('bundestica_token')));

    // Cerramos la sesión quitando los datos almacenados y limpiando el usuario mostrado en pantalla.
    const logout = useCallback(() => {
        sessionStorage.removeItem('bundestica_token');
        sessionStorage.removeItem('bundestica_usuario');
        setToken(null);
        setPerfil(null);
        setVerificando(false);
    }, []);

    // Al montar la aplicación consultamos el perfil y comprobamos si el token guardado sigue siendo válido.
    useEffect(() => {
        let activo = true;
        // Sin token no tiene sentido solicitar el perfil al servidor.
        if (!token) { setVerificando(false); return; }
        // Comprobamos la sesión cada vez que se vuelve a abrir la página.
        // Esta petición obtiene los roles reales desde Django; no inventamos permisos en React.
        api.get('/auth/me/').then(({data}) => {
            if (activo) { setPerfil(data); setVerificando(false); }
        }).catch(() => { if (activo) logout(); });
        // Al desmontar el componente evitamos actualizar su estado con una respuesta tardía.
        return () => { activo = false; };
    }, [token, logout]);

    useEffect(() => {
        // Escuchamos el aviso del cliente Axios para cerrar automáticamente una sesión vencida.
        window.addEventListener('bundestica-sesion-expirada', logout);
        return () => window.removeEventListener('bundestica-sesion-expirada', logout);
    }, [logout]);

    // Primero se solicitan las credenciales a la API; luego recuperamos el perfil antes de dejar entrar al usuario.
    async function login(usuario, contrasena) {
        try {
            // Se manda usuario y contraseña a la ruta de autenticación que ya trae el backend.
            const {data} = await api.post('/auth/token/', {username: usuario, password: contrasena});
            if (!data.token) throw new Error('Django no devolvió un token.');
            // Conservamos el token únicamente en la sesión actual del navegador.
            sessionStorage.setItem('bundestica_token', data.token);
            // Después del token consultamos el perfil del usuario.
            const respuesta = await api.get('/auth/me/');
            sessionStorage.setItem('bundestica_usuario', respuesta.data.username);
            // Con el perfil recibido se habilitan o deshabilitan las acciones permitidas en los módulos.
            setPerfil(respuesta.data);
            setToken(data.token);
            setVerificando(false);
        } catch(error) {
            logout();
            throw new Error(error.response ? getError(error) : error.message);
        }
    }

    // Esta función consulta el permiso de un módulo para decidir si se muestra su formulario o sus botones.
    function puedeEditar(modulo) {
        return Boolean(perfil?.permisos?.[modulo]);
    }

    // El provider comparte el inicio y cierre de sesión con toda la aplicación.
    return <AuthContext.Provider value={{
        login, logout, puedeEditar, perfil,
        username: perfil?.username || '',
        roles: perfil?.roles || [],
        verificando,
        isAuthenticated: Boolean(token && perfil)
    }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
