export default function Button({ variant = 'primary', className = '', children, ...rest }) {
  const base = variant === 'primary' ? 'btn-primary' : 'btn-ghost';
  return (
    <button className={`${base} ${className}`} {...rest}>
      {children}
    </button>
  );
}
