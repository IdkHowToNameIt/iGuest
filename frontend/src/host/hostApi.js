// Host API client. Talks to the protected /api/host endpoints with a bearer
// token (the host JWT from /api/host/login), kept in localStorage. Mirrors the
// admin client but with its own token key so an admin and a host can be signed
// in in the same browser without clobbering each other.

import { BACKEND_URL } from '../backendUrl.js'

const TOKEN_KEY = 'guestreply_host_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export class HostApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  let payload
  if (isForm) {
    payload = body // FormData — let the browser set the multipart boundary
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(`${BACKEND_URL}${path}`, { method, headers, body: payload })
  } catch {
    throw new HostApiError('Cannot reach the server.', 0)
  }

  if (response.status === 204) return null

  let data = null
  try {
    data = await response.json()
  } catch {
    // empty / non-JSON body
  }

  if (!response.ok) {
    const message =
      (data && (typeof data.detail === 'string' ? data.detail : data.detail?.message)) ||
      `Request failed (${response.status})`
    throw new HostApiError(message, response.status)
  }
  return data
}

// ── auth ───────────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  request('/api/host/login', { method: 'POST', body: { email, password } })
export const changePassword = (currentPassword, newPassword) =>
  request('/api/host/change-password', {
    method: 'POST',
    body: { current_password: currentPassword, new_password: newPassword },
  })

// ── profile / content ────────────────────────────────────────────────────────────
export const getMe = () => request('/api/host/me')
export const uploadAvatar = (file) => {
  const form = new FormData()
  form.set('file', file)
  return request('/api/host/me/avatar', { method: 'POST', body: form, isForm: true })
}
export const deleteAvatar = () => request('/api/host/me/avatar', { method: 'DELETE' })
export const listDocuments = () => request('/api/host/documents')
export const getDocumentContent = (id) => request(`/api/host/documents/${id}/content`)
export const listFaqs = () => request('/api/host/faqs')
export const getAnalytics = () => request('/api/host/analytics')
export const getUnitAnalytics = (unitId) => request(`/api/host/units/${unitId}/analytics`)

// ── change requests ──────────────────────────────────────────────────────────────
export const listChangeRequests = () => request('/api/host/change-requests')
// documentId set -> request about a document; otherwise pass a `title` for an
// "other" problem (the two are mutually exclusive on the backend).
export const createChangeRequest = (body, documentId, title) =>
  request('/api/host/change-requests', {
    method: 'POST',
    body: { body, document_id: documentId || null, title: title || null },
  })
