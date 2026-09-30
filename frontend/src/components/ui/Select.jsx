export default function Select({ label, options, error, className = '', ...rest }) {
  return (
    <div className={className}>
      {label && <label className="label-base">{label}</label>}
      <select className="input-base" {...rest}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
