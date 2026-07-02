import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Avatar from './Avatar.jsx'
import Icon from './Icon.jsx'
import { useT } from '../i18n/index.jsx'

// Topbar avatar dropdown: profile name/email, a link to profile settings, and
// log out. Mirrors ThemeToggle's open/close-on-outside-click pattern.
export default function UserMenu({ name, email, avatarUrl, settingsPath, onLogout }) {
  const { t } = useT()
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
        aria-label={t('Account menu')}
        aria-expanded={open}
      >
        <Avatar name={name || email} avatarUrl={avatarUrl} size={30} />
        {name && <span className="user-menu-name">{name}</span>}
      </button>
      {open && (
        <div className="user-menu-menu" role="menu">
          <div className="user-menu-header">
            <span className="user-menu-header-name">{name || t('Account')}</span>
            {email && <span className="user-menu-header-sub">{email}</span>}
          </div>
          {settingsPath && (
            <Link className="user-menu-item" to={settingsPath} onClick={() => setOpen(false)}>
              <Icon name="user" size={16} /> {t('Profile settings')}
            </Link>
          )}
          <button type="button" className="user-menu-item" onClick={onLogout}>
            <Icon name="power" size={16} /> {t('Log out')}
          </button>
        </div>
      )}
    </div>
  )
}
