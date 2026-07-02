import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage.jsx'
import Landing from './pages/Landing.jsx'
import AdminRoutes from './admin/AdminRoutes.jsx'
import { HostAuthProvider, RequireHostAuth } from './host/hostAuth.jsx'
import HostLayout from './host/HostLayout.jsx'
import HostLoginPage from './host/pages/HostLoginPage.jsx'
import HostDashboardPage from './host/pages/HostDashboardPage.jsx'
import HostChangePasswordPage from './host/pages/HostChangePasswordPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Guest chat opened via the capability link */}
        <Route path="/c/:token" element={<ChatPage />} />

        {/* Admin panel (not linked from the public landing; reachable by URL and
            protected by the admin login). */}
        <Route path="/admin/*" element={<AdminRoutes />} />

        {/* Host portal */}
        <Route
          path="/host/*"
          element={
            <HostAuthProvider>
              <Routes>
                <Route path="login" element={<HostLoginPage />} />
                <Route
                  path="change-password"
                  element={
                    <RequireHostAuth allowDuringPasswordChange>
                      <HostLayout />
                    </RequireHostAuth>
                  }
                >
                  <Route index element={<HostChangePasswordPage />} />
                </Route>
                <Route
                  path=""
                  element={
                    <RequireHostAuth>
                      <HostLayout />
                    </RequireHostAuth>
                  }
                >
                  <Route index element={<HostDashboardPage />} />
                </Route>
              </Routes>
            </HostAuthProvider>
          }
        />

        {/* Public landing (home) */}
        <Route path="*" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  )
}
