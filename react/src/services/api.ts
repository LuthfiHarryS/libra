// Axios instance — baseURL='/api' (relative, Vite proxy handles → http://localhost:8080/api)
// DO NOT use absolute URL here — Vite proxy won't intercept absolute URLs
import axios from 'axios'
import useAuthStore from '../store/authStore'

const api = axios.create({
  baseURL: '/api',
})

// Inject Bearer token on every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401: logout + redirect to /login?expired=1
// useAuthStore.getState() works outside React because Zustand exposes getState() on the store object
// No circular import: api.ts imports authStore, authStore does NOT import api.ts
//
// PENGECUALIAN: /auth/login. Di sana 401 = "password salah", BUKAN "session expired" —
// user belum punya session. Biarkan error lewat ke LoginPage untuk display inline.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url ?? ''
    const isLoginAttempt = url.endsWith('/auth/login')
    if (error.response?.status === 401 && !isLoginAttempt) {
      useAuthStore.getState().logout()
      window.location.href = '/login?expired=1'
    }
    return Promise.reject(error)
  }
)

export default api
