// Dashboard admin: stat cards + top books + overdue alerts + logo upload.
import { useState, useEffect, useMemo } from 'react'
import { BookOpen, BookMarked, Clock, Users, AlertTriangle, TrendingUp, Loader2 } from 'lucide-react'
import { toast } from 'react-hot-toast'
import AdminSidebar from '../../components/AdminSidebar'
import StatCard from '../../components/StatCard'
import api from '../../services/api'
import type { DashboardStats, LogoSettings, ApiResponse, TopBook, OverdueBorrow } from '../../types'

function TopBooksSection({ books }: { books: TopBook[] }) {
  const max = useMemo(() => Math.max(1, ...books.map(b => b.borrow_count)), [books])

  if (books.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-gray-500">
        Belum ada data peminjaman.
      </div>
    )
  }

  return (
    <ol className="space-y-3">
      {books.map((b, idx) => {
        const width = (b.borrow_count / max) * 100
        return (
          <li key={b.id} className="flex items-center gap-3">
            <span className="w-6 text-sm font-bold text-gray-400 flex-shrink-0">#{idx + 1}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-sm font-semibold text-gray-900 truncate">{b.judul}</p>
                <span className="text-xs font-bold text-indigo-600 flex-shrink-0">
                  {b.borrow_count}×
                </span>
              </div>
              <p className="text-xs text-gray-500 truncate mb-1">{b.penulis}</p>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function OverdueSection({ items }: { items: OverdueBorrow[] }) {
  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-gray-500">
        Tidak ada pinjaman yang telat.
      </div>
    )
  }

  return (
    <ul className="space-y-2">
      {items.map(item => (
        <li
          key={item.id}
          className="flex items-center justify-between gap-3 p-3 rounded-lg bg-red-50 border border-red-200"
        >
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900 truncate">{item.judul}</p>
            <p className="text-xs text-gray-600 truncate">Dipinjam oleh {item.user_nama}</p>
          </div>
          <span className="text-xs font-extrabold text-red-700 bg-red-100 px-2.5 py-1 rounded-full whitespace-nowrap">
            Telat {item.days_overdue} hari
          </span>
        </li>
      ))}
    </ul>
  )
}

function AdminDashboardPage() {
  const [stats, setStats]                   = useState<DashboardStats | null>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [logoUrl, setLogoUrl]               = useState<string | null>(null)
  const [logoFile, setLogoFile]             = useState<File | null>(null)
  const [isUploading, setIsUploading]       = useState(false)
  const [logoPreview, setLogoPreview]       = useState<string | null>(null)

  useEffect(() => {
    setIsLoadingStats(true)
    api.get<ApiResponse<DashboardStats>>('/admin/dashboard')
      .then(res => setStats(res.data.data))
      .catch(() => setStats(null))
      .finally(() => setIsLoadingStats(false))
  }, [])

  useEffect(() => {
    api.get<ApiResponse<LogoSettings>>('/settings/logo')
      .then(res => setLogoUrl(res.data.data.logo_url))
      .catch(() => {})
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setLogoFile(file)
    if (file) {
      const reader = new FileReader()
      reader.onload = (ev) => setLogoPreview(ev.target?.result as string)
      reader.readAsDataURL(file)
    } else {
      setLogoPreview(null)
    }
  }

  const handleLogoUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!logoFile) {
      toast.error('Pilih file logo terlebih dahulu.')
      return
    }
    const formData = new FormData()
    formData.append('logo', logoFile)
    setIsUploading(true)
    try {
      const res = await api.post<ApiResponse<LogoSettings>>('/admin/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setLogoUrl(res.data.data.logo_url)
      setLogoFile(null)
      setLogoPreview(null)
      toast.success('Logo berhasil diperbarui.')
    } catch {
      toast.error('Gagal mengupload logo. Pastikan file PNG/JPG tidak melebihi ukuran yang diizinkan.')
    } finally {
      setIsUploading(false)
    }
  }

  const overdueCount = stats?.overdue?.length ?? 0

  return (
    <div className="flex">
      <AdminSidebar />
      <main className="ml-0 md:ml-64 pt-14 md:pt-0 flex-1 min-w-0 min-h-screen bg-gray-50">
        <div className="px-4 md:px-8 py-6 md:py-8">
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Ringkasan aktivitas perpustakaan</p>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
            {isLoadingStats ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 animate-pulse h-24" />
              ))
            ) : (
              <>
                <StatCard
                  label="Total Buku"
                  value={stats?.total_buku ?? 0}
                  icon={<BookOpen size={24} className="text-indigo-600" />}
                />
                <StatCard
                  label="Pinjaman Aktif"
                  value={stats?.pinjaman_aktif ?? 0}
                  icon={<BookMarked size={24} className="text-blue-600" />}
                />
                <StatCard
                  label="Pending Request"
                  value={stats?.pending_count ?? 0}
                  icon={<Clock size={24} className="text-yellow-600" />}
                />
                <StatCard
                  label="Siswa Terdaftar"
                  value={stats?.total_siswa ?? 0}
                  icon={<Users size={24} className="text-emerald-600" />}
                />
              </>
            )}
          </div>

          {overdueCount > 0 && !isLoadingStats && (
            <div className="mt-6 flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200">
              <AlertTriangle size={22} className="text-red-600 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-bold text-red-900">
                  {overdueCount} pinjaman terlambat dikembalikan
                </p>
                <p className="text-xs text-red-700 mt-0.5">
                  Hubungi siswa untuk mengingatkan pengembalian buku.
                </p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={18} className="text-indigo-600" />
                <h2 className="text-lg font-semibold text-gray-900">Top 5 Buku Populer</h2>
              </div>
              {isLoadingStats ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : (
                <TopBooksSection books={stats?.top_books ?? []} />
              )}
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={18} className="text-red-600" />
                  <h2 className="text-lg font-semibold text-gray-900">Pinjaman Telat</h2>
                </div>
                {overdueCount > 0 && (
                  <span className="text-xs font-bold text-red-700 bg-red-100 px-2 py-0.5 rounded-full">
                    {overdueCount}
                  </span>
                )}
              </div>
              {isLoadingStats ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-14 bg-gray-100 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : (
                <OverdueSection items={stats?.overdue ?? []} />
              )}
            </div>
          </div>

          <div className="mt-6 bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Logo Sistem</h2>
            <p className="text-sm text-gray-500 mt-1">
              Upload logo PNG atau JPG. Logo akan tampil di sidebar dan halaman siswa.
            </p>

            <div className="mt-4 flex flex-col sm:flex-row items-start gap-4 sm:gap-6">
              <div className="w-32 h-32 border border-gray-200 rounded-lg bg-gray-50 flex items-center justify-center overflow-hidden flex-shrink-0">
                {logoPreview ? (
                  <img src={logoPreview} alt="Preview logo" className="w-full h-full object-contain" />
                ) : logoUrl ? (
                  <img src={logoUrl} alt="Logo saat ini" className="w-full h-full object-contain" />
                ) : (
                  <span className="text-indigo-600 font-bold text-xl">LIBRA</span>
                )}
              </div>

              <form onSubmit={handleLogoUpload} className="flex-1 min-w-0 w-full">
                <input
                  type="file"
                  accept="image/png,image/jpeg"
                  onChange={handleFileChange}
                  className="block w-full max-w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                />
                <button
                  type="submit"
                  disabled={isUploading || !logoFile}
                  className="mt-3 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
                >
                  {isUploading ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Mengunggah...
                    </>
                  ) : (
                    'Simpan Logo'
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default AdminDashboardPage
