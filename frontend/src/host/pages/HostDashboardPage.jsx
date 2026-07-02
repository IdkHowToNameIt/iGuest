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
import { DocumentRow } from '../../components/DocumentText.jsx'
import Avatar from '../../components/Avatar.jsx'
import Icon from '../../components/Icon.jsx'
import DashboardGrid, { resetLayout } from '../../components/DashboardGrid.jsx'
import { useT } from '../../i18n/index.jsx'

// Localized status badge (open→pending, resolved→active …); label is translated.
function StatusBadge({ status }) {
  const { t } = useT()
  return <span className={`badge badge-${status}`}>{t(status)}</span>
}

// Dashboard blocks the host can freely drag/resize (see DashboardGrid). The
// arrangement is persisted per browser in localStorage.
const SECTION_LABELS = {
  documentation: 'Documentation',
  faq: 'Suggested answers (FAQ)',
  analytics: 'What guests ask',
  requests: 'Change requests',
}
const LAYOUT_KEY = 'iguest_host_dashboard_layout_v1'
const DEFAULT_LAYOUT = [
  { i: 'documentation', x: 0, y: 0, w: 6, h: 7 },
  { i: 'analytics', x: 6, y: 0, w: 6, h: 8 },
  { i: 'faq', x: 0, y: 7, w: 6, h: 5 },
  { i: 'requests', x: 6, y: 8, w: 6, h: 9 },
]
// Notifications: whether they're on, and which resolved requests were already seen.
const NOTIF_KEY = 'iguest_host_notifications'
const SEEN_KEY = 'iguest_host_seen_resolved'

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
  const { t } = useT()
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

  if (loading) return <p className="muted">{t('Loading…')}</p>
  if (!me) return <p className="error-text">{error || t('Could not load your account.')}</p>

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
                  {r.document_id ? t('Document request') : r.title || t('Other')}
                </span>
                <span className="row-sub">{new Date(r.created_at).toLocaleString()}</span>
              </div>
              <StatusBadge status={r.status === 'open' ? 'pending' : 'active'} />
            </div>
            <p style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap' }}>{r.body}</p>
            {r.admin_note && (
              <p className="muted">
                {t('Note from {name}: {note}', { name: r.admin_name || t('Admin'), note: r.admin_note })}
              </p>
            )}
          </li>
        ))}
      </ul>
    )
  }

  const sections = {
    documentation: (
      <section className="card" key="documentation">
        <h2>{t('Documentation')}</h2>
        <p className="muted">
          {t(
            'The manuals the assistant uses to answer your guests (read-only). To change them, send a request below.',
          )}
        </p>
        {documents.length === 0 ? (
          <p className="muted">{t('No documents yet.')}</p>
        ) : (
          <ul className="list">
            {documents.map((d) => (
              <DocumentRow
                key={d.id}
                docId={d.id}
                fetchContent={getDocumentContent}
                title={d.original_filename}
                subtitle={
                  <>
                    {d.scope_type === 'structure' ? t('shared') : unitName[d.unit_id] || t('unit')}{' '}
                    · {d.file_type} <StatusBadge status={d.status} />
                  </>
                }
              />
            ))}
          </ul>
        )}
      </section>
    ),

    faq: (
      <section className="card" key="faq">
        <h2>{t('Suggested answers (FAQ)')}</h2>
        {faqs.length === 0 ? (
          <p className="muted">{t('No FAQ entries yet — they build up from guest questions.')}</p>
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
        analyticsScope === 'general' ? t('all rooms') : unitName[analyticsScope] || t('this room')
      return (
        <section className="card" key="analytics">
          <h2>{t('What guests ask')}</h2>
          <div className="pill-tabs">
            <button
              type="button"
              className={`pill-tab${analyticsScope === 'general' ? ' active' : ''}`}
              onClick={() => handleSelectAnalyticsScope('general')}
            >
              {t('General')}
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
            <p className="muted">{t('Loading…')}</p>
          ) : !scoped || scoped.total === 0 ? (
            <p className="muted">{t('No guest questions for {scope} yet.', { scope: scopeLabel })}</p>
          ) : (
            <>
              <p className="muted">
                {t('{n} guest question(s) for {scope}.', { n: scoped.total, scope: scopeLabel })}
              </p>
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
                          {t('{n} question(s)', { n: cat.count })} · {Math.round(cat.share * 100)}%
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
        <h2>{t('Change requests')}</h2>
        <form className="form" onSubmit={handleSubmitRequest}>
          <div className="form-row">
            <label htmlFor="docId">{t('Related document')}</label>
            <select id="docId" className="select" value={docId} onChange={(e) => setDocId(e.target.value)}>
              <option value="" disabled>
                {t('— select —')}
              </option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename}
                </option>
              ))}
              <option value="__other__">{t('Other (a different problem)')}</option>
            </select>
          </div>
          {isOther && (
            <div className="form-row">
              <label htmlFor="reqTitle">{t('Problem title')}</label>
              <input
                id="reqTitle"
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={t('e.g. Broken heating in the living room')}
                maxLength={200}
              />
            </div>
          )}
          <div className="form-row">
            <label htmlFor="body">{t('What should change?')}</label>
            <textarea
              id="body"
              className="input"
              rows={4}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={t('e.g. The wifi password changed to …')}
            />
          </div>
          <div className="form-actions">
            <button
              className="btn"
              type="submit"
              disabled={submitting || !body.trim() || !docId || (isOther && !title.trim())}
            >
              {submitting ? t('Sending…') : t('Send request')}
            </button>
          </div>
        </form>

        <div className="form-actions" style={{ gap: 8, marginTop: 8 }}>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setOpenInProgress((v) => !v)}
          >
            <Icon name={openInProgress ? 'chevron-down' : 'chevron-right'} size={14} />{' '}
            {t('In progress ({n})', { n: openRequests.length })}
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setOpenResolved((v) => !v)}
          >
            <Icon name={openResolved ? 'chevron-down' : 'chevron-right'} size={14} />{' '}
            {t('Resolved ({n})', { n: resolvedRequests.length })}
          </button>
        </div>
        {openInProgress && (
          <div style={{ marginTop: 8 }}>
            <RequestList items={openRequests} empty={t('No pending requests.')} />
          </div>
        )}
        {openResolved && (
          <div style={{ marginTop: 8 }}>
            <RequestList items={resolvedRequests} empty={t('No resolved requests yet.')} />
          </div>
        )}
      </section>
    ),
  }

  const blocks = Object.entries(sections).map(([key, content]) => ({
    key,
    title: t(SECTION_LABELS[key]),
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
            {customizing ? t('Done arranging') : t('Customize layout')}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowSettings((v) => !v)}>
            <Icon name="settings" size={14} /> {t('Settings')}
          </button>
        </div>
      </div>
      <p className="muted">
        {t('{n} unit(s)', { n: (me.units || []).length })} ·{' '}
        {t('signed in as {email}', { email: me.email })}{' '}
        · <Link to="/host/change-password">{t('change password')}</Link>
      </p>
      {error && <p className="error-text">{error}</p>}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">{t('Documents')}</span>
            <span className="chip">
              <Icon name="file-text" size={19} />
            </span>
          </div>
          <span className="stat-card-value">{documents.length}</span>
        </div>
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">{t('FAQ entries')}</span>
            <span className="chip tone-2">
              <Icon name="help-circle" size={19} />
            </span>
          </div>
          <span className="stat-card-value">{faqs.length}</span>
        </div>
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">{t('Guest questions')}</span>
            <span className="chip tone-3">
              <Icon name="message-circle" size={19} />
            </span>
          </div>
          <span className="stat-card-value">{analytics?.total || 0}</span>
        </div>
        <div className="stat-card">
          <div className="stat-card-top">
            <span className="stat-card-label">{t('Open requests')}</span>
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
            <Icon name="bell" size={16} />{' '}
            {t('{n} request(s) resolved: {list}', {
              n: notifications.length,
              list: notifications
                .map((r) => (r.document_id ? t('document request') : r.title || t('other')))
                .join(', '),
            })}
          </span>
          <button className="btn btn-ghost btn-sm" onClick={() => setNotifications([])}>
            {t('Dismiss')}
          </button>
        </div>
      )}

      {showSettings && (
        <section className="card">
          <h2>{t('Settings')}</h2>

          <h3 className="form-section">{t('Profile picture')}</h3>
          <div className="avatar-upload">
            <Avatar name={me.email} avatarUrl={me.avatar_url} size={64} zoomable />
            <div className="avatar-upload-actions">
              <label className="btn btn-ghost btn-sm">
                {avatarBusy ? t('Uploading…') : t('Upload photo')}
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
                  {t('Remove photo')}
                </button>
              )}
            </div>
          </div>

          <h3 className="form-section">{t('Notifications')}</h3>
          <label className="notif-toggle">
            <input type="checkbox" checked={notifEnabled} onChange={toggleNotifications} />{' '}
            {t('Notify me when the admin resolves one of my requests')}
          </label>

          <h3 className="form-section">{t('Dashboard layout')}</h3>
          <p className="muted">
            {t(
              'Click "Customize layout" above to drag and resize the blocks below to your liking. Saved in this browser.',
            )}
          </p>
          <div className="form-actions">
            <button className="btn btn-ghost btn-sm" onClick={handleResetLayout}>
              {t('Reset layout to default')}
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
