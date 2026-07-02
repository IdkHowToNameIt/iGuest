// Admin API client. Talks to the protected /api/admin endpoints with a bearer
// token (the admin JWT obtained from /api/admin/login). The token is kept in
// localStorage and read on every request via getToken().

import { BACKEND_URL } from '../backendUrl.js'

const TOKEN_KEY = 'iguest_admin_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

// Thrown on any non-2xx response. `status` lets callers detect 401 (expired
// session) and bounce back to the login screen.
export class AdminApiError extends Error {
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
    payload = body // FormData â€” let the browser set the multipart boundary
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(`${BACKEND_URL}${path}`, { method, headers, body: payload })
  } catch {
    throw new AdminApiError('Cannot reach the server.', 0)
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
    throw new AdminApiError(message, response.status)
  }
  return data
}

// â”€â”€ auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function login(username, password) {
  return request('/api/admin/login', { method: 'POST', body: { username, password } })
}
export const changePassword = (currentPassword, newPassword) =>
  request('/api/admin/change-password', {
    method: 'POST',
    body: { current_password: currentPassword, new_password: newPassword },
  })

// â”€â”€ admin accounts (additional logins, alongside the legacy .env admin) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listAdmins = () => request('/api/admin/admins')
export const createAdmin = (username) =>
  request('/api/admin/admins', { method: 'POST', body: { username } })
// body: { is_active?, reset_password? }. Response carries temp_password when reset.
export const updateAdmin = (id, body) =>
  request(`/api/admin/admins/${id}`, { method: 'PATCH', body })
export const deleteAdmin = (id) => request(`/api/admin/admins/${id}`, { method: 'DELETE' })

// â”€â”€ structures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listStructures = ({ q, region, province, city } = {}) => {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (region) params.set('region', region)
  if (province) params.set('province', province)
  if (city) params.set('city', city)
  const qs = params.toString()
  return request(`/api/admin/structures${qs ? `?${qs}` : ''}`)
}
export const getStructure = (id) => request(`/api/admin/structures/${id}`)
export const createStructure = (body) =>
  request('/api/admin/structures', { method: 'POST', body })
export const updateStructure = (id, body) =>
  request(`/api/admin/structures/${id}`, { method: 'PATCH', body })
export const deleteStructure = (id) =>
  request(`/api/admin/structures/${id}`, { method: 'DELETE' })

// â”€â”€ units â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listUnits = (structureId) =>
  request(`/api/admin/structures/${structureId}/units`)
export const getUnit = (id) => request(`/api/admin/units/${id}`)
export const createUnit = (structureId, body) =>
  request(`/api/admin/structures/${structureId}/units`, { method: 'POST', body })
export const deleteUnit = (id) => request(`/api/admin/units/${id}`, { method: 'DELETE' })

// â”€â”€ documents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listDocuments = ({ structureId, unitId } = {}) => {
  const params = new URLSearchParams()
  if (structureId) params.set('structure_id', structureId)
  if (unitId) params.set('unit_id', unitId)
  const qs = params.toString()
  return request(`/api/admin/documents${qs ? `?${qs}` : ''}`)
}
export const uploadDocument = (scopeType, targetId, file) => {
  const form = new FormData()
  form.set('scope_type', scopeType)
  form.set('target_id', targetId)
  form.set('file', file)
  return request('/api/admin/documents', { method: 'POST', body: form, isForm: true })
}
export const getDocumentContent = (id) => request(`/api/admin/documents/${id}/content`)
export const deleteDocument = (id) =>
  request(`/api/admin/documents/${id}`, { method: 'DELETE' })

// â”€â”€ guest links â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listLinks = (unitId) => request(`/api/admin/units/${unitId}/links`)
export const createLink = (unitId, body = {}) =>
  request(`/api/admin/units/${unitId}/links`, { method: 'POST', body })
export const revokeLink = (id) =>
  request(`/api/admin/links/${id}/revoke`, { method: 'POST' })

// â”€â”€ conversations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listConversations = (unitId) =>
  request(`/api/admin/units/${unitId}/conversations`)
export const getConversation = (id) => request(`/api/admin/conversations/${id}`)
export const deleteConversation = (id) =>
  request(`/api/admin/conversations/${id}`, { method: 'DELETE' })

// â”€â”€ hosts (structure-scoped) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listHosts = (structureId) =>
  request(`/api/admin/structures/${structureId}/hosts`)
export const createHost = (structureId, email) =>
  request(`/api/admin/structures/${structureId}/hosts`, { method: 'POST', body: { email } })
// body: { is_active?, reset_password? }. Response carries temp_password when reset.
export const updateHost = (id, body) =>
  request(`/api/admin/hosts/${id}`, { method: 'PATCH', body })
export const deleteHost = (id) => request(`/api/admin/hosts/${id}`, { method: 'DELETE' })

// â”€â”€ document change requests (admin inbox) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const listChangeRequests = ({ status, structureId, type } = {}) => {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (structureId) params.set('structure_id', structureId)
  if (type) params.set('type', type)
  const qs = params.toString()
  return request(`/api/admin/change-requests${qs ? `?${qs}` : ''}`)
}
export const updateChangeRequest = (id, body) =>
  request(`/api/admin/change-requests/${id}`, { method: 'PATCH', body })

// â”€â”€ analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const getUnitAnalytics = (unitId) =>
  request(`/api/admin/units/${unitId}/analytics`)

// â”€â”€ admin profile (single account) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const getProfile = () => request('/api/admin/profile')
export const updateProfile = (body) => request('/api/admin/profile', { method: 'PATCH', body })
export const uploadAvatar = (file) => {
  const form = new FormData()
  form.set('file', file)
  return request('/api/admin/profile/avatar', { method: 'POST', body: form, isForm: true })
}
export const deleteAvatar = () => request('/api/admin/profile/avatar', { method: 'DELETE' })

// â”€â”€ dashboard stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const getStats = () => request('/api/admin/stats')
