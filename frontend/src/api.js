// Guest API client. No secrets here — only the public backend URL and the
// capability token that arrives in the page URL.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

// Error carrying a machine-readable `code` so the UI can show the right screen.
// codes: not_found | revoked | expired | not_yet_valid | network | server
export class ApiError extends Error {
  constructor(code, message, status) {
    super(message || code)
    this.code = code
    this.status = status
  }
}

async function parseError(response) {
  let code = 'server'
  let message = `Request failed (${response.status})`
  try {
    const body = await response.json()
    // FastAPI returns { detail: { code, message } } for link errors
    if (body?.detail?.code) {
      code = body.detail.code
      message = body.detail.message || message
    } else if (typeof body?.detail === 'string') {
      message = body.detail
    }
  } catch {
    // non-JSON body; keep defaults
  }
  return new ApiError(code, message, response.status)
}

export async function getOpening(token) {
  let response
  try {
    response = await fetch(`${BACKEND_URL}/api/guest/${encodeURIComponent(token)}/opening`)
  } catch {
    throw new ApiError('network', 'Cannot reach the server.')
  }
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function getHistory(token) {
  let response
  try {
    response = await fetch(`${BACKEND_URL}/api/guest/${encodeURIComponent(token)}/history`)
  } catch {
    throw new ApiError('network', 'Cannot reach the server.')
  }
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function getFaqs(token) {
  let response
  try {
    response = await fetch(`${BACKEND_URL}/api/guest/${encodeURIComponent(token)}/faqs`)
  } catch {
    throw new ApiError('network', 'Cannot reach the server.')
  }
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function sendMessage(token, message) {
  let response
  try {
    response = await fetch(`${BACKEND_URL}/api/guest/${encodeURIComponent(token)}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
  } catch {
    throw new ApiError('network', 'Cannot reach the server.')
  }
  if (!response.ok) throw await parseError(response)
  return response.json()
}
