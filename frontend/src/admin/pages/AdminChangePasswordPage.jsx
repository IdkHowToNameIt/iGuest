import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { changePassword } from '../adminApi.js'
import { useAuth } from '../auth.jsx'

export default function AdminChangePasswordPage() {
  const navigate = useNavigate()
  const { mustChangePassword, clearMustChange, logout } = useAuth()

  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    if (next.length < 8) {
      setError('The new password must be at least 8 characters.')
      return
    }
    if (next !== confirm) {
      setError('The new passwords do not match.')
      return
    }
    setBusy(true)
    try {
      await changePassword(current, next)
      clearMustChange()
      navigate('/admin', { replace: true })
    } catch (err) {
      if (err.status === 401) {
        logout()
        navigate('/admin/login', { replace: true })
        return
      }
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1>Change password</h1>
      {mustChangePassword && (
        <p className="muted">
          You signed in with a temporary password. Please choose a new one to continue.
        </p>
      )}
      <section className="card">
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label htmlFor="current">Current password</label>
            <input
              id="current"
              type="password"
              className="input"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <div className="form-row">
            <label htmlFor="next">New password (min 8 characters)</label>
            <input
              id="next"
              type="password"
              className="input"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div className="form-row">
            <label htmlFor="confirm">Confirm new password</label>
            <input
              id="confirm"
              type="password"
              className="input"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          {error && <p className="error-text">{error}</p>}
          <div className="form-actions">
            <button className="btn" type="submit" disabled={busy || !current || !next || !confirm}>
              {busy ? 'Saving…' : 'Update password'}
            </button>
          </div>
        </form>
      </section>
    </>
  )
}
