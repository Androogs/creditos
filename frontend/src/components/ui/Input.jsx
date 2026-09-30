export default function Input({ label, error, className = '', ...rest }) {
  return (
    <div className={className}>
      {label && <label className="label-base">{label}</label>}
      <input className="input-base" {...rest} />
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
