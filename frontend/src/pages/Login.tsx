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
    <>
    <style>{`
      .login-wrapper { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%); padding: 2rem; font-family: system-ui; }
      .login { display: grid; grid-template-columns: 1fr 1fr; width: 100%; max-width: 1000px; min-height: 600px; border-radius: 24px; overflow: hidden; background: #ffffff; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.15); }
      .login__welcome { position: relative; display: flex; flex-direction: column; justify-content: space-between; padding: 3rem 2rem; background: #0a0e27; color: #fff; }
      .login__welcome-content { display: flex; flex-direction: column; align-items: center; text-align: center; margin-top: 2rem; }
      .login__icon-wrapper { display: flex; align-items: center; justify-content: center; width: 5rem; height: 5rem; margin-bottom: 1.5rem; border: 2px solid rgba(255,255,255,0.2); border-radius: 50%; background: rgba(255,255,255,0.05); }
      .login__shield-icon { width: 2.5rem; height: 2.5rem; }
      .login__heading { margin: 0 0 1rem; font-size: 2rem; font-weight: 700; }
      .login__description { max-width: 24rem; color: #a0aec0; font-size: 1rem; line-height: 1.5; }
      .login__welcome-image { display: flex; justify-content: center; margin-top: 2rem; }
      .login__dashboard-mockup { display: flex; width: 100%; max-width: 320px; height: 160px; border-radius: 8px; background: #fff; overflow: hidden; }
      .mockup-sidebar { width: 15%; background: #1a1f3a; }
      .mockup-content { flex: 1; padding: 1rem; background: #f8fafc; }
      .mockup-header { height: 15px; width: 40%; background: #e2e8f0; border-radius: 4px; margin-bottom: .75rem; }
      .mockup-charts, .mockup-table { height: 40px; background: #e2e8f0; border-radius: 4px; margin-bottom: .75rem; }
      .login__form-panel { display: flex; align-items: center; justify-content: center; padding: 3rem 2rem; }
      .login__content { display: flex; flex-direction: column; width: 100%; max-width: 360px; }
      .login__form-header { margin-bottom: 1.5rem; }
      .login__form-title { margin: 0 0 .5rem; color: #1d2939; font-size: 1.25rem; font-weight: 700; }
      .login__form-subtitle { margin: 0; color: #667085; font-size: .85rem; }
      .login__form { display: flex; flex-direction: column; gap: 1.25rem; }
      .login__label { color: #475467; font-size: .8rem; font-weight: 600; }
      .login__input { width: 100%; padding: .875rem 1rem; border: 1px solid transparent; border-radius: 8px; background: #f4f6f8; color: #1d2939; font-size: .9rem; }
      .login__input:focus { background: #fff; border-color: #099dd7; outline: none; box-shadow: 0 0 0 3px rgba(9,157,215,0.15); }
      .login__remember { display: flex; align-items: center; gap: .5rem; color: #667085; font-size: .85rem; cursor: pointer; }
      .login__submit { padding: .875rem; border: none; border-radius: 8px; background: #1a1b41; color: #fff; font-weight: 600; cursor: pointer; }
      .login__submit:hover { background: #2a2b5e; }
      .login__credit { margin-top: 2.5rem; color: #98a2b3; font-size: .7rem; text-align: center; }
      @media (max-width: 850px) { .login { grid-template-columns: 1fr; } .login__welcome-image { display: none; } }
    `}</style>

    <div className="login-wrapper">
      <main className="login">
        <section className="login__welcome">
          <div className="login__welcome-content">
            <div>
              <img
            src="/pacifico-blancos.png"
            alt="Inversiones Pacífico"
            className="h-36 w-auto object-contain flex-1"
          />
            </div>
            <h1 className="login__heading">Bienvenido.</h1>
            <p className="login__description">Accede a tu cuenta y continuemos con tu solicitud de crédito en 5 minutos.</p>
          </div>
          <div className="login__welcome-image">
            <div className="login__dashboard-mockup"><div className="mockup-sidebar"></div><div className="mockup-content"><div className="mockup-header"></div><div className="mockup-charts"></div><div className="mockup-table"></div></div></div>
          </div>
        </section>
        <section className="login__form-panel">
          <div className="login__content">
            <div className="login__form-header">
              <h2 className="login__form-title">Ingresa a tu Sesión</h2>
              <p className="login__form-subtitle">Ingresa tus credenciales para acceder.</p>
            </div>
            <form className="login__form" onSubmit={submit}>
              <div><label className="login__label">Email / Usuario</label><input className="login__input" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Ingrese su credencial Asignada" /></div>
              <div><label className="login__label">Contraseña</label><input type="password" className="login__input" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Ingrese su contraseña" /></div>
              {error && <p style={{color:'#ef4444', fontSize:'0.8rem'}}>{error}</p>}
              <button type="submit" className="login__submit" disabled={loading}>{loading ? 'Ingresando...' : 'Ingresar'}</button>
            </form>
            <p className="login__credit">Developed By GaRi Software Team</p>
          </div>
        </section>
      </main>
    </div>
    </>
  );
}