import { createContext, useContext, useState, useCallback } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getToken, setToken, login as apiLogin } from './adminApi.js'

// Auth context for the admin panel. The JWT lives in localStorage (see
// adminApi.js); additionally we remember whether the caller must change their
// (initially temporary) password — only ever true for a DB-backed admin
// account created from the panel, never for the legacy .env admin — so the
// guard can force that step first, mirroring the host portal's flow.

const MUST_CHANGE_KEY = 'guestreply_admin_must_change'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => getToken())
  const [mustChangePassword, setMustChange] = useState(
    () => localStorage.getItem(MUST_CHANGE_KEY) === '1',
  )

  const login = useCallback(async (username, password) => {
    const data = await apiLogin(username, password)
    setToken(data.access_token)
    setTokenState(data.access_token)
    const must = Boolean(data.must_change_password)
    localStorage.setItem(MUST_CHANGE_KEY, must ? '1' : '0')
    setMustChange(must)
    return data
  }, [])

  const clearMustChange = useCallback(() => {
    localStorage.setItem(MUST_CHANGE_KEY, '0')
    setMustChange(false)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setTokenState(null)
    localStorage.removeItem(MUST_CHANGE_KEY)
    setMustChange(false)
  }, [])

  const value = { isAuthenticated: Boolean(token), mustChangePassword, login, logout, clearMustChange }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}

// Route guard: redirects to the login page, remembering where we came from so
// the login page can send us back after a successful sign-in. Also bounces to
// the change-password page until a temporary password has been rotated.
export function RequireAuth({ children, allowDuringPasswordChange = false }) {
  const { isAuthenticated, mustChangePassword } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace state={{ from: location }} />
  }
  if (mustChangePassword && !allowDuringPasswordChange) {
    return <Navigate to="/admin/change-password" replace />
  }
  return children
}
