// Zustand v5 — MUST use curried syntax create<T>()(...)
// NOT create<T>(...) — that is Zustand v4 syntax and causes TypeScript error in v5
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthUser } from '../types'

interface AuthState {
  token: string | null
  user: AuthUser | null
  isAuthenticated: boolean
  login: (token: string, user: AuthUser) => void
  logout: () => void
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (token, user) => set({ token, user, isAuthenticated: true }),
      logout: () => set({ token: null, user: null, isAuthenticated: false }),
    }),
    {
      name: 'libra-auth',  // localStorage key — per D-20
      // default storage is localStorage — no createJSONStorage needed in Zustand v5
    }
  )
)

export default useAuthStore
