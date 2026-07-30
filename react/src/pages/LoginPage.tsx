import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router'
import { toast } from 'react-hot-toast'
import { Loader2, AlertCircle } from 'lucide-react'
import api from '../services/api'
import useAuthStore from '../store/authStore'
import PasswordInput from '../components/PasswordInput'

const inputStyle = (hasError: boolean): React.CSSProperties => ({
  width: '100%',
  padding: '12px 14px',
  border: `1.5px solid ${hasError ? 'var(--unavail)' : 'var(--border)'}`,
  borderRadius: '10px',
  background: 'var(--bg-input)',
  color: 'var(--text)',
  fontFamily: 'var(--font-ui)',
  fontSize: '14px',
  fontWeight: 500,
  outline: 'none',
  transition: 'border-color var(--transition), box-shadow var(--transition)',
})

function FormInput({
  type, value, onChange, placeholder, hasError, autoComplete,
}: { type: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; placeholder: string; hasError: boolean; autoComplete?: string }) {
  const [focused, setFocused] = useState(false)
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      autoComplete={autoComplete}
      style={{
        ...inputStyle(hasError),
        borderColor: hasError ? 'var(--unavail)' : focused ? 'var(--accent)' : 'var(--border)',
        boxShadow: focused && !hasError ? '0 0 0 3px rgba(217,119,6,.15)' : 'none',
      }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    />
  )
}

function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((state) => state.login)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    if (params.get('expired') === '1') {
      toast.error('Sesi berakhir, silakan login kembali.')
    }
  }, [location.search])

  useEffect(() => {
    if (isAuthenticated) {
      navigate(user?.role === 'admin' ? '/admin/dashboard' : '/katalog', { replace: true })
    }
  }, [isAuthenticated, navigate, user])

  const validate = (): boolean => {
    const newErrors: { username?: string; password?: string } = {}
    if (!username.trim()) newErrors.username = 'Kolom ini wajib diisi'
    if (!password) newErrors.password = 'Kolom ini wajib diisi'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (!validate()) return
    setIsLoading(true)
    try {
      const res = await api.post('/auth/login', { username: username.trim(), password })
      const { token, user } = res.data.data
      login(token, user)
      if (user.role === 'admin') {
        navigate('/admin/dashboard', { replace: true })
      } else {
        const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/katalog'
        navigate(from, { replace: true })
      }
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Login gagal. Coba lagi.'
      setFormError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row" style={{ background: 'var(--bg)' }}>
      {/* ── Left: illustration panel ─────────────────────────────── */}
      <div
        className="relative flex items-center justify-center overflow-hidden md:flex-1"
        style={{
          background: 'linear-gradient(150deg, var(--bg) 0%, var(--bg-card) 100%)',
          minHeight: 'clamp(180px, 30vh, 320px)',
          padding: 'clamp(20px, 4vw, 56px)',
        }}
      >
        {/* Decorative blobs */}
        <div
          className="absolute pointer-events-none"
          style={{ width: 420, height: 420, borderRadius: '50%', background: 'radial-gradient(circle, rgba(217,119,6,.18) 0%, transparent 70%)', filter: 'blur(90px)', top: -120, left: -80 }}
        />
        <div
          className="absolute pointer-events-none"
          style={{ width: 340, height: 340, borderRadius: '50%', background: 'radial-gradient(circle, rgba(30,77,107,.15) 0%, transparent 70%)', filter: 'blur(90px)', bottom: -80, right: -40 }}
        />

        <div className="relative z-10 flex flex-col items-center w-full max-w-[560px]">
          <img
            src="/study-illustration.png"
            alt="Dua siswa membaca buku bersama di perpustakaan"
            className="w-full h-auto"
            style={{ maxHeight: '62vh', objectFit: 'contain', borderRadius: '28px', boxShadow: 'var(--shadow-lg)' }}
          />
          <p
            className="hidden md:block text-center mt-8 text-[15px] font-semibold leading-relaxed"
            style={{ color: 'var(--text-2)', maxWidth: 420 }}
          >
            Jelajahi ribuan buku &amp; referensi akademik SMPN 1 Kemang — kapan saja, di mana saja.
          </p>
        </div>
      </div>

      {/* ── Right: login form panel — full height, no floating card ── */}
      <div
        className="flex items-center justify-center px-6 sm:px-12 py-12 md:flex-none md:w-[540px] lg:w-[620px]"
        style={{ background: 'var(--bg-card)', borderLeft: '1.5px solid var(--border)', boxShadow: 'var(--shadow-lg)' }}
      >
        <div className="relative z-10 w-full max-w-[440px]">
          {/* Brand */}
          <div className="text-center mb-6">
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '40px', fontWeight: 800, color: 'var(--accent)', display: 'block', lineHeight: 1 }}>
              LIBRA
            </span>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-3)', marginTop: 4, display: 'block', letterSpacing: '.02em' }}>
              Perpustakaan Digital SMPN 1 Kemang
            </span>
          </div>

          <p className="text-center text-[15px] font-bold mb-6" style={{ color: 'var(--text)' }}>Selamat datang kembali!</p>

          {formError && (
            <div
              role="alert"
              className="flex items-start gap-2.5 px-3.5 py-3 mb-4 rounded-[10px]"
              style={{
                background: 'var(--unavail-bg)',
                border: '1.5px solid var(--unavail)',
                color: 'var(--unavail)',
              }}
            >
              <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
              <p className="text-sm font-semibold leading-snug">{formError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-4">
              <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)', letterSpacing: '.02em' }}>Username</label>
              <FormInput type="text" value={username} onChange={e => { setUsername(e.target.value); setFormError(null) }} placeholder="cth: luthfi1" hasError={!!errors.username} autoComplete="username" />
              {errors.username && <p className="text-xs mt-1" style={{ color: 'var(--unavail)' }}>{errors.username}</p>}
            </div>

            <div className="mb-6">
              <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)', letterSpacing: '.02em' }}>Password</label>
              <PasswordInput
                value={password}
                onChange={e => { setPassword(e.target.value); setFormError(null) }}
                placeholder="Password kamu"
                hasError={!!errors.password}
                autoComplete="current-password"
              />
              {errors.password && <p className="text-xs mt-1" style={{ color: 'var(--unavail)' }}>{errors.password}</p>}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 text-[15px] font-extrabold text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ padding: '13px', background: 'var(--accent)', borderRadius: '10px', border: 'none', letterSpacing: '.01em' }}
              onMouseEnter={e => { if (!isLoading) (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent-h)' }}
              onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent)' }}
            >
              {isLoading ? <><Loader2 className="animate-spin" size={16} /> Memuat...</> : 'Masuk'}
            </button>
          </form>

          <p className="text-sm text-center mt-5 font-semibold" style={{ color: 'var(--text-2)' }}>
            Belum punya akun?{' '}
            <Link to="/daftar" className="font-extrabold" style={{ color: 'var(--accent)' }}>
              Daftar di sini
            </Link>
          </p>

          <p className="text-sm text-center mt-3 font-semibold" style={{ color: 'var(--text-3)' }}>
            <Link to="/katalog" className="font-extrabold" style={{ color: 'var(--text-2)' }}>
              ← Lihat katalog tanpa login
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
