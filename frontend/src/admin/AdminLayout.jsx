import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import { getProfile } from './adminApi.js'
import ThemeToggle from '../components/ThemeToggle.jsx'
import UserMenu from '../components/UserMenu.jsx'
import './admin.css'

const NAV = [
  { to: '/admin', label: 'Dashboard', icon: '📊', end: true },
  { to: '/admin/structures', label: 'Structures', icon: '🏢', end: false },
  { to: '/admin/change-requests', label: 'Change requests', icon: '📝', end: false },
  { to: '/admin/accounts', label: 'Admin accounts', icon: '👤', end: false },
]

// Shell around every authenticated admin page: a sidebar (brand + nav + logout)
// and a topbar (search, notifications, account menu), with an <Outlet /> for
// the matched page.
export default function AdminLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(() => {
        /* topbar avatar just falls back to initials */
      })
  }, [])

  function handleLogout() {
    logout()
    navigate('/admin/login', { replace: true })
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="sidebar-brand-icon">🏠</span>
          <div>
            <div className="sidebar-brand-name">GuestReply</div>
            <div className="sidebar-brand-sub">Admin</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
            >
              <span className="sidebar-link-icon">{item.icon}</span>
              <span className="sidebar-link-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
            ⏻ Log out
          </button>
        </div>
      </aside>

      <div className="shell-content">
        <header className="topbar">
          <span className="topbar-title">Admin panel</span>
          <div className="topbar-actions">
            <button type="button" className="icon-btn" aria-label="Notifications">
              🔔
            </button>
            <ThemeToggle />
            <UserMenu
              name={profile?.display_name || 'Admin'}
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
