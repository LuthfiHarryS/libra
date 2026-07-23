// Per D-04, D-05: URL scheme, root redirect based on auth state
// Toaster placed here per UI-SPEC §Toast
import { BrowserRouter, Routes, Route, Navigate } from 'react-router'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/authStore'
import PrivateRoute from './components/PrivateRoute'
import AdminPrivateRoute from './components/AdminPrivateRoute'
import ChatWidget from './components/ChatWidget'
import LoginPage from './pages/LoginPage'
import AdminDashboardPage from './pages/admin/AdminDashboardPage'
import AdminBooksPage from './pages/admin/AdminBooksPage'
import AdminBorrowsPage from './pages/admin/AdminBorrowsPage'
import RegisterPage from './pages/RegisterPage'
import NotFoundPage from './pages/NotFoundPage'
import CatalogPage from './pages/CatalogPage'
import BookDetailPage from './pages/BookDetailPage'
import BorrowStatusPage from './pages/BorrowStatusPage'
import FavoritePage from './pages/FavoritePage'
import ProfilePage from './pages/ProfilePage'

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)

  return (
    <BrowserRouter>
      <Routes>
        {/* Root redirect — admin ke /admin/dashboard, semua lain ke /katalog */}
        <Route
          path="/"
          element={<Navigate to={isAuthenticated && user?.role === 'admin' ? '/admin/dashboard' : '/katalog'} replace />}
        />

        {/* Public routes — no auth required */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/daftar" element={<RegisterPage />} />
        <Route path="/katalog" element={<CatalogPage />} />
        <Route path="/buku/:id" element={<BookDetailPage />} />

        {/* Protected routes — require login */}
        <Route
          path="/pinjaman"
          element={
            <PrivateRoute>
              <BorrowStatusPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/favorit"
          element={
            <PrivateRoute>
              <FavoritePage />
            </PrivateRoute>
          }
        />
        <Route
          path="/profil"
          element={
            <PrivateRoute>
              <ProfilePage />
            </PrivateRoute>
          }
        />

        {/* Admin routes — protected by AdminPrivateRoute (role='admin') — D-02 */}
        <Route path="/admin/dashboard" element={<AdminPrivateRoute><AdminDashboardPage /></AdminPrivateRoute>} />
        <Route path="/admin/buku"      element={<AdminPrivateRoute><AdminBooksPage /></AdminPrivateRoute>} />
        <Route path="/admin/pinjaman"  element={<AdminPrivateRoute><AdminBorrowsPage /></AdminPrivateRoute>} />

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { borderRadius: '8px', fontSize: '14px' },
        }}
      />

      {/* ChatWidget — floating FAB untuk siswa saja, CHAT-01 — D-10 */}
      {isAuthenticated && user?.role === 'siswa' && <ChatWidget />}
    </BrowserRouter>
  )
}

export default App
