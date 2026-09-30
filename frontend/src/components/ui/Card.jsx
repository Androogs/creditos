export default function Card({ className = '', children }) {
  return <div className={`card p-5 ${className}`}>{children}</div>;
}
