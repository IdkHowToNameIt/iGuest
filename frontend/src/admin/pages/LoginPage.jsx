import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import Icon from '../../components/Icon.jsx'
import { useT, LangToggle } from '../../i18n/index.jsx'
import '../admin.css'

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const { t } = useT()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/admin'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  // Already signed in → skip the form.
  if (isAuthenticated) return <Navigate to={from} replace />

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const data = await login(username, password)
      // Force the password rotation step before anything else when required.
      navigate(data.must_change_password ? '/admin/change-password' : from, { replace: true })
    } catch (err) {
      setError(err.status === 401 ? t('Invalid username or password.') : err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-hero">
        <div className="auth-hero-brand">
          <span className="brand-mark">
            <Icon name="home" size={20} />
          </span>
          <div>
            <div className="sidebar-brand-name">iGuest</div>
            <div className="sidebar-brand-sub">{t('Admin panel')}</div>
          </div>
        </div>
        <div>
          <div className="auth-hero-title">{t('Run every property from one place.')}</div>
          <p className="auth-hero-text">
            {t(
              'Manage structures, units and digital manuals, hand out guest links, and keep an eye on what your guests are asking — all from this panel.',
            )}
          </p>
        </div>
        <div className="auth-hero-foot">
          {t('Multilingual guest assistant for short-term rentals')}
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-lang"><LangToggle /></div>
        <form className="card auth-card form" onSubmit={handleSubmit}>
          <h2>{t('Admin sign in')}</h2>
          <p className="auth-card-sub">{t('Welcome back — enter your credentials to continue.')}</p>
          <div className="form-row">
            <label htmlFor="username">{t('Username')}</label>
            <input
              id="username"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              autoComplete="username"
            />
          </div>
          <div className="form-row">
            <label htmlFor="password">{t('Password')}</label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {error && <p className="error-text">{error}</p>}
          <button className="btn" type="submit" disabled={busy || !username || !password}>
            {busy ? t('Signing in…') : t('Sign in')}
          </button>
        </form>
      </div>
    </div>
  )
}
