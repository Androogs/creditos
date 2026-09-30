export default function Header({ title, subtitle, actions }) {
  return (
    <header className="h-16 flex items-center justify-between border-b border-slate-200 bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">{actions}</div>
    </header>
  );
}
