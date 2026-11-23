// Aquí se piden el usuario y la contraseña para ingresar.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';

// Esta pantalla recibe las credenciales y llama al método login del contexto de autenticación.
export default function LoginPage() {

    // useNavigate permite abrir el Dashboard sin una recarga completa del navegador.
    const {login} = useAuth(); const navigate = useNavigate();

    // Los inputs son controlados para conservar lo que escribe el usuario.
    const [usuario,setUsuario]=useState('');const [contrasena,setContrasena]=useState('');

    // Se indica cuando la autenticación falla y se bloquea el botón mientras se envía.
    const [error,setError]=useState(''); const [cargando,setCargando]=useState(false);

    // Mantenemos el mismo inicio de sesión; solo cambia cómo se muestra el formulario.
    // Evitamos que el formulario recargue la página y esperamos la respuesta de Django.
    async function ingresar(evento) {
        evento.preventDefault();setError('');setCargando(true);

        // Si el login termina bien, el navegador cambia al Dashboard; si falla se muestra el motivo.
        try {await login(usuario,contrasena);navigate('/dashboard',{replace:true});}
        catch(error){setError(error.message);}finally{setCargando(false);}
    }

    // La contraseña se introduce en un campo oculto y nunca se muestra como texto normal.
    return <main className="login-screen">
        <div className="pitch-art" aria-hidden="true"><div className="pitch-lines"><span/><span/></div></div>
        <section className="login-form-area">
            <div className="login-form-wrap">
                <div className="brand"><span className="brand-mark"><i className="bi bi-crosshair2" aria-hidden="true"/></span>BundesTica</div>
                <h1>Iniciar sesión</h1>
                {error && <div className="alert alert-danger" role="alert">{error}</div>}
                <form onSubmit={ingresar}>
                    <div className="mb-3"><label className="form-label" htmlFor="login-usuario">Usuario</label>
                        <div className="input-icon-wrap"><i className="bi bi-person"/><input id="login-usuario" className="form-control" value={usuario} onChange={e=>setUsuario(e.target.value)} placeholder="Tu nombre de usuario" autoComplete="username" required/></div></div>
                    <div className="mb-4"><label className="form-label" htmlFor="login-contrasena">Contraseña</label>
                        <div className="input-icon-wrap"><i className="bi bi-lock"/><input id="login-contrasena" type="password" className="form-control" value={contrasena} onChange={e=>setContrasena(e.target.value)} placeholder="Tu contraseña" autoComplete="current-password" required/></div></div>
                    <button disabled={cargando} className="btn btn-primary w-100 login-submit"><i className="bi bi-box-arrow-in-right me-2"/>{cargando?'Ingresando...':'Entrar al sistema'}</button>
                </form>
            </div>
        </section>
    </main>;
}
