// Profile siswa: edit nama, ganti password, statistik aktivitas.
import { useState, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { Loader2, User, KeyRound, BookOpen, Heart, History, Sparkles } from 'lucide-react'
import Navbar from '../components/Navbar'
import PasswordInput from '../components/PasswordInput'
import api from '../services/api'
import useAuthStore from '../store/authStore'
import type { ProfileStats, ApiResponse } from '../types'

function StatTile({ label, value, Icon, color }: { label: string; value: string | number; Icon: typeof BookOpen; color: string }) {
  return (
    <div
      className="p-4 rounded-2xl flex items-center gap-3"
      style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border)' }}
    >
      <div
        className="rounded-full flex items-center justify-center flex-shrink-0"
        style={{ width: 40, height: 40, background: 'var(--bg-subtle)', color }}
      >
        <Icon size={18} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-bold truncate" style={{ color: 'var(--text-3)' }}>{label}</p>
        <p className="text-lg font-extrabold mt-0.5 truncate" style={{ color: 'var(--text)' }}>{value}</p>
      </div>
    </div>
  )
}

function ProfilePage() {
  const user      = useAuthStore(s => s.user)
  const setLogin  = useAuthStore(s => s.login)
  const token     = useAuthStore(s => s.token)

  const [nama, setNama]                 = useState(user?.nama ?? '')
  const [isSavingNama, setIsSavingNama] = useState(false)

  const [oldPassword, setOldPassword]   = useState('')
  const [newPassword, setNewPassword]   = useState('')
  const [confirmPassword, setConfirm]   = useState('')
  const [pwError, setPwError]           = useState<string | null>(null)
  const [isChanging, setIsChanging]     = useState(false)

  const [stats, setStats]               = useState<ProfileStats | null>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)

  useEffect(() => {
    setIsLoadingStats(true)
    api.get<ApiResponse<ProfileStats>>('/users/me/stats')
      .then(res => setStats(res.data.data))
      .catch(() => setStats(null))
      .finally(() => setIsLoadingStats(false))
  }, [])

  const handleSaveNama = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = nama.trim()
    if (!trimmed || trimmed.length < 2) {
      toast.error('Nama harus minimal 2 karakter.')
      return
    }
    if (trimmed === user?.nama) {
      toast('Tidak ada perubahan.', { icon: 'ℹ️' })
      return
    }
    setIsSavingNama(true)
    try {
      await api.put('/users/me', { nama: trimmed })
      if (user && token) {
        setLogin(token, { ...user, nama: trimmed })  // sync ke authStore agar Navbar update
      }
      toast.success('Profil berhasil diperbarui.')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message ?? 'Gagal update profil.'
      toast.error(msg)
    } finally {
      setIsSavingNama(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwError(null)
    if (!oldPassword || !newPassword || !confirmPassword) {
      setPwError('Semua field wajib diisi.')
      return
    }
    if (newPassword.length < 8) {
      setPwError('Password baru minimal 8 karakter.')
      return
    }
    if (newPassword !== confirmPassword) {
      setPwError('Konfirmasi password tidak cocok.')
      return
    }
    if (oldPassword === newPassword) {
      setPwError('Password baru harus berbeda dari yang lama.')
      return
    }
    setIsChanging(true)
    try {
      await api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      toast.success('Password berhasil diganti.')
      setOldPassword('')
      setNewPassword('')
      setConfirm('')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message ?? 'Gagal ganti password.'
      setPwError(msg)
    } finally {
      setIsChanging(false)
    }
  }

  const initials = user?.nama
    ? user.nama.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()
    : 'U'

  return (
    <>
      <Navbar />
      <div className="pt-[60px]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <div
              className="rounded-full flex items-center justify-center text-2xl font-extrabold text-white flex-shrink-0"
              style={{ width: 72, height: 72, background: 'linear-gradient(135deg, var(--accent) 0%, var(--brand) 100%)' }}
            >
              {initials}
            </div>
            <div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 800, color: 'var(--text)' }}>
                {user?.nama ?? 'Pengguna'}
              </h1>
              <p className="text-sm font-semibold" style={{ color: 'var(--text-3)' }}>@{user?.username}</p>
            </div>
          </div>

          {/* Statistik */}
          <h2 className="text-base font-extrabold mb-3" style={{ color: 'var(--text)' }}>
            Aktivitas Saya
          </h2>
          {isLoadingStats ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-20 rounded-2xl animate-pulse" style={{ background: 'var(--bg-subtle)' }} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <StatTile label="Total Pinjam"      value={stats?.total_pinjam ?? 0}   Icon={BookOpen} color="var(--accent)" />
              <StatTile label="Sedang Aktif"      value={stats?.total_active ?? 0}   Icon={History}  color="#2563eb" />
              <StatTile label="Sudah Dikembalikan" value={stats?.total_returned ?? 0} Icon={Sparkles} color="var(--avail)" />
              <StatTile label="Buku Favorit"      value={stats?.total_favorit ?? 0}  Icon={Heart}    color="#dc2626" />
            </div>
          )}
          {stats?.top_kategori && (
            <p className="text-sm font-semibold mb-8" style={{ color: 'var(--text-2)' }}>
              📚 Kategori favoritmu: <strong style={{ color: 'var(--accent)' }}>{stats.top_kategori}</strong>
            </p>
          )}

          {/* Edit nama */}
          <div
            className="p-6 rounded-2xl mb-6"
            style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border)' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <User size={18} style={{ color: 'var(--accent)' }} />
              <h2 className="text-base font-extrabold" style={{ color: 'var(--text)' }}>Edit Nama</h2>
            </div>
            <form onSubmit={handleSaveNama}>
              <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)' }}>Nama Lengkap</label>
              <input
                type="text"
                value={nama}
                onChange={e => setNama(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  border: '1.5px solid var(--border)',
                  borderRadius: '10px',
                  background: 'var(--bg-input)',
                  color: 'var(--text)',
                  fontSize: '14px',
                  fontWeight: 500,
                  outline: 'none',
                }}
              />
              <button
                type="submit"
                disabled={isSavingNama}
                className="mt-4 px-5 py-2 rounded-full text-sm font-extrabold text-white flex items-center gap-2 disabled:opacity-50"
                style={{ background: 'var(--accent)' }}
              >
                {isSavingNama ? <><Loader2 size={14} className="animate-spin" /> Menyimpan...</> : 'Simpan Nama'}
              </button>
            </form>
          </div>

          {/* Ganti password */}
          <div
            className="p-6 rounded-2xl"
            style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border)' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <KeyRound size={18} style={{ color: 'var(--accent)' }} />
              <h2 className="text-base font-extrabold" style={{ color: 'var(--text)' }}>Ganti Password</h2>
            </div>

            {pwError && (
              <div
                role="alert"
                className="mb-4 px-3 py-2.5 rounded-lg text-sm font-semibold"
                style={{ background: 'var(--unavail-bg)', color: 'var(--unavail)', border: '1.5px solid var(--unavail)' }}
              >
                {pwError}
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)' }}>Password Lama</label>
                <PasswordInput value={oldPassword} onChange={e => { setOldPassword(e.target.value); setPwError(null) }} placeholder="Password lama" autoComplete="current-password" />
              </div>
              <div>
                <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)' }}>Password Baru</label>
                <PasswordInput value={newPassword} onChange={e => { setNewPassword(e.target.value); setPwError(null) }} placeholder="Minimal 8 karakter" autoComplete="new-password" />
              </div>
              <div>
                <label className="block text-[13px] font-extrabold mb-1.5" style={{ color: 'var(--text-2)' }}>Konfirmasi Password Baru</label>
                <PasswordInput value={confirmPassword} onChange={e => { setConfirm(e.target.value); setPwError(null) }} placeholder="Ulangi password baru" autoComplete="new-password" />
              </div>
              <button
                type="submit"
                disabled={isChanging}
                className="px-5 py-2 rounded-full text-sm font-extrabold text-white flex items-center gap-2 disabled:opacity-50"
                style={{ background: 'var(--accent)' }}
              >
                {isChanging ? <><Loader2 size={14} className="animate-spin" /> Mengubah...</> : 'Ganti Password'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  )
}

export default ProfilePage
