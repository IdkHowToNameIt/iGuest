import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage.jsx'
import Landing from './pages/Landing.jsx'
import { AuthProvider, RequireAuth } from './admin/auth.jsx'
import AdminLayout from './admin/AdminLayout.jsx'
import LoginPage from './admin/pages/LoginPage.jsx'
import AdminDashboardPage from './admin/pages/AdminDashboardPage.jsx'
import AdminProfilePage from './admin/pages/AdminProfilePage.jsx'
import AdminAccountsPage from './admin/pages/AdminAccountsPage.jsx'
import AdminChangePasswordPage from './admin/pages/AdminChangePasswordPage.jsx'
import StructuresPage from './admin/pages/StructuresPage.jsx'
import StructureDetailPage from './admin/pages/StructureDetailPage.jsx'
import UnitDetailPage from './admin/pages/UnitDetailPage.jsx'
import ChangeRequestsPage from './admin/pages/ChangeRequestsPage.jsx'
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

        {/* Admin */}
        <Route
          path="/admin/*"
          element={
            <AuthProvider>
              <Routes>
                <Route path="login" element={<LoginPage />} />
                <Route
                  path="change-password"
                  element={
                    <RequireAuth allowDuringPasswordChange>
                      <AdminLayout />
                    </RequireAuth>
                  }
                >
                  <Route index element={<AdminChangePasswordPage />} />
                </Route>
                <Route
                  path=""
                  element={
                    <RequireAuth>
                      <AdminLayout />
                    </RequireAuth>
                  }
                >
                  <Route index element={<AdminDashboardPage />} />
                  <Route path="structures" element={<StructuresPage />} />
                  <Route path="structures/:id" element={<StructureDetailPage />} />
                  <Route path="units/:id" element={<UnitDetailPage />} />
                  <Route path="change-requests" element={<ChangeRequestsPage />} />
                  <Route path="accounts" element={<AdminAccountsPage />} />
                  <Route path="profile" element={<AdminProfilePage />} />
                </Route>
              </Routes>
            </AuthProvider>
          }
        />

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

        <Route path="*" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  )
}
