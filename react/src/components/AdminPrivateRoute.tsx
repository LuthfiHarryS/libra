// Protects all /admin/* routes — requires both authenticated AND role='admin'
// If not authenticated or wrong role → redirect to /login (no state saved)
// Per D-01: separate from student PrivateRoute
import { Navigate } from 'react-router'
import useAuthStore from '../store/authStore'

interface AdminPrivateRouteProps {
  children: React.ReactElement
}

function AdminPrivateRoute({ children }: AdminPrivateRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)

  if (!isAuthenticated || user?.role !== 'admin') {
    return <Navigate to="/login" replace />
  }

  return children
}

export default AdminPrivateRoute
