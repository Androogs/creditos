import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('demo@underwriting.io');
  const [password, setPassword] = useState('demo1234');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = (e) => {
    e.preventDefault();
    if (!email || !password) return setError('Completa todos los campos.');
    setLoading(true);
    setTimeout(() => {
      localStorage.setItem('uw_auth', '1');
      navigate('/dashboard');
    }, 600);
  };

  return (
    <div className="login-wrapper">
      <main className="login">
        <section className="login__welcome">
          <div className="login__welcome-content">
            <div className="login__icon-wrapper">🛡️</div>
            <h1 className="login__heading">Bienvenido.</h1>
            <p className="login__description">Accede a tu cuenta y continuemos con tu solicitud en 5 minutos.</p>
          </div>
        </section>
        <section className="login__form-panel">
          <div className="login__content">
            <h2 className="login__form-title">Ingresa a tu Sesión</h2>
            <p className="login__form-subtitle">Ingresa tus credenciales para acceder.</p>
            <form className="login__form" onSubmit={submit}>
              <div><label className="login__label">Email / Usuario</label><input className="login__input" value={email} onChange={e=>setEmail(e.target.value)} /></div>
              <div><label className="login__label">Contraseña</label><input type="password" className="login__input" value={password} onChange={e=>setPassword(e.target.value)} /></div>
              {error && <p style={{color:'red', fontSize:'12px'}}>{error}</p>}
              <button type="submit" className="login__submit">{loading ? 'Ingresando...' : 'Ingresar'}</button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}