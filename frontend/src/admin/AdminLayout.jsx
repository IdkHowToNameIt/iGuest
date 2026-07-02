import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import { getProfile, getStats } from './adminApi.js'
import Icon from '../components/Icon.jsx'
import ThemeToggle from '../components/ThemeToggle.jsx'
import UserMenu from '../components/UserMenu.jsx'
import { useT, LangToggle } from '../i18n/index.jsx'
import './admin.css'

// `badge` is a key into the stats object (or null); resolved to a live count below.
const NAV = [
  { to: '/admin', label: 'Dashboard', icon: 'dashboard', end: true, badge: null },
  { to: '/admin/structures', label: 'Structures', icon: 'building', end: false, badge: 'structures' },
  { to: '/admin/change-requests', label: 'Requests', icon: 'clipboard', end: false, badge: 'open_requests' },
  { to: '/admin/accounts', label: 'Admin accounts', icon: 'users', end: false, badge: null },
]

// Shell around every authenticated admin page: a dark navy sidebar (brand +
// nav + logout) and a light topbar (theme + account menu), with an <Outlet />
// for the matched page.
export default function AdminLayout() {
  const { logout } = useAuth()
  const { t } = useT()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(() => {
        /* topbar avatar just falls back to initials */
      })
    getStats()
      .then(setStats)
      .catch(() => {
        /* nav badges just stay hidden */
      })
  }, [])

  // Live nav-badge counts (concept shows a pill count next to each nav item).
  const badgeCounts = {
    structures: stats?.structures || 0,
    open_requests: (stats?.open_change_requests || 0) + (stats?.new_visit_requests || 0),
  }

  function handleLogout() {
    logout()
    navigate('/admin/login', { replace: true })
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-mark">
            <Icon name="home" size={20} />
          </span>
          <div>
            <div className="sidebar-brand-name">iGuest</div>
            <div className="sidebar-brand-sub">{t('Admin panel')}</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          {NAV.map((item) => {
            const count = item.badge ? badgeCounts[item.badge] : 0
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
              >
                <span className="sidebar-link-icon">
                  <Icon name={item.icon} size={18} />
                </span>
                <span className="sidebar-link-label">{t(item.label)}</span>
                {count > 0 && <span className="sidebar-badge">{count}</span>}
              </NavLink>
            )
          })}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-card">
            <div className="sidebar-card-title">{t('Free plan · Gemini')}</div>
            <div className="sidebar-card-sub">{t('Multilingual guest assistant')}</div>
          </div>
          <button className="btn btn-sm" onClick={handleLogout}>
            <Icon name="power" size={15} /> <span className="sidebar-link-label">{t('Log out')}</span>
          </button>
        </div>
      </aside>

      <div className="shell-content">
        <header className="topbar">
          <span className="topbar-title">{t('Admin panel')}</span>
          <div className="topbar-actions">
            <LangToggle />
            <ThemeToggle />
            <UserMenu
              name={profile?.display_name || t('Admin')}
              avatarUrl={profile?.avatar_url}
              settingsPath="/admin/profile"
              onLogout={handleLogout}
            />
          </div>
        </header>
        <main className="admin-main">
          <Outlet context={{ profile, refreshProfile: () => getProfile().then(setProfile) }} />
        </main>
      </div>
    </div>
  )
}
