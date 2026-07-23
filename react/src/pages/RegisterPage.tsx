import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router'
import { toast } from 'react-hot-toast'
import { Loader2 } from 'lucide-react'
import api from '../services/api'
import useAuthStore from '../store/authStore'
import PasswordInput from '../components/PasswordInput'

const inputBase: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  border: '1.5px solid var(--border)',
  borderRadius: '10px',
  background: 'var(--bg-input)',
  color: 'var(--text)',
  fontFamily: 'var(--font-ui)',
  fontSize: '14px',
  fontWeight: 500,
  outline: 'none',
  transition: 'border-color var(--transition), box-shadow var(--transition)',
}

function FormInput({
  type, value, onChange, placeholder, hasError,
}: { type: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; placeholder: string; hasError: boolean }) {
  const [focused, setFocused] = useState(false)
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={{
        ...inputBase,
        borderColor: hasError ? 'var(--unavail)' : focused ? 'var(--accent)' : 'var(--border)',
        boxShadow: focused && !hasError ? '0 0 0 3px rgba(217,119,6,.15)' : 'none',
      }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    />
  )
}

function RegisterPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((state) => state.login)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  const [nama, setNama] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<{ nama?: string; username?: string; password?: string }>({})
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated) navigate('/katalog', { replace: true })
  }, [isAuthenticated, navigate])

  const validate = (): boolean => {
    const newErrors: { nama?: string; username?: string; password?: string } = {}
    if (!nama.trim()) newErrors.nama = 'Kolom ini wajib diisi'
    if (!username.trim()) newErrors.username = 'Kolom ini wajib diisi'
    else if (!/^[a-zA-Z0-9._]{3,30}$/.test(username)) newErrors.username = '3-30 karakter: huruf, angka, titik, garis bawah'
    if (!password) newErrors.password = 'Kolom ini wajib diisi'
    else if (password.length < 8) newErrors.password = 'Password minimal 8 karakter'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setIsLoading(true)
    try {
      await api.post('/auth/register', { nama, username, password })
      try {
        const loginRes = await api.post('/auth/login', { username, password })
        const { token, user } = loginRes.data.data
        login(token, user)
        const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/katalog'
        navigate(from, { replace: true })
      } catch {
        toast.error('Akun dibuat, silakan login manual.')
        navigate('/login')
      }
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Pendaftaran gagal. Coba lagi.'
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden" style={{ background: 'var(--bg)' }}>
      <div
        className="absolute pointer-events-none"
        style={{ width: 360, height: 360, borderRadius: '50%', background: 'radial-gradient(circle, rgba(217,119,6,.18) 0%, transparent 70%)', filter: 'blur(80px)', top: -100, right: -80 }}
      />
      <div
        className="absolute pointer-events-none"
        style={{ width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(30,77,107,.15) 0%, transparent 70%)', filter: 'blur(80px)', bottom: -60, left: -40 }}
      />

      <div
        className="relative z-10 w-full max-w-[400px]"
        style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border)', borderRadius: '24px', padding: '36px 32px', boxShadow: 'var(--shadow-lg)' }}
      >
        <div className="text-center mb-6">
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '40px', fontWeight: 800, color: 'var(--accent)', display: 'block', lineHeight: 1 }}>
            LIBRA
          </span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-3)', marginTop: 4, display: 'block' }}>
            Perpustakaan Digital SMPN 1 Kemang
          </span>
        </div>

        <p className="text-center text-[15px] font-bold mb-6" style={{ color: 'var(--text)' }}>Buat akun baru ✨</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)' }}>Nama Lengkap</label>
            <FormInput type="text" value={nama} onChange={e => setNama(e.target.value)} placeholder="Nama kamu" hasError={!!errors.nama} />
            {errors.nama && <p className="text-xs mt-1" style={{ color: 'var(--unavail)' }}>{errors.nama}</p>}
          </div>

          <div className="mb-4">
            <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)' }}>Username</label>
            <FormInput type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="cth: luthfi1" hasError={!!errors.username} />
            {errors.username && <p className="text-xs mt-1" style={{ color: 'var(--unavail)' }}>{errors.username}</p>}
          </div>

          <div className="mb-6">
            <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)' }}>Password</label>
            <PasswordInput
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Minimal 8 karakter"
              hasError={!!errors.password}
              autoComplete="new-password"
            />
            {errors.password && <p className="text-xs mt-1" style={{ color: 'var(--unavail)' }}>{errors.password}</p>}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 text-[15px] font-extrabold text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ padding: '13px', background: 'var(--accent)', borderRadius: '10px', border: 'none' }}
            onMouseEnter={e => { if (!isLoading) (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent-h)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent)' }}
          >
            {isLoading ? <><Loader2 className="animate-spin" size={16} /> Memuat...</> : 'Daftar'}
          </button>
        </form>

        <p className="text-sm text-center mt-5 font-semibold" style={{ color: 'var(--text-2)' }}>
          Sudah punya akun?{' '}
          <Link to="/login" className="font-extrabold" style={{ color: 'var(--accent)' }}>
            Masuk di sini
          </Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
