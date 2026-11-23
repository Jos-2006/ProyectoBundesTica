// Este archivo inicia React y carga los estilos generales.
import React from 'react';
import ReactDOM from 'react-dom/client';

// Bootstrap se carga una sola vez para que los formularios y las tablas usen sus clases.
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

// Este archivo contiene los estilos particulares de BundesTica, además de los de Bootstrap.
import './styles.css';
import App from './App.jsx';

// Montamos la aplicación dentro del elemento root que está definido en index.html.
ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
