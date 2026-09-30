import { EmploymentType } from './underwritingEngine';

const emp = [EmploymentType.EMPLOYEE, EmploymentType.PENSIONER, EmploymentType.FORCES, EmploymentType.INDEPENDENT];

const CONCESIONARIOS = [
  'Suzuki Sumoto S.A.',
  'Hero Sumoto S.A.',
  'Bajaj Sumoto S.A.',
  'AKT Sumoto S.A.',
  'Honda Sumoto S.A.'
];

const ASESORES = [
  'Carlos Ruiz',
  'María Gómez',
  'Jorge Torres',
  'Luisa Fernanda Ortiz',
  'Andrés Valencia'
];

const STATUSES = ['APROBADO', 'RECHAZADO', 'REQUIERE_REVISION'];

export const MOCK_APPLICATIONS = Array.from({ length: 42 }).map((_, i) => {
  const employmentType = emp[i % emp.length];
  const declaredIncome = 1_200_000 + ((i * 137_000) % 6_500_000);
  const creditScore = 480 + ((i * 53) % 420);
  const quantoFactor = +(0.7 + ((i * 7) % 90) / 100).toFixed(2);
  const requestedInstallment = 200_000 + ((i * 91_000) % 1_800_000);
  const revolvingExpenses = (i % 3) * 180_000;
  const nonRevolvingExpenses = (i % 5) * 120_000;

  // NUEVOS CAMPOS
  const documento = `${1000000000 + ((i * 731997) % 900000000)}`;
  const telefono = `3${String(10 + (i % 90))}${String(1000000 + (i * 12345) % 9000000)}`;
  const concesionario = CONCESIONARIOS[i % CONCESIONARIOS.length];
  const asesor = ASESORES[i % ASESORES.length];
  const status = STATUSES[i % STATUSES.length];
  const suggestedCreditLimit = Math.round(declaredIncome * quantoFactor);

  return {
    id: `SOL-${String(1000 + i)}`,
    createdAt: new Date(Date.now() - i * 86400000).toISOString(),
    customer: `Cliente ${String.fromCharCode(65 + (i % 26))}${i}`,
    documento,
    telefono,
    concesionario,
    asesor,
    employmentType,
    declaredIncome,
    creditScore,
    quantoFactor,
    requestedInstallment,
    revolvingExpenses,
    nonRevolvingExpenses,
    suggestedCreditLimit,
    status
  };
});

// funciones que ya usas en la tabla
export function listApplications() {
  return MOCK_APPLICATIONS;
}

export function getApplicationById(id) {
  return MOCK_APPLICATIONS.find(a => a.id === id);
}