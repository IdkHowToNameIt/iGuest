import { useEffect, useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import {
  getMe,
  listDocuments,
  getDocumentContent,
  listFaqs,
  getAnalytics,
  getUnitAnalytics,
  listChangeRequests,
  createChangeRequest,
  uploadAvatar,
  deleteAvatar,
} from '../hostApi.js'
import { useHostAuth } from '../hostAuth.jsx'
import DocumentText from '../../components/DocumentText.jsx'
import Avatar from '../../components/Avatar.jsx'
import Icon from '../../components/Icon.jsx'
import DashboardGrid, { resetLayout } from '../../components/DashboardGrid.jsx'

function statusBadge(status) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

// Dashboard blocks the host can freely drag/resize (see DashboardGrid). The
// arrangement is persisted per browser in localStorage.
const SECTION_LABELS = {
  documentation: 'Documentation',
  faq: 'Suggested answers (FAQ)',
  analytics: 'What guests ask',
  requests: 'Change requests',
}
const LAYOUT_KEY = 'guestreply_host_dashboard_layout_v1'
const DEFAULT_LAYOUT = [
  { i: 'documentation', x: 0, y: 0, w: 6, h: 7 },
  { i: 'analytics', x: 6, y: 0, w: 6, h: 8 },
  { i: 'faq', x: 0, y: 7, w: 6, h: 5 },
  { i: 'requests', x: 6, y: 8, w: 6, h: 9 },
]
// Notifications: whether they're on, and which resolved requests were already seen.
const NOTIF_KEY = 'guestreply_host_notifications'
const SEEN_KEY = 'guestreply_host_seen_resolved'

// Notifications default ON; explicit "false" disables them.
const loadNotifEnabled = () => localStorage.getItem(NOTIF_KEY) !== 'false'

function loadSeen() {
  try {
    const v = JSON.parse(localStorage.getItem(SEEN_KEY))
    return Array.isArray(v) ? v : null
  } catch {
    return null
  }
}
const saveSeen = (ids) => localStorage.setItem(SEEN_KEY, JSON.stringify(ids))

// The host's home: read-only documentation + FAQ/analytics for their unit, and
// a form to send the admin a document change request.
export default function HostDashboardPage() {
  const navigate = useNavigate()
  const { logout } = useHostAuth()
  const { refreshMe } = useOutletContext() ?? {}

  const [me, setMe] = useState(null)
  const [documents, setDocuments] = useState([])
  const [faqs, setFaqs] = useState([])
  const [analytics, setAnalytics] = useState(null) // structure-wide ("General")
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // per-room analytics: 'general' (structure-wide) or a unit id; per-unit
  // results are fetched lazily and cached so switching tabs back and forth
  // doesn't re-hit the API every time.
  const [analyticsScope, setAnalyticsScope] = useState('general')
  const [unitAnalytics, setUnitAnalytics] = useState({}) // unitId -> AnalyticsOut
  const [loadingUnitAnalytics, setLoadingUnitAnalytics] = useState(false)
  const [openCategory, setOpenCategory] = useState(null) // expanded category label

  // change-request form
  const [body, setBody] = useState('')
  const [docId, setDocId] = useState('') // '' | <document id> | '__other__'
  const [title, setTitle] = useState('') // problem title, only for "Other"
  const [submitting, setSubmitting] = useState(false)

  // dashboard layout settings
  const [showSettings, setShowSettings] = useState(false)
  const [customizing, setCustomizing] = useState(false)
  const [layoutVersion, setLayoutVersion] = useState(0)

  // profile avatar
  const [avatarBusy, setAvatarBusy] = useState(false)

  // notifications (when the admin resolves a request)
  const [notifEnabled, setNotifEnabled] = useState(loadNotifEnabled)
  const [notifications, setNotifications] = useState([]) // newly-resolved requests to show

  // collapsible request sections (hidden until the host clicks to open)
  const [openInProgress, setOpenInProgress] = useState(false)
  const [openResolved, setOpenResolved] = useState(false)

  function handleAuthError(err) {
    if (err.status === 401 || err.status === 403) {
      logout()
      navigate('/host/login', { replace: true })
      return true
    }
    return false
  }

  // Detect requests newly resolved since the host last loaded the dashboard and
  // surface a notification for them (in-app banner + optional browser notification).
  function detectResolved(reqs) {
    const resolvedIds = reqs.filter((r) => r.status === 'resolved').map((r) => r.id)
    const seen = loadSeen()
    if (seen === null) {
      // First ever load: establish a baseline, don't notify for old resolutions.
      saveSeen(resolvedIds)
      return
    }
    const newly = reqs.filter((r) => r.status === 'resolved' && !seen.includes(r.id))
    saveSeen(resolvedIds) // update baseline so each resolution notifies once
    if (newly.length === 0 || !loadNotifEnabled()) return
    setNotifications(newly)
    if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
      newly.forEach((r) =>
        new Notification('Request resolved', {
          body: r.document_id ? 'Your document change request was resolved.' : (r.title || 'Your request was resolved.'),
        }),
      )
    }
  }

  function toggleNotifications() {
    const next = !notifEnabled
    setNotifEnabled(next)
    localStorage.setItem(NOTIF_KEY, next ? 'true' : 'false')
    // Ask for browser-notification permission when turning them on.
    if (next && typeof Notification !== 'undefined' && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }

  async function refresh() {
    setLoading(true)
    try {
      const [m, d, f, a, r] = await Promise.all([
        getMe(),
        listDocuments(),
        listFaqs(),
        getAnalytics(),
        listChangeRequests(),
      ])
      setMe(m)
      setDocuments(d)
      setFaqs(f)
      setAnalytics(a)
      setRequests(r)
      setUnitAnalytics({}) // stale once new questions may have come in
      detectResolved(r)
      setError(null)
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSelectAnalyticsScope(scope) {
    setAnalyticsScope(scope)
    setOpenCategory(null)
    if (scope === 'general' || unitAnalytics[scope]) return
    setLoadingUnitAnalytics(true)
    try {
      const a = await getUnitAnalytics(scope)
      setUnitAnalytics((prev) => ({ ...prev, [scope]: a }))
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setLoadingUnitAnalytics(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const isOther = docId === '__other__'

  async function handleSubmitRequest(e) {
    e.preventDefault()
    if (!body.trim() || !docId || (isOther && !title.trim())) return
    setSubmitting(true)
    try {
      await createChangeRequest(
        body.trim(),
        isOther ? null : docId,
        isOther ? title.trim() : null,
      )
      setBody('')
      setDocId('')
      setTitle('')
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  function handleResetLayout() {
    resetLayout(LAYOUT_KEY)
    setLayoutVersion((v) => v + 1)
  }

  async function handleAvatarChange(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setAvatarBusy(true)
    try {
      const updated = await uploadAvatar(file)
      setMe(updated)
      await refreshMe?.()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setAvatarBusy(false)
    }
  }

  async function handleAvatarDelete() {
    setAvatarBusy(true)
    try {
      const updated = await deleteAvatar()
      setMe(updated)
      await refreshMe?.()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setAvatarBusy(false)
    }
  }

  if (loading) return <p className="muted">Loading…</p>
  if (!me) return <p className="error-text">{error || 'Could not load your account.'}</p>

  // Map unit id → name so unit-scoped documents can be labelled.
  const unitName = Object.fromEntries((me.units || []).map((u) => [u.id, u.name]))

  const openRequests = requests.filter((r) => r.status === 'open')
  const resolvedRequests = requests.filter((r) => r.status === 'resolved')

  function RequestList({ items, empty }) {
    if (items.length === 0) return <p className="muted">{empty}</p>
    return (
      <ul className="list">
        {items.map((r) => (
          <li className="row" key={r.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
            <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
              <div className="row-main">
                <span className="row-title">
                  <Icon name={r.document_id ? 'file-text' : 'help-circle'} size={15} />{' '}
                  {r.document_id ? 'Document request' : r.title || 'Other'}
                </span>
                <span className="row-sub">{new Date(r.created_at).toLocaleString()}</span>
              </div>
              {statusBadge(r.status === 'open' ? 'pending' : 'active')}
            </div>
            <p style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap' }}>{r.body}</p>
            {r.admin_note && <p className="muted">Note from {r.admin_name || 'Admin'}: {r.admin_note}</p>}
          </li>
        ))}
      </ul>
    )
  }

  const sections = {
    documentation: (
      <section className="card" key="documentation">
        <h2>Documentation</h2>
        <p className="muted">
          The manuals the assistant uses to answer your guests (read-only). To change
          them, send a request below.
        </p>
        {documents.length === 0 ? (
          <p className="muted">No documents yet.</p>
        ) : (
          <ul className="list">
            {documents.map((d) => (
              <li className="row" key={d.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                  <div className="row-main">
                    <span className="row-title">{d.original_filename}</span>
                    <span className="row-sub">
                      {d.scope_type === 'structure'
                        ? 'shared'
                        : unitName[d.unit_id] || 'unit'}{' '}
                      · {d.file_type} {statusBadge(d.status)}
                    </span>
                  </div>
                  <div className="row-actions">
                    <DocumentText
                      docId={d.id}
                      fetchContent={getDocumentContent}
                      variant="modal"
                      title={d.original_filename}
                    />
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    ),

    faq: (
      <section className="card" key="faq">
        <h2>Suggested answers (FAQ)</h2>
        {faqs.length === 0 ? (
          <p className="muted">No FAQ entries yet — they build up from guest questions.</p>
        ) : (
          <ul className="list">
            {faqs.map((f) => (
              <li className="row" key={f.rank} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <span className="row-title">{f.question}</span>
                <span className="row-sub" style={{ whiteSpace: 'pre-wrap' }}>{f.answer}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    ),

    analytics: (() => {
      const scoped = analyticsScope === 'general' ? analytics : unitAnalytics[analyticsScope]
      const scopeLabel =
        analyticsScope === 'general' ? 'all rooms' : unitName[analyticsScope] || 'this room'
      return (
        <section className="card" key="analytics">
          <h2>What guests ask</h2>
          <div className="pill-tabs">
            <button
              type="button"
              className={`pill-tab${analyticsScope === 'general' ? ' active' : ''}`}
              onClick={() => handleSelectAnalyticsScope('general')}
            >
              General
            </button>
            {(me.units || []).map((u) => (
              <button
                type="button"
                key={u.id}
                className={`pill-tab${analyticsScope === u.id ? ' active' : ''}`}
                onClick={() => handleSelectAnalyticsScope(u.id)}
              >
                {u.name}
              </button>
            ))}
          </div>

          {loadingUnitAnalytics && analyticsScope !== 'general' && !scoped ? (
            <p className="muted">Loading…</p>
          ) : !scoped || scoped.total === 0 ? (
            <p className="muted">No guest questions for {scopeLabel} yet.</p>
          ) : (
            <>
              <p className="muted">{scoped.total} guest question(s) for {scopeLabel}.</p>
              <ul className="list">
                {scoped.categories.map((cat) => (
                  <li className="row" key={cat.label} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                    <button
                      type="button"
                      className="row"
                      style={{ border: 'none', padding: 0, background: 'transparent', width: '100%', textAlign: 'left' }}
                      onClick={() => setOpenCategory((c) => (c === cat.label ? null : cat.label))}
                    >
                      <div className="row-main">
                        <span className="row-title">{cat.label}</span>
                        <span className="row-sub">
                          {cat.count} question(s) · {Math.round(cat.share * 100)}%
                        </span>
                      </div>
                      <span className="muted">
                        <Icon name={openCategory === cat.label ? 'chevron-down' : 'chevron-right'} size={16} />
                      </span>
                    </button>
                    {openCategory === cat.label && (
                      <ul className="list" style={{ marginTop: 8 }}>
                        {cat.questions.map((q) => (
                          <li className="row" key={q.question}>
                            <span className="row-sub">{q.question}</span>
                            <span className="badge">{q.count} · {Math.round(q.share * 100)}%</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )
    })(),

    requests: (
      <section className="card" key="requests">
        <h2>Change requests</h2>
        <form className="form" onSubmit={handleSubmitRequest}>
          <div className="form-row">
            <label htmlFor="docId">Related document</label>
            <select id="docId" className="select" value={docId} onChange={(e) => setDocId(e.target.value)}>
              <option value="" disabled>
                — select —
              </option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename}
                </option>
              ))}
              <option value="__other__">Other (a different problem)</option>
            </select>
          </div>
          {isOther && (
            <div className="form-row">
              <label htmlFor="reqTitle">Problem title</label>
              <input
                id="reqTitle"
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Broken heating in the living room"
                maxLength={200}
              />
            </div>
          )}
          <div className="form-row">
            <label htmlFor="body">What should change?</label>
            <textarea
              id="body"
              className="input"
              rows={4}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="e.g. The wifi password changed to …"
            />
          </div>
          <div className="form-actions">
            <button
              className="btn"
              type="submit"
              disabled={submitting || !body.trim() || !docId || (isOther && !title.trim())}
            >
              {submitting ? 'Sending…' : 'Send request'}
            </button>
          </div>
        </form>

        <div className="form-actions" style={{ gap: 8, marginTop: 8 }}>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setOpenInProgress((v) => !v)}
          >
            <Icon name={openInProgress ? 'chevron-down' : 'chevron-right'} size={14} /> In progress ({openRequests.length})
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setOpenResolved((v) => !v)}
          >
            <Icon name={openResolved ? 'chevron-down' : 'chevron-right'} size={14} /> Resolved ({resolvedRequests.length})
          </button>
        </div>
        {openInProgress && (
          <div style={{ marginTop: 8 }}>
            <RequestList items={openRequests} empty="No pending requests." />
          </div>
        )}
        {openResolved && (
          <div style={{ marginTop: 8 }}>
            <RequestList items={resolvedRequests} empty="No resolved requests yet." />
          </div>
        )}
      </section>
    ),
  }

  const blocks = Object.entries(sections).map(([key, content]) => ({
    key,
    title: SECTION_LABELS[key],
    content,
  }))

  return (
    <>
      <div className="page-head">
        <h1>{me.structure_name}</h1>
        <div className="form-actions">
          <button
            className={`btn btn-sm${customizing ? '' : ' btn-ghost'}`}
            onClick={() => setCustomizing((v) => !v)}
          >
            <Icon name={customizing ? 'check' : 'grip'} size={14} />{' '}
            {customizing ? 'Done arranging' : 'Customize layout'}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowSettings((v) => !v)}>
            <Icon name="settings" size={14} /> Settings
          </button>
        </div>
      </div>
      <p className="muted">
        {(me.units || []).length} unit(s) · signed in as {me.email}{' '}
        · <Link to="/host/change-password">change password</Link>
      </p>
      {error && <p className="error-text">{error}</p>}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">Documents</span>
            <span className="chip">
              <Icon name="file-text" size={19} />
            </span>
          </div>
          <span className="stat-card-value">{documents.length}</span>
        </div>
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">FAQ entries</span>
            <span className="chip tone-2">
              <Icon name="help-circle" size={19} />
            </span>
          </div>
          <span className="stat-card-value">{faqs.length}</span>
        </div>
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">Guest questions</span>
            <span className="chip tone-3">
              <Icon name="message-circle" size={19} />
            </span>
          </div>
          <span className="stat-card-value">{analytics?.total || 0}</span>
        </div>
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">Open requests</span>
            <span className="chip tone-4">
              <Icon name="clipboard" size={19} />
            </span>
          </div>
          <span className="stat-card-value">{openRequests.length}</span>
        </div>
      </div>

      {notifications.length > 0 && (
        <div className="notif-banner">
          <span className="notif-banner-text">
            <Icon name="bell" size={16} /> {notifications.length} request(s) resolved:{' '}
            {notifications.map((r) => (r.document_id ? 'document request' : r.title || 'other')).join(', ')}
          </span>
          <button className="btn btn-ghost btn-sm" onClick={() => setNotifications([])}>
            Dismiss
          </button>
        </div>
      )}

      {showSettings && (
        <section className="card">
          <h2>Settings</h2>

          <h3 className="form-section">Profile picture</h3>
          <div className="avatar-upload">
            <Avatar name={me.email} avatarUrl={me.avatar_url} size={64} zoomable />
            <div className="avatar-upload-actions">
              <label className="btn btn-ghost btn-sm">
                {avatarBusy ? 'Uploading…' : 'Upload photo'}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={handleAvatarChange}
                  disabled={avatarBusy}
                  style={{ display: 'none' }}
                />
              </label>
              {me.avatar_url && (
                <button className="btn btn-ghost btn-sm" onClick={handleAvatarDelete} disabled={avatarBusy}>
                  Remove photo
                </button>
              )}
            </div>
          </div>

          <h3 className="form-section">Notifications</h3>
          <label className="notif-toggle">
            <input type="checkbox" checked={notifEnabled} onChange={toggleNotifications} />{' '}
            Notify me when the admin resolves one of my requests
          </label>

          <h3 className="form-section">Dashboard layout</h3>
          <p className="muted">
            Click "Customize layout" above to drag and resize the blocks below to your liking.
            Saved in this browser.
          </p>
          <div className="form-actions">
            <button className="btn btn-ghost btn-sm" onClick={handleResetLayout}>
              Reset layout to default
            </button>
          </div>
        </section>
      )}

      <DashboardGrid
        key={layoutVersion}
        storageKey={LAYOUT_KEY}
        blocks={blocks}
        defaultLayout={DEFAULT_LAYOUT}
        editing={customizing}
      />
    </>
  )
}
