import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listAdmins, createAdmin, updateAdmin, deleteAdmin } from '../adminApi.js'
import { useAuth } from '../auth.jsx'

// Manage additional admin logins, on top of the built-in .env admin account
// (which never shows up here — it has no DB row, see app/services/auth.py).
export default function AdminAccountsPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const [admins, setAdmins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [username, setUsername] = useState('')
  const [creating, setCreating] = useState(false)
  const [tempPassword, setTempPassword] = useState(null) // { adminId, password }

  function handleAuthError(err) {
    if (err.status === 401) {
      logout()
      navigate('/admin/login', { replace: true })
      return true
    }
    return false
  }

  async function refresh() {
    setLoading(true)
    try {
      setAdmins(await listAdmins())
      setError(null)
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    if (!username.trim()) return
    setCreating(true)
    try {
      const admin = await createAdmin(username.trim())
      setUsername('')
      setTempPassword({ adminId: admin.id, password: admin.temp_password })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setCreating(false)
    }
  }

  async function handleToggle(admin) {
    try {
      await updateAdmin(admin.id, { is_active: !admin.is_active })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleResetPassword(adminId) {
    if (!window.confirm('Issue a new temporary password for this admin account?')) return
    try {
      const admin = await updateAdmin(adminId, { reset_password: true })
      setTempPassword({ adminId: admin.id, password: admin.temp_password })
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleDelete(adminId) {
    if (!window.confirm('Delete this admin account?')) return
    try {
      await deleteAdmin(adminId)
      if (tempPassword?.adminId === adminId) setTempPassword(null)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  return (
    <>
      <h1>Admin accounts</h1>

      <section className="card">
        <p className="muted">
          The built-in admin login (set in the backend&apos;s .env file) always keeps working as a
          fallback. Add further named accounts here for other administrators — the temporary
          password is shown once, so share it securely.
        </p>
        <form className="form" onSubmit={handleCreate}>
          <div className="form-row">
            <label htmlFor="adminUsername">Username</label>
            <input
              id="adminUsername"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. mario"
            />
          </div>
          <div className="form-actions">
            <button className="btn" type="submit" disabled={creating || !username.trim()}>
              {creating ? 'Creating…' : 'Add admin'}
            </button>
          </div>
        </form>

        {error && <p className="error-text">{error}</p>}
        {loading ? (
          <p className="muted">Loading…</p>
        ) : admins.length === 0 ? (
          <p className="muted">No additional admin accounts yet.</p>
        ) : (
          <ul className="list">
            {admins.map((a) => (
              <li className="row" key={a.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                  <div className="row-main">
                    <span className="row-title">{a.username}</span>
                    <span className="row-sub">
                      <span className={`badge badge-${a.is_active ? 'active' : 'revoked'}`}>
                        {a.is_active ? 'active' : 'disabled'}
                      </span>
                      {a.must_change_password ? ' · awaiting password change' : ''}
                    </span>
                  </div>
                  <div className="row-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => handleToggle(a)}>
                      {a.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleResetPassword(a.id)}>
                      Reset password
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(a.id)}>
                      Delete
                    </button>
                  </div>
                </div>
                {tempPassword?.adminId === a.id && (
                  <p className="temp-password">
                    Temporary password (shown once): <code>{tempPassword.password}</code>
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
