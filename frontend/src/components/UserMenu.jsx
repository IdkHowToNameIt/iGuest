import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Avatar from './Avatar.jsx'

// Topbar avatar dropdown: profile name/email, a link to profile settings, and
// log out. Mirrors ThemeToggle's open/close-on-outside-click pattern.
export default function UserMenu({ name, email, avatarUrl, settingsPath, onLogout }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div className="user-menu" ref={ref}>
      <button
        type="button"
        className="user-menu-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label="Account menu"
        aria-expanded={open}
      >
        <Avatar name={name || email} avatarUrl={avatarUrl} size={30} />
        {name && <span className="user-menu-name">{name}</span>}
      </button>
      {open && (
        <div className="user-menu-menu" role="menu">
          <div className="user-menu-header">
            <span className="user-menu-header-name">{name || 'Account'}</span>
            {email && <span className="user-menu-header-sub">{email}</span>}
          </div>
          {settingsPath && (
            <Link className="user-menu-item" to={settingsPath} onClick={() => setOpen(false)}>
              👤 Profile settings
            </Link>
          )}
          <button type="button" className="user-menu-item" onClick={onLogout}>
            ⏻ Log out
          </button>
        </div>
      )}
    </div>
  )
}
