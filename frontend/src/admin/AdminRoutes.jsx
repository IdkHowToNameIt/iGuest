import { Routes, Route } from 'react-router-dom'
import { AuthProvider, RequireAuth } from './auth.jsx'
import AdminLayout from './AdminLayout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import AdminDashboardPage from './pages/AdminDashboardPage.jsx'
import AdminProfilePage from './pages/AdminProfilePage.jsx'
import AdminAccountsPage from './pages/AdminAccountsPage.jsx'
import AdminChangePasswordPage from './pages/AdminChangePasswordPage.jsx'
import StructuresPage from './pages/StructuresPage.jsx'
import StructureDetailPage from './pages/StructureDetailPage.jsx'
import UnitDetailPage from './pages/UnitDetailPage.jsx'
import RequestsPage from './pages/RequestsPage.jsx'

// The whole admin subtree, kept in its own component so App.jsx stays readable.
export default function AdminRoutes() {
  return (
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
          <Route path="change-requests" element={<RequestsPage />} />
          <Route path="accounts" element={<AdminAccountsPage />} />
          <Route path="profile" element={<AdminProfilePage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
