import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import { EMPLOYMENT_LABELS, EmploymentType } from '../lib/underwritingEngine';
import { createApplication } from '../lib/mockStore';
import { ArrowRight } from 'lucide-react';

const initial = {
  customer: '',
  declaredIncome: 1_750_905,
  employmentType: EmploymentType.EMPLOYEE,
  creditScore: 661,
  quantoFactor: 1.38,
  requestedInstallment: 460_120,
  revolvingExpenses: 546_000,
  nonRevolvingExpenses: 0
};

export default function NewApplication() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initial);
  const [errors, setErrors] = useState({});

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const validate = () => {
    const e = {};
    if (!form.customer.trim()) e.customer = 'Ingresa el nombre del cliente';
    if (+form.declaredIncome <= 0) e.declaredIncome = 'Debe ser mayor a 0';
    if (+form.creditScore < 0 || +form.creditScore > 1000) e.creditScore = 'Rango 0-1000';
    if (+form.quantoFactor < 0) e.quantoFactor = 'Valor inválido';
    if (+form.requestedInstallment <= 0) e.requestedInstallment = 'Debe ser mayor a 0';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const submit = (ev) => {
    ev.preventDefault();
    if (!validate()) return;
    const app = createApplication({
      customer: form.customer,
      declaredIncome: +form.declaredIncome,
      employmentType: form.employmentType,
      creditScore: +form.creditScore,
      quantoFactor: +form.quantoFactor,
      requestedInstallment: +form.requestedInstallment,
      revolvingExpenses: +form.revolvingExpenses,
      nonRevolvingExpenses: +form.nonRevolvingExpenses
    });
    navigate(`/solicitudes/${app.id}`);
  };

  return (
    <>
      <Header title="Nueva simulación" subtitle="Ingresa los datos para evaluar la solicitud" />
      <div className="p-6 overflow-auto">
        <form onSubmit={submit} className="max-w-3xl mx-auto space-y-6">
          <Card>
            <h3 className="font-semibold text-slate-900 mb-4">Datos del solicitante</h3>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input label="Cliente" value={form.customer} onChange={update('customer')} error={errors.customer} placeholder="Nombre del cliente" />
              <Select
                label="Tipo de empleo"
                value={form.employmentType}
                onChange={update('employmentType')}
                options={Object.entries(EMPLOYMENT_LABELS).map(([value, label]) => ({ value, label }))}
              />
              <Input label="Ingreso declarado (COP)" type="number" value={form.declaredIncome} onChange={update('declaredIncome')} error={errors.declaredIncome} />
              <Input label="Score crediticio" type="number" value={form.creditScore} onChange={update('creditScore')} error={errors.creditScore} />
            </div>
          </Card>

          <Card>
            <h3 className="font-semibold text-slate-900 mb-4">Variables de riesgo y capacidad</h3>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input label="Factor Quanto" type="number" step="0.01" value={form.quantoFactor} onChange={update('quantoFactor')} error={errors.quantoFactor} />
              <Input label="Cuota solicitada (COP)" type="number" value={form.requestedInstallment} onChange={update('requestedInstallment')} error={errors.requestedInstallment} />
              <Input label="Gastos revolving (COP)" type="number" value={form.revolvingExpenses} onChange={update('revolvingExpenses')} />
              <Input label="Gastos no revolving (COP)" type="number" value={form.nonRevolvingExpenses} onChange={update('nonRevolvingExpenses')} />
            </div>
          </Card>

          <div className="flex justify-end gap-3">
            <button type="button" className="btn-ghost" onClick={() => navigate('/dashboard')}>Cancelar</button>
            <button type="submit" className="btn-primary">
              Evaluar solicitud <ArrowRight size={16} />
            </button>
          </div>
        </form>
      </div>
    </>
  );
}