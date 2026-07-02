import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useHostAuth } from '../hostAuth.jsx'
import Icon from '../../components/Icon.jsx'
import '../../admin/admin.css'

export default function HostLoginPage() {
  const { isAuthenticated, login } = useHostAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/host'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (isAuthenticated) return <Navigate to={from} replace />

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const data = await login(email, password)
      // Force the password rotation step before anything else when required.
      navigate(data.must_change_password ? '/host/change-password' : from, { replace: true })
    } catch (err) {
      setError(err.status === 401 ? 'Invalid email or password.' : err.message)
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
            <div className="sidebar-brand-name">GuestReply</div>
            <div className="sidebar-brand-sub">Host portal</div>
          </div>
        </div>
        <div>
          <div className="auth-hero-title">Everything your guests are told, at a glance.</div>
          <p className="auth-hero-text">
            Read your property's manuals, see what guests keep asking, and send the admin a
            change request whenever something needs updating.
          </p>
        </div>
        <div className="auth-hero-foot">Multilingual guest assistant for short-term rentals</div>
      </div>

      <div className="auth-form-side">
        <form className="card auth-card form" onSubmit={handleSubmit}>
          <h2>Host sign in</h2>
          <p className="auth-card-sub">Use the credentials your property manager gave you.</p>
          <div className="form-row">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
              autoComplete="username"
            />
          </div>
          <div className="form-row">
            <label htmlFor="password">Password</label>
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
          <button className="btn" type="submit" disabled={busy || !email || !password}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
