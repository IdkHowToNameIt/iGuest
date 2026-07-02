import { useEffect, useRef, useState } from 'react'
import { getThemePreference, setThemePreference } from '../theme.js'
import Icon from './Icon.jsx'

const OPTIONS = [
  { value: 'light', label: 'Light', icon: 'sun' },
  { value: 'dark', label: 'Dark', icon: 'moon' },
  { value: 'system', label: 'System', icon: 'monitor' },
]

// Small collapsible menu to switch between light/dark/system theme. The choice
// is persisted per browser (see ../theme.js) and applied instantly.
export default function ThemeToggle() {
  const [pref, setPref] = useState(getThemePreference)
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  function choose(value) {
    setPref(value)
    setThemePreference(value)
    setOpen(false)
  }

  const current = OPTIONS.find((o) => o.value === pref) || OPTIONS[2]

  return (
    <div className="theme-toggle" ref={ref}>
      <button
        type="button"
        className="theme-toggle-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label="Change theme"
        aria-expanded={open}
      >
        <Icon name={current.icon} size={17} />
      </button>
      {open && (
        <div className="theme-toggle-menu" role="menu">
          {OPTIONS.map((o) => (
            <button
              key={o.value}
              type="button"
              role="menuitemradio"
              aria-checked={o.value === pref}
              className={`theme-toggle-option${o.value === pref ? ' active' : ''}`}
              onClick={() => choose(o.value)}
            >
              <Icon name={o.icon} size={16} /> {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
