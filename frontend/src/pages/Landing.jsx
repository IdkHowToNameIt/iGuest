import { Link } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import '../chat.css'

// Fallback page for any unmatched route (including the bare "/"). Guests reach
// the app through a capability link (/c/<token>); there is nothing public here
// other than a pointer to the admin panel.
export default function Landing() {
  return (
    <div className="screen-center">
      <div className="error-card">
        <div className="error-icon">
          <Icon name="home" size={26} />
        </div>
        <h2>iGuest</h2>
        <p>
          This is the guest assistant for short-term rentals. Guests access it
          through the personal link provided by their host.
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
          <Link className="btn" to="/admin">
            Admin panel
          </Link>
          <Link className="btn" to="/host">
            Host portal
          </Link>
        </div>
      </div>
    </div>
  )
}
