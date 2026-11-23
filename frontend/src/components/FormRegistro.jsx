// Este formulario sirve tanto para registrar como para editar datos.
import { useEffect, useState } from 'react';
import CampoFormulario from './CampoFormulario.jsx';
// Se recibe un registro cuando hay que editarlo; si no existe, el formulario sirve para crear uno nuevo.
export default function FormRegistro({registro, inicial, campos, opciones={}, guardar, cancelar, guardando, titulo}) {
    // Guardamos temporalmente lo que el usuario escribe sin enviarlo todavía a Django.
    const [form,setForm]=useState({...inicial});
    // Al elegir Editar se rellenan los campos con los datos existentes; al cancelar se recuperan los valores iniciales.
    useEffect(()=>{setForm(registro ? Object.fromEntries(Object.keys(inicial).map(k=>[k,registro[k] ?? inicial[k]])) : {...inicial});},[registro,inicial]);
    // Se actualiza solo el campo que cambió, manteniendo los demás valores del formulario.
    function cambiar(evento){const {name,value}=evento.target;setForm(actual=>({...actual,[name]:value}));}
    // Antes de enviar convertimos los campos numéricos al tipo esperado.
    // Primero evitamos la recarga normal de la página, luego preparamos el objeto que se mandará a la API.
    async function enviar(evento){evento.preventDefault(); const datos={};
        // Cada campo se revisa según su tipo para conservar números como números y limpiar espacios en los textos.
        campos.forEach(c=>{
            const valor = form[c.nombre];
            if ((c.tipo==='number'||(c.tipo==='select'&&c.numero)) && valor==='') {
                datos[c.nombre] = null;
            } else if (c.tipo==='number'||(c.tipo==='select'&&c.numero)) {
                datos[c.nombre] = Number(valor);
            } else if (typeof valor === 'string') {
                datos[c.nombre] = valor.trim();
            } else {
                datos[c.nombre] = valor;
            }
        });
        // La página principal decide si hace POST o PATCH; aquí solo se reinicia el formulario después de crear correctamente.
        const correcto=await guardar(datos);if(correcto&&!registro)setForm({...inicial});
    }
    // El encabezado cambia entre Registrar y Editar, pero el formulario y sus validaciones son los mismos.
    return <section className="card form-panel border-0 shadow-sm mb-4"><div className="card-body p-4">
        <div className="panel-heading"><span className="panel-heading-icon"><i className={`bi ${registro?'bi-pencil-square':'bi-plus-circle-fill'}`}/></span>
            <div><h2>{registro?'Editar':'Registrar'} {titulo.toLowerCase()}</h2><small>{registro?'Modifica los datos y guarda los cambios.':'Completa los campos para agregar un registro.'}</small></div>
        </div>
        <form onSubmit={enviar}><div className="row g-3">{campos.map(c=><CampoFormulario key={c.nombre} campo={c} valor={form[c.nombre]} cambiar={cambiar} opciones={opciones[c.nombre]} bloqueado={Boolean(registro && titulo==='Inscripción' && c.nombre==='torneo')}/>)}</div>
            <div className="form-actions"><button type="submit" disabled={guardando} className="btn btn-primary"><i className="bi bi-check-circle me-2"/>{guardando?'Guardando...':registro?'Guardar cambios':'Registrar'}</button>
                {registro&&<button type="button" className="btn btn-outline-secondary" onClick={cancelar}>Cancelar</button>}
            </div>
        </form>
    </div></section>;
}
