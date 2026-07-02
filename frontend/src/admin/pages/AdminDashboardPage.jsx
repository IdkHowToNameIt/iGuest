import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getStats, listStructures, listChangeRequests } from '../adminApi.js'
import { useAuth } from '../auth.jsx'
import DashboardGrid, { resetLayout } from '../../components/DashboardGrid.jsx'

const LAYOUT_KEY = 'guestreply_admin_dashboard_layout_v1'
const DEFAULT_LAYOUT = [
  { i: 'overview', x: 0, y: 0, w: 12, h: 4 },
  { i: 'recentStructures', x: 0, y: 4, w: 6, h: 8 },
  { i: 'openChangeRequests', x: 6, y: 4, w: 6, h: 8 },
  { i: 'quickActions', x: 0, y: 12, w: 12, h: 3 },
]

function locationLine(s) {
  const parts = [s.city, s.province, s.region].filter(Boolean)
  return parts.length ? parts.join(' · ') : 'No location set'
}

// The admin's home: dashboard overview built from free-form blocks (see
// DashboardGrid) — drag/resize is available via "Customize layout".
export default function AdminDashboardPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()

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
      setRecentStructures(structures.slice(-5).reverse())
      setOpenRequests(requests.slice(0, 5))
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

  if (loading) return <p className="muted">Loading…</p>
  if (error) return <p className="error-text">{error}</p>

  const blocks = [
    {
      key: 'overview',
      title: 'Overview',
      content: (
        <section className="card" style={{ height: '100%' }}>
          <h2>Overview</h2>
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-card-icon">🏢</span>
              <span className="stat-card-label">Structures</span>
              <span className="stat-card-value">{stats.structures}</span>
            </div>
            <div className="stat-card">
              <span className="stat-card-icon tone-2">🛏️</span>
              <span className="stat-card-label">Units</span>
              <span className="stat-card-value">{stats.units}</span>
            </div>
            <div className="stat-card">
              <span className="stat-card-icon">🔗</span>
              <span className="stat-card-label">Active guest links</span>
              <span className="stat-card-value">{stats.active_links}</span>
            </div>
            <div className="stat-card">
              <span className="stat-card-icon tone-2">📝</span>
              <span className="stat-card-label">Open change requests</span>
              <span className="stat-card-value">{stats.open_change_requests}</span>
            </div>
          </div>
        </section>
      ),
    },
    {
      key: 'recentStructures',
      title: 'Recent structures',
      content: (
        <section className="card">
          <h2>Recent structures</h2>
          {recentStructures.length === 0 ? (
            <p className="muted">No structures yet.</p>
          ) : (
            <ul className="list">
              {recentStructures.map((s) => (
                <li className="row" key={s.id}>
                  <div className="row-main">
                    <span className="row-title">
                      <Link to={`/admin/structures/${s.id}`}>{s.name}</Link>
                    </span>
                    <span className="row-sub">📍 {locationLine(s)}</span>
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
      title: 'Open change requests',
      content: (
        <section className="card">
          <h2>Open change requests</h2>
          {openRequests.length === 0 ? (
            <p className="muted">Nothing pending.</p>
          ) : (
            <ul className="list">
              {openRequests.map((r) => (
                <li className="row" key={r.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                  <div className="row-main">
                    <span className="row-title">
                      <Link to={`/admin/structures/${r.structure_id}`}>
                        {r.structure_name || 'structure'}
                      </Link>
                    </span>
                    <span className="row-sub">
                      {r.host_email || 'host removed'} · {new Date(r.created_at).toLocaleString()}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <div className="form-actions">
            <Link className="btn btn-ghost btn-sm" to="/admin/change-requests">
              View all change requests
            </Link>
          </div>
        </section>
      ),
    },
    {
      key: 'quickActions',
      title: 'Quick actions',
      content: (
        <section className="card">
          <h2>Quick actions</h2>
          <div className="form-actions">
            <Link className="btn btn-sm" to="/admin/structures">
              + New structure
            </Link>
            <Link className="btn btn-ghost btn-sm" to="/admin/change-requests">
              Change requests
            </Link>
            <Link className="btn btn-ghost btn-sm" to="/admin/profile">
              Profile settings
            </Link>
          </div>
        </section>
      ),
    },
  ]

  return (
    <>
      <div className="page-head">
        <h1>Dashboard</h1>
        <button
          className={`btn btn-sm${customizing ? '' : ' btn-ghost'}`}
          onClick={() => setCustomizing((v) => !v)}
        >
          {customizing ? '✓ Done arranging' : '⠿ Customize layout'}
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
