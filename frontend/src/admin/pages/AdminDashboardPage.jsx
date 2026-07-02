import { useEffect, useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import { getStats, listStructures, listChangeRequests } from '../adminApi.js'
import { useAuth } from '../auth.jsx'
import Icon from '../../components/Icon.jsx'
import DashboardGrid, { resetLayout } from '../../components/DashboardGrid.jsx'

const LAYOUT_KEY = 'iguest_admin_dashboard_layout_v2'
const DEFAULT_LAYOUT = [
  { i: 'overview', x: 0, y: 0, w: 12, h: 3 },
  { i: 'recentStructures', x: 0, y: 3, w: 7, h: 8 },
  { i: 'openChangeRequests', x: 7, y: 3, w: 5, h: 8 },
  { i: 'quickActions', x: 0, y: 11, w: 12, h: 4 },
]

function locationLine(s) {
  const parts = [s.city, s.province, s.region].filter(Boolean)
  return parts.length ? parts.join(' Â· ') : 'No location set'
}

// Compact relative timestamp for the activity feed ("5m ago", "2h ago", â€¦).
function timeAgo(iso) {
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = seconds / 60
  if (minutes < 60) return `${Math.floor(minutes)}m ago`
  const hours = minutes / 60
  if (hours < 24) return `${Math.floor(hours)}h ago`
  const days = hours / 24
  if (days < 7) return `${Math.floor(days)}d ago`
  return new Date(iso).toLocaleDateString()
}

// The admin's home: dashboard overview built from free-form blocks (see
// DashboardGrid) â€” drag/resize is available via "Customize layout".
export default function AdminDashboardPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { profile } = useOutletContext() ?? {}

  const [stats, setStats] = useState(null)
  const [recentStructures, setRecentStructures] = useState([])
  const [openRequests, setOpenRequests] = useState([])
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
      const [s, structures, requests] = await Promise.all([
        getStats(),
        listStructures({}),
        listChangeRequests({ status: 'open' }),
      ])
      setStats(s)
      setRecentStructures(structures.slice(-6).reverse())
      setOpenRequests(requests.slice(0, 6))
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

  if (loading) return <p className="muted">Loadingâ€¦</p>
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
      title: 'Overview',
      bare: true,
      content: (
        <div className="stat-grid" style={{ height: '100%', alignContent: 'start' }}>
          {statCards.map((c) => (
            <div className="stat-card" key={c.label}>
              <div className="stat-card-top">
                <span className="stat-card-label">{c.label}</span>
                <span className={`chip${c.tone}`}>
                  <Icon name={c.icon} size={19} />
                </span>
              </div>
              <span className="stat-card-value">{c.value}</span>
              <Link className="stat-card-link" to={c.to}>
                {c.linkLabel} <Icon name="arrow-right" size={13} />
              </Link>
            </div>
          ))}
        </div>
      ),
    },
    {
      key: 'recentStructures',
      title: 'Recent structures',
      content: (
        <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Recent structures</h2>
          {recentStructures.length === 0 ? (
            <div className="empty-state">
              <span className="chip chip-round">
                <Icon name="building" size={20} />
              </span>
              No structures yet â€” create your first one to get started.
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
                      <Icon name="map-pin" size={12} /> {locationLine(s)}
                    </span>
                  </div>
                  <Link className="btn btn-ghost btn-sm" to={`/admin/structures/${s.id}`}>
                    Open
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
      title: 'Recent activity',
      content: (
        <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="page-head">
            <h2 style={{ fontSize: 17 }}>Recent activity</h2>
            <Link className="btn btn-ghost btn-sm" to="/admin/change-requests">
              View all
            </Link>
          </div>
          {openRequests.length === 0 ? (
            <div className="empty-state">
              <span className="chip chip-round tone-2">
                <Icon name="check" size={20} />
              </span>
              All caught up â€” no open change requests.
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
                        {r.structure_name || 'structure'}
                      </Link>
                    </span>
                    <span className="activity-sub">
                      {r.document_id ? 'Document change request' : r.title || 'Request'} Â·{' '}
                      {r.host_email || 'host removed'}
                    </span>
                  </div>
                  <span className="activity-time">{timeAgo(r.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      ),
    },
    {
      key: 'quickActions',
      title: 'Quick actions',
      bare: true,
      content: (
        <section
          className="card card-promo"
          style={{ height: '100%', justifyContent: 'center' }}
        >
          <h2>Set up a new property</h2>
          <p className="muted">
            Create a structure, add its units and manuals, then share a guest link â€” the
            assistant answers from those documents only.
          </p>
          <div className="form-actions">
            <Link className="btn btn-ghost btn-sm" to="/admin/structures">
              <Icon name="plus" size={14} /> New structure
            </Link>
            <Link className="btn btn-ghost btn-sm" to="/admin/change-requests">
              <Icon name="clipboard" size={14} /> Change requests
            </Link>
            <Link className="btn btn-ghost btn-sm" to="/admin/profile">
              <Icon name="user" size={14} /> Profile settings
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
          <h1>Welcome back, {profile?.display_name || 'Admin'}</h1>
          <p className="page-hero-sub">Here's what is happening across your properties.</p>
        </div>
        <button
          className={`btn btn-sm${customizing ? '' : ' btn-ghost'}`}
          onClick={() => setCustomizing((v) => !v)}
        >
          <Icon name={customizing ? 'check' : 'grip'} size={14} />{' '}
          {customizing ? 'Done arranging' : 'Customize layout'}
        </button>
      </div>
      {customizing && (
        <div className="form-actions">
          <button className="btn btn-ghost btn-sm" onClick={handleResetLayout}>
            Reset layout to default
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
