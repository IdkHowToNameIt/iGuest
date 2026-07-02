import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listChangeRequests, updateChangeRequest } from '../adminApi.js'
import { useAuth } from '../auth.jsx'

// Admin inbox for host-submitted document change requests. Filter by status,
// add a note, and mark resolved / reopen.
export default function ChangeRequestsPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const [requests, setRequests] = useState([])
  const [statusFilter, setStatusFilter] = useState('open')
  const [typeFilter, setTypeFilter] = useState('all') // all | document | other
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notes, setNotes] = useState({}) // { [requestId]: draftNote }

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
      const params = {}
      if (statusFilter !== 'all') params.status = statusFilter
      if (typeFilter !== 'all') params.type = typeFilter
      const items = await listChangeRequests(params)
      setRequests(items)
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
  }, [statusFilter, typeFilter])

  async function handleSetStatus(req, status) {
    try {
      await updateChangeRequest(req.id, { status, admin_note: notes[req.id] ?? req.admin_note ?? null })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  // Free-text search over structure, host email and the request's own text —
  // applied client-side on top of the server-filtered status/type results.
  const query = search.trim().toLowerCase()
  const visibleRequests = query
    ? requests.filter((r) =>
        [r.structure_name, r.host_email, r.title, r.body].some((field) =>
          field?.toLowerCase().includes(query),
        ),
      )
    : requests

  return (
    <>
      <h1>Change requests</h1>

      <section className="card">
        <div className="form-grid">
          <div className="form-row">
            <label htmlFor="statusFilter">Status</label>
            <select
              id="statusFilter"
              className="select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="open">Open</option>
              <option value="resolved">Resolved</option>
              <option value="all">All</option>
            </select>
          </div>
          <div className="form-row">
            <label htmlFor="typeFilter">Type</label>
            <select
              id="typeFilter"
              className="select"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="all">All types</option>
              <option value="document">Document-based</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="form-row">
            <label htmlFor="requestSearch">Search</label>
            <input
              id="requestSearch"
              type="search"
              className="input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Structure, host email, title or message…"
            />
          </div>
        </div>

        {error && <p className="error-text">{error}</p>}
        {loading ? (
          <p className="muted">Loading…</p>
        ) : visibleRequests.length === 0 ? (
          <p className="muted">
            {requests.length === 0 ? 'No change requests.' : 'No change requests match your search.'}
          </p>
        ) : (
          <ul className="list">
            {visibleRequests.map((r) => (
              <li className="row" key={r.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                  <div className="row-main">
                    <span className="row-title">
                      <Link to={`/admin/structures/${r.structure_id}`}>{r.structure_name || 'structure'}</Link>
                    </span>
                    <span className="row-sub">
                      <span className={`badge badge-${r.status === 'open' ? 'pending' : 'active'}`}>{r.status}</span>
                      {' · '}
                      <span className="badge">{r.document_id ? 'document' : 'other'}</span>
                      {' · '}
                      {r.host_email || 'host removed'} · {new Date(r.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                {!r.document_id && r.title && (
                  <p style={{ margin: '8px 0 0', fontWeight: 600 }}>{r.title}</p>
                )}
                <p style={{ margin: '8px 0', whiteSpace: 'pre-wrap' }}>{r.body}</p>

                <div className="form-row">
                  <label htmlFor={`note-${r.id}`}>Admin note</label>
                  <input
                    id={`note-${r.id}`}
                    className="input"
                    defaultValue={r.admin_note || ''}
                    onChange={(e) => setNotes((n) => ({ ...n, [r.id]: e.target.value }))}
                    placeholder="Optional note for your own reference"
                  />
                </div>
                <div className="row-actions" style={{ marginTop: 8 }}>
                  {r.status === 'open' ? (
                    <button className="btn btn-sm" onClick={() => handleSetStatus(r, 'resolved')}>
                      Mark resolved
                    </button>
                  ) : (
                    <button className="btn btn-ghost btn-sm" onClick={() => handleSetStatus(r, 'open')}>
                      Reopen
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
