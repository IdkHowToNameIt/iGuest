import { createContext, useContext, useState, useCallback } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getToken, setToken, login as apiLogin } from './hostApi.js'

// Auth context for the host portal. Like the admin one, the JWT lives in
// localStorage; additionally we remember whether the host must change their
// (initially temporary) password, so the guard can force that step first.

const MUST_CHANGE_KEY = 'iguest_host_must_change'

const HostAuthContext = createContext(null)

export function HostAuthProvider({ children }) {
  const [token, setTokenState] = useState(() => getToken())
  const [mustChangePassword, setMustChange] = useState(
    () => localStorage.getItem(MUST_CHANGE_KEY) === '1',
  )

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password)
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

  const value = {
    isAuthenticated: Boolean(token),
    mustChangePassword,
    login,
    logout,
    clearMustChange,
  }
  return <HostAuthContext.Provider value={value}>{children}</HostAuthContext.Provider>
}

export function useHostAuth() {
  const ctx = useContext(HostAuthContext)
  if (!ctx) throw new Error('useHostAuth must be used within a HostAuthProvider')
  return ctx
}

// Route guard: require a host token, and bounce to the change-password page
// until the temporary password has been rotated.
export function RequireHostAuth({ children, allowDuringPasswordChange = false }) {
  const { isAuthenticated, mustChangePassword } = useHostAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/host/login" replace state={{ from: location }} />
  }
  if (mustChangePassword && !allowDuringPasswordChange) {
    return <Navigate to="/host/change-password" replace />
  }
  return children
}
