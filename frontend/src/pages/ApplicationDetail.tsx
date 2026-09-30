import { useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import Header from '../components/layout/Header';
import Card from '../components/ui/Card';
import StatusBadge from '../components/ui/StatusBadge';
import { getApplication } from '../lib/mockStore';
import { currency, dateShort } from '../lib/formatters';
import { ArrowLeft, CheckCircle2, XCircle, AlertTriangle, User, Building2, CreditCard, FileImage, Video, Database, Eye, Download } from 'lucide-react';

export default function ApplicationDetail() {
  const { id } = useParams();
  const app = getApplication(id);
  const [jsonTab, setJsonTab] = useState('datacredito');

  if (!app) {
    return (
      <>
        <Header title="Solicitud no encontrada" />
        <div className="p-6">
          <Link to="/solicitudes" className="btn-ghost"><ArrowLeft size={16} /> Volver</Link>
        </div>
      </>
    );
  }

  const docs = app.documentos || {
    cedulaFrente: 'https://placehold.co/600x380?text=CEDULA+FRONTAL',
    cedulaDorso: 'https://placehold.co/600x380?text=CEDULA+DORSO',
    videoSala: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
    datacredito: { score: app.creditScore, obligaciones: 2, mora: 0, mensaje: 'JSON de ejemplo - Reemplazar con real de Experian' },
    ingresos: { ingreso_validado: app.finalIncome, confianza: 0.89, mensaje: 'JSON de ejemplo - Valida Ingresos' }
  };

  const documento = app.documento || app.cedula;
  const asesor = app.asesor || app.vendedor;

  return (
    <>
      <Header
        title={`Solicitud ${app.id}`}
        subtitle={`${app.customer} · ${documento}`}
        actions={<Link to="/solicitudes" className="btn-ghost"><ArrowLeft size={16} /> Volver</Link>}
      />
      <div className="p-6 space-y-6 overflow-auto max-w-6xl mx-auto w-full">
        
        <Card className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-4">
            <StatusBadge status={app.status} />
            <div>
              <p className="text-xs uppercase text-slate-500">Resultado</p>
              <p className="font-semibold text-slate-900 capitalize">{(app.status||'').replace('_',' ').toLowerCase()}</p>
            </div>
          </div>
          <div className="flex gap-8">
            <div className="text-right">
              <p className="text-xs uppercase text-slate-500">Score</p>
              <p className="text-2xl font-bold text-slate-900">{app.creditScore}</p>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase text-slate-500">Fecha</p>
              <p className="text-sm font-medium text-slate-900">{dateShort(app.createdAt)}</p>
            </div>
          </div>
        </Card>

        <div className="grid sm:grid-cols-3 gap-4">
          <Metric label="Cupo sugerido" value={currency(app.suggestedCreditLimit)} />
          <Metric label="Cuota máxima soportada" value={currency(app.suggestedQuota)} />
          <Metric label="Cuota solicitada" value={currency(app.requestedInstallment)} />
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="font-semibold mb-4 flex items-center gap-2"><User size={18}/> Datos personales</h3>
            <dl className="space-y-1 text-sm">
              <Row k="Nombre" v={app.customer} />
              <Row k="Documento" v={documento} />
              <Row k="Teléfono" v={app.telefono} />
              <Row k="Ingresos declarados" v={currency(app.declaredIncome)} />
              <Row k="Ingresos admitidos" v={currency(app.finalIncome)} />
            </dl>
          </Card>
          <Card>
            <h3 className="font-semibold mb-4 flex items-center gap-2"><Building2 size={18}/> Datos comerciales</h3>
            <dl className="space-y-1 text-sm">
              <Row k="Concesionario" v={app.concesionario} />
              <Row k="Asesor" v={asesor} />
              <Row k="Fecha" v={dateShort(app.createdAt)} />
              <Row k="ID" v={app.id} />
            </dl>
          </Card>
        </div>

        {/* NUEVA SECCIÓN DE DOCUMENTOS */}
        <Card>
          <h3 className="font-semibold text-slate-900 mb-5 flex items-center gap-2"><FileImage size={18}/> Documentos del solicitante</h3>
          <div className="grid md:grid-cols-3 gap-6">
            
            {/* Cédula Frente */}
            <div className="space-y-2">
              <p className="text-xs uppercase text-slate-500 font-medium">Cédula - Anverso</p>
              <div className="group relative rounded-xl overflow-hidden border border-slate-200 bg-slate-50">
                <img src={docs.cedulaFrente} alt="Cedula frente" className="w-full h-48 object-cover" />
                <a href={docs.cedulaFrente} target="_blank" rel="noreferrer" className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-sm gap-2 transition">
                  <Eye size={16}/> Ver ampliado
                </a>
              </div>
            </div>

            {/* Cédula Dorso */}
            <div className="space-y-2">
              <p className="text-xs uppercase text-slate-500 font-medium">Cédula - Reverso</p>
              <div className="group relative rounded-xl overflow-hidden border border-slate-200 bg-slate-50">
                <img src={docs.cedulaDorso} alt="Cedula dorso" className="w-full h-48 object-cover" />
                <a href={docs.cedulaDorso} target="_blank" rel="noreferrer" className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-sm gap-2 transition">
                  <Eye size={16}/> Ver ampliado
                </a>
              </div>
            </div>

            {/* Video Sala */}
            <div className="space-y-2">
              <p className="text-xs uppercase text-slate-500 font-medium flex items-center gap-1"><Video size={14}/> Video en sala - Concesionario</p>
              <div className="rounded-xl overflow-hidden border border-slate-200 bg-black">
                <video controls className="w-full h-48 object-cover" src={docs.videoSala} />
              </div>
              <p className="text-[11px] text-slate-500">Evidencia de presencia del cliente en sala.</p>
            </div>
          </div>
        </Card>

        {/* JSON Datacrédito Experian */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2"><Database size={18}/> DataCrédito Experian - JSON</h3>
            <div className="flex bg-slate-100 rounded-full p-1 text-xs">
              <button onClick={() => setJsonTab('datacredito')} className={`px-3 py-1 rounded-full ${jsonTab==='datacredito' ? 'bg-white shadow font-medium' : 'text-slate-500'}`}>Historial Crediticio</button>
              <button onClick={() => setJsonTab('ingresos')} className={`px-3 py-1 rounded-full ${jsonTab==='ingresos' ? 'bg-white shadow font-medium' : 'text-slate-500'}`}>Valor Ingreso</button>
            </div>
          </div>

          <div className="rounded-xl bg-slate-950 text-slate-100 p-4 overflow-auto max-h-[380px]">
            <div className="flex justify-between items-center mb-2 text-[11px] text-slate-400">
              <span>{jsonTab==='datacredito' ? 'datacredito_historial.json' : 'datacredito_valida_ingresos.json'}</span>
              <button onClick={() => {
                const blob = new Blob([JSON.stringify(jsonTab==='datacredito' ? docs.datacredito : docs.ingresos, null, 2)], {type:'application/json'});
                const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=`${id}_${jsonTab}.json`; a.click();
              }} className="flex items-center gap-1 hover:text-white"><Download size={12}/> Descargar</button>
            </div>
            <pre className="text-xs leading-relaxed whitespace-pre-wrap">
{JSON.stringify(jsonTab==='datacredito' ? docs.datacredito : docs.ingresos, null, 2)}
            </pre>
          </div>
        </Card>

        <div className="grid lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="font-semibold mb-4 flex items-center gap-2"><CreditCard size={18}/> Capacidad</h3>
            <dl className="grid sm:grid-cols-2 gap-x-8 gap-y-1 text-sm">
              <Row k="Ingreso admitido" v={currency(app.finalIncome)} />
              <Row k="Gastos revolving" v={currency(app.revolvingExpenses)} />
              <Row k="Gastos no revolving" v={currency(app.nonRevolvingExpenses)} />
              <Row k="Disponible" v={currency(app.availableIncome)} highlight />
            </dl>
          </Card>
          <Card>
            <h3 className="font-semibold mb-4">Reglas</h3>
            <ul className="space-y-2">
              {app.rules?.map((r) => (
                <li key={r.code} className="flex gap-3 text-sm">
                  {r.passed ? <CheckCircle2 size={18} className="text-emerald-600" /> : <XCircle size={18} className="text-red-600" />}
                  <span>{r.label}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>

        {app.rejectionReasons?.length > 0 && (
          <Card className="border-amber-200 bg-amber-50/40">
            <h3 className="font-semibold text-amber-900 mb-3 flex items-center gap-2"><AlertTriangle size={18}/> Causales</h3>
            <ul className="list-disc pl-5 text-sm text-amber-900 space-y-1">
              {app.rejectionReasons.map((r,i) => <li key={i}>{r}</li>)}
            </ul>
          </Card>
        )}
      </div>
    </>
  );
}

function Metric({ label, value }) {
  return (<Card><p className="text-xs uppercase text-slate-500">{label}</p><p className="mt-2 text-xl font-bold">{value}</p></Card>);
}
function Row({ k, v, highlight }) {
  return (<div className="flex justify-between border-b border-slate-100 py-2.5 text-sm"><dt className="text-slate-500">{k}</dt><dd className={`font-medium ${highlight ? 'text-emerald-700 font-bold' : 'text-slate-900'}`}>{v}</dd></div>);
}