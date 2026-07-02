import { useEffect, useState } from 'react'
import { BACKEND_URL } from '../backendUrl.js'
import Icon from './Icon.jsx'

function initialsOf(name) {
  const trimmed = (name || '').trim()
  if (!trimmed) return '?'
  return trimmed
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

// Full-screen preview of the picture, closable via the X, a backdrop click, or Escape.
function Lightbox({ src, onClose }) {
  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div className="lightbox-backdrop" onClick={onClose}>
      <button type="button" className="lightbox-close" onClick={onClose} aria-label="Close">
        <Icon name="x" size={18} />
      </button>
      <img className="lightbox-img" src={src} alt="" onClick={(e) => e.stopPropagation()} />
    </div>
  )
}

// Circular avatar: shows the uploaded picture (avatarUrl is a backend-relative
// path, e.g. "/uploads/avatars/xyz.png") or falls back to initials from `name`.
// Pass `zoomable` to let the guest/host/admin click the picture to see it full-size.
export default function Avatar({ name, avatarUrl, size = 36, zoomable = false }) {
  const [expanded, setExpanded] = useState(false)
  const src = avatarUrl ? `${BACKEND_URL}${avatarUrl}` : null
  const clickable = zoomable && src

  return (
    <>
      <span
        className={`avatar${clickable ? ' avatar-zoomable' : ''}`}
        style={{ '--avatar-size': `${size}px` }}
        onClick={clickable ? () => setExpanded(true) : undefined}
        role={clickable ? 'button' : undefined}
        tabIndex={clickable ? 0 : undefined}
        aria-label={clickable ? 'View full-size picture' : undefined}
        onKeyDown={
          clickable
            ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') setExpanded(true)
              }
            : undefined
        }
      >
        {src ? (
          <img className="avatar-img" src={src} alt="" />
        ) : (
          <span className="avatar-fallback">{initialsOf(name)}</span>
        )}
      </span>
      {expanded && clickable && <Lightbox src={src} onClose={() => setExpanded(false)} />}
    </>
  )
}
