import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useHostAuth } from './hostAuth.jsx'
import { getMe } from './hostApi.js'
import Icon from '../components/Icon.jsx'
import ThemeToggle from '../components/ThemeToggle.jsx'
import UserMenu from '../components/UserMenu.jsx'
import '../admin/admin.css'

// Shell around the authenticated host portal. Reuses the admin panel's sidebar
// shell/styling for a consistent look between the two panels.
export default function HostLayout() {
  const { logout } = useHostAuth()
  const navigate = useNavigate()
  const [me, setMe] = useState(null)

  useEffect(() => {
    getMe()
      .then(setMe)
      .catch(() => {
        /* topbar avatar just falls back to initials */
      })
  }, [])

  function handleLogout() {
    logout()
    navigate('/host/login', { replace: true })
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
            <div className="sidebar-brand-sub">Host portal</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/host" end className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            <span className="sidebar-link-icon">
              <Icon name="dashboard" size={18} />
            </span>
            <span className="sidebar-link-label">Dashboard</span>
          </NavLink>
          <NavLink
            to="/host/change-password"
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            <span className="sidebar-link-icon">
              <Icon name="key" size={18} />
            </span>
            <span className="sidebar-link-label">Change password</span>
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <button className="btn btn-sm" onClick={handleLogout}>
            <Icon name="power" size={15} /> <span className="sidebar-link-label">Log out</span>
          </button>
        </div>
      </aside>

      <div className="shell-content">
        <header className="topbar">
          <span className="topbar-title">Host portal</span>
          <div className="topbar-actions">
            <ThemeToggle />
            <UserMenu
              name={me?.email}
              avatarUrl={me?.avatar_url}
              settingsPath="/host"
              onLogout={handleLogout}
            />
          </div>
        </header>
        <main className="admin-main">
          <Outlet context={{ me, refreshMe: () => getMe().then(setMe) }} />
        </main>
      </div>
    </div>
  )
}
