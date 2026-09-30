export const EmploymentType = {
  EMPLOYEE: 'empleado',
  PENSIONER: 'pensionado',
  FORCES: 'fuerzas',
  INDEPENDENT: 'independiente'
};

export const EMPLOYMENT_LABELS = {
  empleado: 'Empleado',
  pensionado: 'Pensionado',
  fuerzas: 'Fuerzas Armadas',
  independiente: 'Independiente'
};

const MULTIPLIERS = {
  empleado: 1.20,
  pensionado: 1.20,
  fuerzas: 1.20,
  independiente: 1.40
};

const round2 = (n) => Math.round(n * 100) / 100;

export function evaluateCreditApplication({
  declaredIncome,
  employmentType,
  creditScore,
  quantoFactor,
  requestedInstallment,
  revolvingExpenses = 0,
  nonRevolvingExpenses = 0,
  personalExpensesPct = 0.5,
  paymentCapacityMargin = 0.7,
  monthlyRatePct = 2.0,
  termMonths = 48
}) {
  const multiplier = MULTIPLIERS[employmentType] ?? 1.0;
  const finalIncome = round2(declaredIncome * multiplier);

  const personalExpenses = round2(finalIncome * personalExpensesPct);
  const totalExpenses = round2(personalExpenses + revolvingExpenses + nonRevolvingExpenses);
  const availableIncome = round2(finalIncome - totalExpenses);
  const maxAvailable = Math.max(0, availableIncome);
  const suggestedQuota = round2(maxAvailable * paymentCapacityMargin);

  let suggestedCreditLimit = 0;
  if (suggestedQuota > 0 && termMonths > 0) {
    const rate = monthlyRatePct / 100;
    const factor = Math.pow(1 + rate, termMonths);
    suggestedCreditLimit = round2(suggestedQuota * ((factor - 1) / (rate * factor)));
  }

  const isScoreValid = creditScore >= 600;
  const isQuantoValid = quantoFactor >= 1.0;
  const isCapacityValid = requestedInstallment <= suggestedQuota;

  const rejectionReasons = [];
  if (!isScoreValid) rejectionReasons.push(`Score insuficiente (${creditScore} < 600).`);
  if (!isQuantoValid) rejectionReasons.push(`Factor Quanto por debajo del mínimo (${quantoFactor} < 1.00).`);
  if (!isCapacityValid)
    rejectionReasons.push(
      `Cuota solicitada supera la capacidad de pago (${requestedInstallment.toLocaleString()} > ${suggestedQuota.toLocaleString()}).`
    );

  let status = 'APROBADO';
  if (rejectionReasons.length > 0) {
    status = (!isScoreValid || !isQuantoValid) ? 'RECHAZADO' : 'REQUIERE_REVISION';
  }

  return {
    status,
    creditScore,
    quantoFactor,
    finalIncome,
    personalExpenses,
    revolvingExpenses,
    nonRevolvingExpenses,
    totalExpenses,
    availableIncome,
    suggestedQuota,
    suggestedCreditLimit,
    requestedInstallment,
    rejectionReasons,
    rules: [
      { code: 'SCORE_MIN', label: 'Score ≥ 600', passed: isScoreValid },
      { code: 'QUANTO_MIN', label: 'Quanto ≥ 1.00', passed: isQuantoValid },
      { code: 'CAPACITY', label: 'Cuota ≤ capacidad de pago', passed: isCapacityValid }
    ]
  };
}
