// Per D-17, D-18: checks isAuthenticated, stores intended destination in location.state
import { Navigate, useLocation } from 'react-router'
import useAuthStore from '../store/authStore'

interface PrivateRouteProps {
  children: React.ReactElement
}

function PrivateRoute({ children }: PrivateRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

export default PrivateRoute
