import { useEffect, useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import { getStats, listStructures, listChangeRequests, getAnalytics } from '../adminApi.js'
import { useAuth } from '../auth.jsx'
import Icon from '../../components/Icon.jsx'
import DashboardGrid, { resetLayout } from '../../components/DashboardGrid.jsx'
import { useT } from '../../i18n/index.jsx'

const LAYOUT_KEY = 'iguest_admin_dashboard_layout_v3'
const DEFAULT_LAYOUT = [
  { i: 'overview', x: 0, y: 0, w: 12, h: 3 },
  { i: 'recentStructures', x: 0, y: 3, w: 7, h: 8 },
  { i: 'openChangeRequests', x: 7, y: 3, w: 5, h: 8 },
  { i: 'questionCategories', x: 0, y: 11, w: 7, h: 8 },
  { i: 'quickActions', x: 7, y: 11, w: 5, h: 8 },
]

// Gradient fills for the "what guests ask" category bars (cycled).
const BAR_COLORS = [
  'linear-gradient(90deg,#9d66ff,#6b3bff)',
  'linear-gradient(90deg,#4fd3c2,#14a08f)',
  'linear-gradient(90deg,#6f9dff,#2f6fed)',
  'linear-gradient(90deg,#f0a04e,#e07c1f)',
]

function locationLine(s, t) {
  const parts = [s.city, s.province, s.region].filter(Boolean)
  return parts.length ? parts.join(' · ') : t('No location set')
}

// Compact relative timestamp for the activity feed ("5m ago", "2h ago", …).
function timeAgo(iso, t) {
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return t('just now')
  const minutes = seconds / 60
  if (minutes < 60) return t('{n}m ago', { n: Math.floor(minutes) })
  const hours = minutes / 60
  if (hours < 24) return t('{n}h ago', { n: Math.floor(hours) })
  const days = hours / 24
  if (days < 7) return t('{n}d ago', { n: Math.floor(days) })
  return new Date(iso).toLocaleDateString()
}

// The admin's home: dashboard overview built from free-form blocks (see
// DashboardGrid) — drag/resize is available via "Customize layout".
export default function AdminDashboardPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { t } = useT()
  const { profile } = useOutletContext() ?? {}

  const [stats, setStats] = useState(null)
  const [recentStructures, setRecentStructures] = useState([])
  const [openRequests, setOpenRequests] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [customizing, setCustomizing] = useState(false)
  const [layoutVersion, setLayoutVersion] = useState(0)

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
      const [s, structures, requests, a] = await Promise.all([
        getStats(),
        listStructures({}),
        listChangeRequests({ status: 'open' }),
        getAnalytics(),
      ])
      setStats(s)
      setRecentStructures(structures.slice(-6).reverse())
      setOpenRequests(requests.slice(0, 6))
      setAnalytics(a)
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

  function handleResetLayout() {
    resetLayout(LAYOUT_KEY)
    setLayoutVersion((v) => v + 1)
  }

  if (loading) return <p className="muted">{t('Loading…')}</p>
  if (error) return <p className="error-text">{error}</p>

  const statCards = [
    {
      label: 'Structures',
      value: stats.structures,
      icon: 'building',
      tone: '',
      to: '/admin/structures',
      linkLabel: 'Manage structures',
    },
    {
      label: 'Units',
      value: stats.units,
      icon: 'bed',
      tone: ' tone-2',
      to: '/admin/structures',
      linkLabel: 'Browse units',
    },
    {
      label: 'Active guest links',
      value: stats.active_links,
      icon: 'link',
      tone: ' tone-3',
      to: '/admin/structures',
      linkLabel: 'View structures',
    },
    {
      label: 'Open change requests',
      value: stats.open_change_requests,
      icon: 'clipboard',
      tone: ' tone-4',
      to: '/admin/change-requests',
      linkLabel: 'Review requests',
    },
  ]

  const blocks = [
    {
      key: 'overview',
      title: t('Overview'),
      bare: true,
      content: (
        <div className="stat-grid" style={{ height: '100%', alignContent: 'start' }}>
          {statCards.map((c) => (
            <div className="stat-card" key={c.label}>
              <div className="stat-card-top">
                <span className="stat-card-label">{t(c.label)}</span>
                <span className={`chip${c.tone}`}>
                  <Icon name={c.icon} size={19} />
                </span>
              </div>
              <span className="stat-card-value">{c.value}</span>
              <Link className="stat-card-link" to={c.to}>
                {t(c.linkLabel)} <Icon name="arrow-right" size={13} />
              </Link>
            </div>
          ))}
        </div>
      ),
    },
    {
      key: 'recentStructures',
      title: t('Recent structures'),
      content: (
        <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>{t('Recent structures')}</h2>
          {recentStructures.length === 0 ? (
            <div className="empty-state">
              <span className="chip chip-round">
                <Icon name="building" size={20} />
              </span>
              {t('No structures yet — create your first one to get started.')}
            </div>
          ) : (
            <ul className="activity-list">
              {recentStructures.map((s) => (
                <li className="activity-item" key={s.id}>
                  <span className="chip chip-round tone-3">
                    <Icon name="building" size={17} />
                  </span>
                  <div className="activity-main">
                    <span className="activity-title">
                      <Link to={`/admin/structures/${s.id}`}>{s.name}</Link>
                    </span>
                    <span className="activity-sub">
                      <Icon name="map-pin" size={12} /> {locationLine(s, t)}
                    </span>
                  </div>
                  <Link className="btn btn-ghost btn-sm" to={`/admin/structures/${s.id}`}>
                    {t('Open')}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      ),
    },
    {
      key: 'openChangeRequests',
      title: t('Recent activity'),
      content: (
        <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="page-head">
            <h2 style={{ fontSize: 17 }}>{t('Recent activity')}</h2>
            <Link className="btn btn-ghost btn-sm" to="/admin/change-requests">
              {t('View all')}
            </Link>
          </div>
          {openRequests.length === 0 ? (
            <div className="empty-state">
              <span className="chip chip-round tone-2">
                <Icon name="check" size={20} />
              </span>
              {t('All caught up — no open change requests.')}
            </div>
          ) : (
            <ul className="activity-list">
              {openRequests.map((r) => (
                <li className="activity-item" key={r.id}>
                  <span className={`chip chip-round${r.document_id ? '' : ' tone-4'}`}>
                    <Icon name={r.document_id ? 'file-text' : 'help-circle'} size={17} />
                  </span>
                  <div className="activity-main">
                    <span className="activity-title">
                      <Link to={`/admin/structures/${r.structure_id}`}>
                        {r.structure_name || t('structure')}
                      </Link>
                    </span>
                    <span className="activity-sub">
                      {r.document_id ? t('Document change request') : r.title || t('Request')} ·{' '}
                      {r.host_email || t('host removed')}
                    </span>
                  </div>
                  <span className="activity-time">{timeAgo(r.created_at, t)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      ),
    },
    {
      key: 'questionCategories',
      title: t('What guests ask'),
      content: (
        <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="page-head">
            <h2 style={{ fontSize: 17 }}>{t('What guests ask')}</h2>
            <span className="muted">{t('{n} questions', { n: analytics?.total || 0 })}</span>
          </div>
          {!analytics || analytics.total === 0 ? (
            <div className="empty-state">
              <span className="chip chip-round tone-3">
                <Icon name="message-circle" size={20} />
              </span>
              {t('No guest questions yet — categories appear here as guests start asking.')}
            </div>
          ) : (
            <div className="qcat-list">
              {analytics.categories.map((cat, i) => {
                const maxCount = analytics.categories[0]?.count || 1
                return (
                  <div className="qcat" key={cat.label}>
                    <div className="qcat-head">
                      <span className="qcat-label">{cat.label}</span>
                      <span className="muted">
                        {cat.count} · {Math.round(cat.share * 100)}%
                      </span>
                    </div>
                    <div className="qbar">
                      <span
                        className="qbar-fill"
                        style={{
                          width: `${Math.max(6, Math.round((cat.count / maxCount) * 100))}%`,
                          background: BAR_COLORS[i % BAR_COLORS.length],
                        }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      ),
    },
    {
      key: 'quickActions',
      title: t('Quick actions'),
      bare: true,
      content: (
        <section
          className="card card-promo"
          style={{ height: '100%', justifyContent: 'center' }}
        >
          <h2>{t('Set up a new property')}</h2>
          <p className="muted">
            {t(
              'Create a structure, add its units and manuals, then share a guest link — the assistant answers from those documents only.',
            )}
          </p>
          <div className="form-actions">
            <Link className="btn btn-ghost btn-sm" to="/admin/structures">
              <Icon name="plus" size={14} /> {t('New structure')}
            </Link>
            <Link className="btn btn-ghost btn-sm" to="/admin/change-requests">
              <Icon name="clipboard" size={14} /> {t('Change requests')}
            </Link>
            <Link className="btn btn-ghost btn-sm" to="/admin/profile">
              <Icon name="user" size={14} /> {t('Profile settings')}
            </Link>
          </div>
        </section>
      ),
    },
  ]

  return (
    <>
      <div className="page-head">
        <div>
          <h1>{t('Welcome back, {name}', { name: profile?.display_name || t('Admin') })}</h1>
          <p className="page-hero-sub">{t("Here's what is happening across your properties.")}</p>
        </div>
        <button
          className={`btn btn-sm${customizing ? '' : ' btn-ghost'}`}
          onClick={() => setCustomizing((v) => !v)}
        >
          <Icon name={customizing ? 'check' : 'grip'} size={14} />{' '}
          {customizing ? t('Done arranging') : t('Customize layout')}
        </button>
      </div>
      {customizing && (
        <div className="form-actions">
          <button className="btn btn-ghost btn-sm" onClick={handleResetLayout}>
            {t('Reset layout to default')}
          </button>
        </div>
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
