// Aquí se ingresan los goles y, si corresponde, los anotadores.
import { useEffect, useState } from 'react';

// Estos son los valores que aparecen cuando todavía no se está registrando ningún resultado.
const vacio={partido:'',goles_local:0,goles_visitante:0};

// Recibimos partidos y jugadores desde la página; el formulario no consulta la API directamente.
export default function FormResultado({registro,partidos,jugadores,guardar,cancelar,guardando}){

    // Se guardan por separado el marcador y la lista de personas que anotaron.
    const [form,setForm]=useState(vacio);const [anotadores,setAnotadores]=useState([]);
    
    // Si se selecciona un resultado para corregir, recuperamos también sus anotadores anteriores.
    useEffect(()=>{setForm(registro?{partido:registro.partido,goles_local:registro.goles_local,goles_visitante:registro.goles_visitante}:{...vacio});
        setAnotadores(registro?.anotadores?.map(a=>({jugador:a.jugador,minuto:a.minuto,tipo:a.tipo}))||[]);},[registro]);
    // Localizamos el partido elegido para saber cuáles equipos participan.
    const partido=partidos.find(p=>p.id===Number(form.partido));
    // El selector de goleadores muestra solamente a los jugadores de los equipos de ese partido.
    const disponibles=jugadores.filter(j=>!partido||[partido.equipo_local,partido.equipo_visitante].includes(j.equipo));
    // Preparamos el marcador y la lista de anotadores antes de guardarlos.
    // Los valores del formulario llegan como texto; antes de guardar pasamos IDs, goles y minutos a números.
    async function enviar(e){e.preventDefault();const datos={partido:Number(form.partido),goles_local:Number(form.goles_local),goles_visitante:Number(form.goles_visitante),anotadores:anotadores.map(a=>({jugador:Number(a.jugador),minuto:Number(a.minuto),tipo:a.tipo}))};
        // Si no hay anotadores, se puede enviar únicamente el marcador.
        // Al editar, no enviamos una lista vacía si ya había anotadores.
        // Cuando no se ingresaron anotadores, se conserva el comportamiento del backend para guardar el marcador.
        if (!anotadores.length && (!registro || !registro.anotadores?.length)) delete datos.anotadores;
        // La página se encarga de guardar y notificar; el formulario se limpia si se creó un resultado nuevo.
        const bien=await guardar(datos);if(bien&&!registro){setForm({...vacio});setAnotadores([]);}}
    // Cambiamos únicamente el jugador, minuto o tipo de gol de la fila seleccionada.
    function cambiarAnotador(i,campo,valor){setAnotadores(actual=>actual.map((a,j)=>i===j?{...a,[campo]:valor}:a));}
    // La parte superior recoge el marcador y las filas de abajo permiten agregar o quitar anotadores.
    return <section className="card border-0 shadow-sm mb-4"><div className="card-body p-4">
        <div className="panel-heading"><span className="panel-heading-icon"><i className="bi bi-flag-fill"/></span>
            <div><h2>{registro?'Corregir':'Registrar'} resultado</h2><small>Selecciona el partido y da su resultado.</small></div>
        </div>
        <p className="result-notice mb-3">Si conoces a los anotadores, asiganales sus goles correspondientes</p>
        <form onSubmit={enviar}><div className="row g-3"><div className="col-md-12"><label className="form-label" htmlFor="resultado-partido">Partido *</label>
            <select id="resultado-partido" className="form-select" disabled={Boolean(registro)} required value={form.partido} onChange={e=>{setForm(f=>({...f,partido:e.target.value}));setAnotadores([]);}}>
                <option value="">Seleccione...</option>{partidos.map(p=><option key={p.id} value={p.id}>{p.nombre_torneo}: {p.nombre_local} vs {p.nombre_visitante} ({p.fecha})</option>)}</select></div>
            {['goles_local','goles_visitante'].map(c=><div className="col-md-6" key={c}><label className="form-label">{c==='goles_local'?'Goles local':'Goles visitante'}</label><input className="form-control" type="number" min="0" max="50" value={form[c]} onChange={e=>setForm(f=>({...f,[c]:e.target.value}))} required/></div>)}
        </div><hr/><div className="d-flex align-items-center justify-content-between mb-2"><h3 className="h6">Anotadores (opcional)</h3><button type="button" className="btn btn-outline-secondary btn-sm" onClick={()=>setAnotadores(a=>[...a,{jugador:'',minuto:1,tipo:'NORMAL'}])}>Agregar anotador</button></div>
        {anotadores.map((a,i)=><div key={i} className="row g-2 align-items-end mb-2"><div className="col-md-5"><label className="form-label">Jugador</label><select className="form-select" value={a.jugador} onChange={e=>cambiarAnotador(i,'jugador',e.target.value)} required><option value="">Seleccione...</option>{disponibles.map(j=><option key={j.id} value={j.id}>{j.nombre} ({j.nombre_equipo})</option>)}</select></div><div className="col-md-2"><label className="form-label">Minuto</label><input className="form-control" type="number" min="1" max="130" value={a.minuto} onChange={e=>cambiarAnotador(i,'minuto',e.target.value)} required/></div><div className="col-md-3"><label className="form-label">Tipo</label><select className="form-select" value={a.tipo} onChange={e=>cambiarAnotador(i,'tipo',e.target.value)}><option value="NORMAL">Normal</option><option value="PENAL">Penal</option><option value="AUTOGOL">Autogol</option></select></div><div className="col-md-2"><button type="button" className="btn btn-outline-danger btn-sm" onClick={()=>setAnotadores(a=>a.filter((_,j)=>j!==i))}>Quitar</button></div></div>)}
        <div className="form-actions"><button className="btn btn-primary" disabled={guardando}><i className="bi bi-check-circle me-2"/>{guardando?'Guardando...':'Guardar resultado'}</button>{registro&&<button type="button" className="btn btn-outline-secondary" onClick={cancelar}>Cancelar</button>}</div>
        </form></div></section>;
}
