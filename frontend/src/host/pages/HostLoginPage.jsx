import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useHostAuth } from '../hostAuth.jsx'
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
    <div className="login-screen">
      <form className="card login-card form" onSubmit={handleSubmit}>
        <h2>Host sign in</h2>
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
  )
}
