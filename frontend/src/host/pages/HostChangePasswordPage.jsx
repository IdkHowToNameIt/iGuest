import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { changePassword } from '../hostApi.js'
import { useHostAuth } from '../hostAuth.jsx'
import { useT } from '../../i18n/index.jsx'
import '../../admin/admin.css'

export default function HostChangePasswordPage() {
  const navigate = useNavigate()
  const { t } = useT()
  const { mustChangePassword, clearMustChange, logout } = useHostAuth()

  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    if (next.length < 8) {
      setError(t('The new password must be at least 8 characters.'))
      return
    }
    if (next !== confirm) {
      setError(t('The new passwords do not match.'))
      return
    }
    setBusy(true)
    try {
      await changePassword(current, next)
      clearMustChange()
      navigate('/host', { replace: true })
    } catch (err) {
      if (err.status === 401) {
        logout()
        navigate('/host/login', { replace: true })
        return
      }
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1>{t('Change password')}</h1>
      {mustChangePassword && (
        <p className="muted">
          {t('You signed in with a temporary password. Please choose a new one to continue.')}
        </p>
      )}
      <section className="card">
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label htmlFor="current">{t('Current password')}</label>
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
            <label htmlFor="next">{t('New password (min 8 characters)')}</label>
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
            <label htmlFor="confirm">{t('Confirm new password')}</label>
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
              {busy ? t('Saving…') : t('Update password')}
            </button>
          </div>
        </form>
      </section>
    </>
  )
}
