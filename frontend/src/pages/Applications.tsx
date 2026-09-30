import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import Card from '../components/ui/Card';
import StatusBadge from '../components/ui/StatusBadge';
import { listApplications } from '../lib/mockStore';
import { currency, dateShort } from '../lib/formatters';
import { Search } from 'lucide-react';

export default function Applications() {
  const apps = useMemo(() => listApplications(), []);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [asesor, setAsesor] = useState('');

  // saca asesores únicos del mock para no escribirlos a mano
  const asesores = useMemo(() => {
    return [...new Set(apps.map(a => a.vendedor || a.asesor).filter(Boolean))];
  }, [apps]);

  const filtered = apps.filter((a) => {
    const doc = a.documento || a.cedula || '';
    const ase = a.asesor || a.vendedor || '';
    const searchText = `${a.id} ${a.customer} ${doc} ${a.concesionario} ${ase}`.toLowerCase();

    if (q &&!searchText.includes(q.toLowerCase())) return false;
    if (status && a.status!== status) return false;
    if (asesor && ase!== asesor) return false;
    return true;
  });

  return (
    <>
      <Header title="Solicitudes" subtitle="Consulta y filtra el histórico de evaluaciones" />
      <div className="p-6 space-y-4 overflow-auto">
        <Card>
          <div className="grid sm:grid-cols-3 gap-3">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                className="input-base pl-9"
                placeholder="Buscar por ID, cliente, cédula, concesionario…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
            <select className="input-base" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Todos los estados</option>
              <option value="APROBADO">Aprobado</option>
              <option value="RECHAZADO">Rechazado</option>
              <option value="REQUIERE_REVISION">Requiere revisión</option>
            </select>
            <select className="input-base" value={asesor} onChange={(e) => setAsesor(e.target.value)}>
              <option value="">Todos los asesores</option>
              {asesores.map((nombre) => (
                <option key={nombre} value={nombre}>{nombre}</option>
              ))}
            </select>
          </div>
        </Card>

        <Card className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase text-slate-500 border-b border-slate-200">
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Solicitante</th>
                  <th className="px-5 py-3">Documento</th>
                  <th className="px-5 py-3">Teléfono</th>
                  <th className="px-5 py-3">Concesionario</th>
                  <th className="px-5 py-3">Asesor</th>
                  <th className="px-5 py-3">Fecha De Solicitud</th>
                  <th className="px-5 py-3">Score</th>
                  <th className="px-5 py-3">Cuota</th>
                  <th className="px-5 py-3">Cupo sugerido</th>
                  <th className="px-5 py-3">Estado</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((a) => (
                  <tr key={a.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium">
                      <Link to={`/solicitudes/${a.id}`} className="text-brand-600 hover:underline">{a.id}</Link>
                    </td>
                    <td className="px-5 py-3 whitespace-nowrap">{a.customer}</td>
                    <td className="px-5 py-3">{a.documento || a.cedula}</td>
                    <td className="px-5 py-3 whitespace-nowrap">{a.telefono}</td>
                    <td className="px-5 py-3 whitespace-nowrap">{a.concesionario}</td>
                    <td className="px-5 py-3 whitespace-nowrap">{a.asesor || a.vendedor}</td>
                    <td className="px-5 py-3 text-slate-600 whitespace-nowrap">{dateShort(a.createdAt)}</td>
                    <td className="px-5 py-3 font-medium">{a.creditScore}</td>
                    <td className="px-5 py-3">{currency(a.requestedInstallment)}</td>
                    <td className="px-5 py-3">{currency(a.suggestedCreditLimit)}</td>
                    <td className="px-5 py-3"><StatusBadge status={a.status} /></td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={11} className="px-5 py-10 text-center text-slate-500">Sin resultados.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </>
  );
}