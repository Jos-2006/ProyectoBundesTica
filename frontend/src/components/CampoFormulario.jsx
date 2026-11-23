// Usamos un solo campo para no repetir los inputs en cada formulario.
// Dependiendo del tipo, mostramos una lista, un texto largo o un input normal.
// Un mismo componente dibuja campos para Equipos, Jugadores, Torneos y los demás formularios.
export default function CampoFormulario({campo, valor, cambiar, opciones, bloqueado=false}) {

    // Las propiedades de cada campo vienen de configuracion.js; así se evita escribir inputs repetidos.
    const {nombre, etiqueta, tipo='text', minimo, maximo, obligatorio=true, ancho='col-md-6'}=campo;

    // Según el tipo se presenta una lista, un área de texto o una entrada normal; todos conservan su valor controlado.
    return <div className={ancho}><label className="form-label" htmlFor={nombre}>{etiqueta}{obligatorio?' *':''}</label>
        {tipo==='select' ? <select id={nombre} name={nombre} className="form-select" disabled={bloqueado} value={valor ?? ''} onChange={cambiar} required={obligatorio}>
            <option value="">Seleccione...</option>{(opciones || campo.opciones || []).map(op=><option key={op.id ?? op.valor} value={op.id ?? op.valor}>{op.nombre ?? op.etiqueta}</option>)}
        </select> : tipo==='textarea' ? <textarea id={nombre} name={nombre} className="form-control" value={valor ?? ''} onChange={cambiar} required={obligatorio}/>
        : <input id={nombre} name={nombre} type={tipo} className="form-control" min={minimo} max={maximo} value={valor ?? ''} onChange={cambiar} required={obligatorio}/>}
    </div>;
}
