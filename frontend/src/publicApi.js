// Public API client — unauthenticated endpoints reachable from the landing page.
// No token, no secrets: just the backend origin.
import { BACKEND_URL } from './backendUrl.js'

export class PublicApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

// Submit a "book a visit" lead from the landing page.
// payload: { structure_name, city?, business_type?, contact_name, contact_email, preferred_date? }
export async function submitVisitRequest(payload) {
  let response
  try {
    response = await fetch(`${BACKEND_URL}/api/public/visit-requests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new PublicApiError('Cannot reach the server.', 0)
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      /* keep default */
    }
    throw new PublicApiError(message, response.status)
  }
  return response.json()
}
