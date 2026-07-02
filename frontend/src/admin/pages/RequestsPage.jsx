import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  listChangeRequests,
  updateChangeRequest,
  listVisitRequests,
  updateVisitRequest,
  deleteVisitRequest,
} from '../adminApi.js'
import { useAuth } from '../auth.jsx'
import Icon from '../../components/Icon.jsx'
import { useT } from '../../i18n/index.jsx'

const BUSINESS_LABEL = {
  bnb_hotel: 'B&B / Hotel',
  private_host: 'Private host',
  property_manager: 'Property manager / Agency',
}

// Admin inbox, split into two tabs:
//   • Document requests — host-submitted requests to change their manuals.
//   • Visit requests    — "book a visit" leads from the public landing page.
export default function RequestsPage() {
  const { t } = useT()
  const [tab, setTab] = useState('document') // 'document' | 'visit'

  return (
    <>
      <h1>{t('Requests')}</h1>
      <div className="pill-tabs" style={{ marginBottom: 18 }}>
        <button
          type="button"
          className={`pill-tab${tab === 'document' ? ' active' : ''}`}
          onClick={() => setTab('document')}
        >
          {t('Document requests')}
        </button>
        <button
          type="button"
          className={`pill-tab${tab === 'visit' ? ' active' : ''}`}
          onClick={() => setTab('visit')}
        >
          {t('Visit requests')}
        </button>
      </div>

      {tab === 'document' ? <DocumentRequests /> : <VisitRequests />}
    </>
  )
}

// ── Document change requests (host-submitted) ─────────────────────────────────
function DocumentRequests() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { t } = useT()

  const [requests, setRequests] = useState([])
  const [statusFilter, setStatusFilter] = useState('open')
  const [typeFilter, setTypeFilter] = useState('all') // all | document | other
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notes, setNotes] = useState({})

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

  const query = search.trim().toLowerCase()
  const visibleRequests = query
    ? requests.filter((r) =>
        [r.structure_name, r.host_email, r.title, r.body].some((field) =>
          field?.toLowerCase().includes(query),
        ),
      )
    : requests

  return (
    <section className="card">
      <div className="form-grid">
        <div className="form-row">
          <label htmlFor="statusFilter">{t('Status')}</label>
          <select
            id="statusFilter"
            className="select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="open">{t('Open##status')}</option>
            <option value="resolved">{t('Resolved')}</option>
            <option value="all">{t('All')}</option>
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="typeFilter">{t('Type')}</label>
          <select
            id="typeFilter"
            className="select"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">{t('All types')}</option>
            <option value="document">{t('Document-based')}</option>
            <option value="other">{t('Other')}</option>
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="requestSearch">{t('Search')}</label>
          <input
            id="requestSearch"
            type="search"
            className="input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('Structure, host email, title or message…')}
          />
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p className="muted">{t('Loading…')}</p>
      ) : visibleRequests.length === 0 ? (
        <p className="muted">
          {requests.length === 0 ? t('No change requests.') : t('No change requests match your search.')}
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
                    <span className={`badge badge-${r.status === 'open' ? 'pending' : 'active'}`}>{t(r.status)}</span>
                    {' · '}
                    <span className="badge">{r.document_id ? t('document') : t('other')}</span>
                    {' · '}
                    {r.host_email || t('host removed')} · {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {!r.document_id && r.title && (
                <p style={{ margin: '8px 0 0', fontWeight: 600 }}>{r.title}</p>
              )}
              <p style={{ margin: '8px 0', whiteSpace: 'pre-wrap' }}>{r.body}</p>

              <div className="form-row">
                <label htmlFor={`note-${r.id}`}>{t('Admin note')}</label>
                <input
                  id={`note-${r.id}`}
                  className="input"
                  defaultValue={r.admin_note || ''}
                  onChange={(e) => setNotes((n) => ({ ...n, [r.id]: e.target.value }))}
                  placeholder={t('Optional note for your own reference')}
                />
              </div>
              <div className="row-actions" style={{ marginTop: 8 }}>
                {r.status === 'open' ? (
                  <button className="btn btn-sm" onClick={() => handleSetStatus(r, 'resolved')}>
                    {t('Mark resolved')}
                  </button>
                ) : (
                  <button className="btn btn-ghost btn-sm" onClick={() => handleSetStatus(r, 'open')}>
                    {t('Reopen')}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

// ── Visit requests (public landing leads) ─────────────────────────────────────
function VisitRequests() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { t } = useT()

  const [requests, setRequests] = useState([])
  const [statusFilter, setStatusFilter] = useState('new')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notes, setNotes] = useState({})

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
      const items = await listVisitRequests(params)
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
  }, [statusFilter])

  async function handleSetStatus(req, status) {
    try {
      await updateVisitRequest(req.id, { status, admin_note: notes[req.id] ?? req.admin_note ?? null })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleDelete(req) {
    if (!window.confirm(t('Delete this visit request permanently?'))) return
    try {
      await deleteVisitRequest(req.id)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  const query = search.trim().toLowerCase()
  const visible = query
    ? requests.filter((r) =>
        [r.structure_name, r.city, r.contact_name, r.contact_email].some((f) =>
          f?.toLowerCase().includes(query),
        ),
      )
    : requests

  const statusBadge = (status) =>
    status === 'new' ? 'pending' : status === 'contacted' ? 'active' : 'muted'

  return (
    <section className="card">
      <p className="muted" style={{ marginTop: 0 }}>
        {t('Leads submitted from the “Book a visit” form on the public landing page.')}
      </p>
      <div className="form-grid">
        <div className="form-row">
          <label htmlFor="vStatusFilter">{t('Status')}</label>
          <select
            id="vStatusFilter"
            className="select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="new">{t('New')}</option>
            <option value="contacted">{t('Contacted')}</option>
            <option value="archived">{t('Archived')}</option>
            <option value="all">{t('All')}</option>
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="vSearch">{t('Search')}</label>
          <input
            id="vSearch"
            type="search"
            className="input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('Structure, city, contact or email…')}
          />
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p className="muted">{t('Loading…')}</p>
      ) : visible.length === 0 ? (
        <p className="muted">
          {requests.length === 0 ? t('No visit requests.') : t('No visit requests match your search.')}
        </p>
      ) : (
        <ul className="list">
          {visible.map((r) => (
            <li className="row" key={r.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                <div className="row-main">
                  <span className="row-title">{r.structure_name}</span>
                  <span className="row-sub">
                    <span className={`badge badge-${statusBadge(r.status)}`}>{t(r.status)}</span>
                    {r.city ? ` · ${r.city}` : ''}
                    {r.business_type ? ` · ${t(BUSINESS_LABEL[r.business_type] || r.business_type)}` : ''}
                    {' · '}
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <p style={{ margin: '8px 0 0' }}>
                <Icon name="user" size={14} /> {r.contact_name} ·{' '}
                <a href={`mailto:${r.contact_email}`}>{r.contact_email}</a>
                {r.preferred_date ? ` · ${t('preferred: {date}', { date: r.preferred_date })}` : ''}
              </p>

              <div className="form-row" style={{ marginTop: 8 }}>
                <label htmlFor={`vnote-${r.id}`}>{t('Admin note')}</label>
                <input
                  id={`vnote-${r.id}`}
                  className="input"
                  defaultValue={r.admin_note || ''}
                  onChange={(e) => setNotes((n) => ({ ...n, [r.id]: e.target.value }))}
                  placeholder={t('Optional note (e.g. call outcome)')}
                />
              </div>
              <div className="row-actions" style={{ marginTop: 8, gap: 8, display: 'flex', flexWrap: 'wrap' }}>
                {r.status !== 'contacted' && (
                  <button className="btn btn-sm" onClick={() => handleSetStatus(r, 'contacted')}>
                    {t('Mark contacted')}
                  </button>
                )}
                {r.status !== 'archived' && (
                  <button className="btn btn-ghost btn-sm" onClick={() => handleSetStatus(r, 'archived')}>
                    {t('Archive')}
                  </button>
                )}
                {r.status !== 'new' && (
                  <button className="btn btn-ghost btn-sm" onClick={() => handleSetStatus(r, 'new')}>
                    {t('Reopen')}
                  </button>
                )}
                <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(r)}>
                  <Icon name="x" size={14} /> {t('Delete')}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
