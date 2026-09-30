import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

const CONFIG = {
  APROBADO: {
    Icon: CheckCircle2,
    className: 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/20',
    label: 'Aprobado'
  },
  RECHAZADO: {
    Icon: XCircle,
    className: 'bg-red-600 text-white shadow-sm shadow-red-600/20',
    label: 'Rechazado'
  },
  REQUIERE_REVISION: {
    Icon: AlertTriangle,
    className: 'bg-amber-500 text-white shadow-sm shadow-amber-500/20',
    label: 'Requiere revisión'
  }
};

export default function StatusBadge({ status }) {
  const cfg = CONFIG[status] || CONFIG.REQUIERE_REVISION;
  const Icon = cfg.Icon;

  return (
    <span
      title={cfg.label}
      className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${cfg.className}`}
    >
      <Icon size={18} strokeWidth={2.5} />
    </span>
  );
}