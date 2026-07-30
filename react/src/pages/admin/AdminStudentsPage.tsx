// Kelola Siswa — daftar siswa terdaftar beserta ringkasan aktivitas peminjaman,
// dan panel rincian berisi seluruh riwayat pinjam satu siswa.
//
// Sebelumnya petugas tidak punya cara melihat siapa saja yang terdaftar maupun
// menelusuri riwayat per siswa; halaman Kelola Pinjaman hanya menampilkan
// transaksi, bukan orangnya.
import { useState, useEffect, useCallback } from 'react'
import { Users, Search, X, ChevronRight, AlertTriangle } from 'lucide-react'
import { toast } from 'react-hot-toast'
import AdminSidebar from '../../components/AdminSidebar'
import Pagination from '../../components/Pagination'
import useDebounce from '../../hooks/useDebounce'
import api from '../../services/api'
import type { ApiResponse } from '../../types'

interface Siswa {
  id: number
  nama: string
  username: string
  created_at: string
  total_pinjam: number
  pinjaman_aktif: number
  terlambat: number
  terakhir_pinjam: string | null
}

interface RiwayatItem {
  id: number
  status: 'Pending' | 'Dipinjam' | 'Dikembalikan' | 'Ditolak'
  tanggal_pinjam: string
  tanggal_approve: string | null
  tanggal_kembali: string | null
  buku_id: number
  judul: string
  penulis: string
  kategori_nama: string
  hari_terlambat: number | null
}

interface DetailSiswa {
  siswa: Siswa
  ringkasan: { total: number; aktif: number; dikembalikan: number; ditolak: number; terlambat: number }
  riwayat: RiwayatItem[]
}

const WARNA_STATUS: Record<string, string> = {
  Pending:      'bg-amber-100 text-amber-700',
  Dipinjam:     'bg-blue-100 text-blue-700',
  Dikembalikan: 'bg-green-100 text-green-700',
  Ditolak:      'bg-red-100 text-red-700',
}

const tanggal = (s: string | null) =>
  s ? new Date(s).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'

function AdminStudentsPage() {
  const [siswa, setSiswa]         = useState<Siswa[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage]           = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal]         = useState(0)
  const [cari, setCari]           = useState('')
  const search = useDebounce(cari, 400)

  const [detail, setDetail]           = useState<DetailSiswa | null>(null)
  const [isLoadingDetail, setLoadingDetail] = useState(false)

  // Konfirmasi hapus memakai ketik-ulang nama, bukan confirm() biasa.
  // Menghapus akun siswa juga menghapus seluruh riwayat peminjamannya dan tidak
  // dapat dibatalkan, sehingga perlu tindakan sadar — bukan sekadar satu klik.
  const [targetHapus, setTargetHapus] = useState<Siswa | null>(null)
  const [ketikNama, setKetikNama]     = useState('')
  const [isMenghapus, setMenghapus]   = useState(false)

  const bukaHapus = (s: Siswa) => { setTargetHapus(s); setKetikNama('') }
  const tutupHapus = () => { setTargetHapus(null); setKetikNama('') }

  const konfirmasiHapus = async () => {
    if (!targetHapus || ketikNama.trim() !== targetHapus.nama) return
    setMenghapus(true)
    try {
      const res = await api.delete<ApiResponse<{ nama: string; riwayat_terhapus: number }>>(
        `/admin/students/${targetHapus.id}`
      )
      const { nama, riwayat_terhapus } = res.data.data
      toast.success(
        riwayat_terhapus > 0
          ? `Akun "${nama}" dihapus beserta ${riwayat_terhapus} riwayat peminjaman.`
          : `Akun "${nama}" berhasil dihapus.`
      )
      tutupHapus()
      fetchSiswa()
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string } } }
      toast.error(e?.response?.data?.message ?? 'Gagal menghapus akun siswa.')
    } finally {
      setMenghapus(false)
    }
  }

  const fetchSiswa = useCallback(() => {
    setIsLoading(true)
    const params: Record<string, string | number> = { page, limit: 20 }
    if (search) params.q = search
    api.get<ApiResponse<{ items: Siswa[]; total: number; total_pages: number }>>('/admin/students', { params })
      .then(res => {
        setSiswa(res.data.data.items)
        setTotal(res.data.data.total)
        setTotalPages(res.data.data.total_pages)
      })
      .catch(() => { setSiswa([]); toast.error('Gagal memuat data siswa.') })
      .finally(() => setIsLoading(false))
  }, [page, search])

  useEffect(() => { fetchSiswa() }, [fetchSiswa])
  useEffect(() => { setPage(1) }, [search])

  const bukaDetail = async (id: number) => {
    setLoadingDetail(true)
    setDetail(null)
    try {
      const res = await api.get<ApiResponse<DetailSiswa>>(`/admin/students/${id}`)
      setDetail(res.data.data)
    } catch {
      toast.error('Gagal memuat riwayat siswa.')
    } finally {
      setLoadingDetail(false)
    }
  }

  return (
    <div className="flex">
      <AdminSidebar />
      <main className="ml-0 md:ml-64 pt-14 md:pt-0 flex-1 min-w-0 min-h-screen bg-gray-50">
        <div className="px-4 md:px-8 py-6 md:py-8">
          <h1 className="text-2xl font-semibold text-gray-900">Kelola Siswa</h1>
          <p className="text-sm text-gray-500 mt-1">
            Daftar siswa terdaftar beserta aktivitas peminjamannya.
          </p>

          {/* Pencarian */}
          <div className="mt-6 relative max-w-md">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={cari}
              onChange={e => setCari(e.target.value)}
              placeholder="Cari nama atau username siswa..."
              className="w-full pl-9 pr-9 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
            {cari && (
              <button
                onClick={() => setCari('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Hapus pencarian"
              >
                <X size={15} />
              </button>
            )}
          </div>

          {!isLoading && (
            <p className="mt-3 text-sm text-gray-500">
              {search
                ? <>Menampilkan <span className="font-semibold text-gray-700">{total}</span> siswa hasil pencarian.</>
                : <>Total <span className="font-semibold text-gray-700">{total}</span> siswa terdaftar.</>}
            </p>
          )}

          {/* Tabel siswa */}
          <div className="mt-4 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {isLoading ? (
              <div className="py-16 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : siswa.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Users size={48} className="text-gray-300" />
                <h3 className="text-lg font-semibold text-gray-500 mt-4">
                  {search ? 'Tidak ada siswa yang cocok' : 'Belum ada siswa terdaftar'}
                </h3>
                <p className="text-sm text-gray-400 mt-2">
                  {search ? 'Coba kata kunci lain.' : 'Akun siswa ditambahkan oleh pengelola sistem.'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px]">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Nama</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Username</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500">Total Pinjam</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500">Aktif</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Terakhir Pinjam</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">Riwayat</th>
                    </tr>
                  </thead>
                  <tbody>
                    {siswa.map(s => (
                      <tr key={s.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-gray-900">{s.nama}</span>
                            {s.terlambat > 0 && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                                <AlertTriangle size={11} />
                                {s.terlambat} telat
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">{s.username}</td>
                        <td className="px-4 py-3 text-center text-sm font-semibold text-gray-900">{s.total_pinjam}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-sm font-semibold ${s.pinjaman_aktif > 0 ? 'text-blue-600' : 'text-gray-400'}`}>
                            {s.pinjaman_aktif}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">{tanggal(s.terakhir_pinjam)}</td>
                        <td className="px-4 py-3">
                          <div className="flex gap-2 justify-end">
                            <button
                              onClick={() => bukaDetail(s.id)}
                              className="inline-flex items-center gap-1 px-3 py-2 text-xs font-semibold text-indigo-600 border border-indigo-300 rounded-md hover:bg-indigo-50 transition-colors"
                            >
                              Lihat
                              <ChevronRight size={13} />
                            </button>
                            <button
                              onClick={() => bukaHapus(s)}
                              disabled={s.pinjaman_aktif > 0}
                              title={s.pinjaman_aktif > 0
                                ? 'Tidak dapat dihapus: siswa masih memiliki peminjaman aktif'
                                : 'Hapus akun siswa'}
                              className="px-3 py-2 text-xs font-semibold text-red-600 border border-red-300 rounded-md hover:bg-red-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                            >
                              Hapus
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {!isLoading && totalPages > 1 && (
            <div className="mt-6">
              <Pagination currentPage={page} totalPages={totalPages} onPageChange={p => { setPage(p); window.scrollTo(0, 0) }} />
            </div>
          )}
        </div>
      </main>

      {/* Konfirmasi hapus akun */}
      {targetHapus && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,.5)' }}
          onClick={tutupHapus}
        >
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-5">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle size={20} className="text-red-600" />
                </div>
                <div className="min-w-0">
                  <h2 className="text-lg font-semibold text-gray-900">Hapus akun siswa?</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Akun <span className="font-semibold">{targetHapus.nama}</span> ({targetHapus.username})
                    akan dihapus permanen.
                  </p>
                </div>
              </div>

              <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-100">
                <p className="text-sm text-red-800 font-semibold">Yang ikut terhapus:</p>
                <ul className="text-sm text-red-700 mt-1 space-y-0.5">
                  <li>· {targetHapus.total_pinjam} riwayat peminjaman</li>
                  <li>· Seluruh buku favorit dan notifikasinya</li>
                </ul>
                <p className="text-xs text-red-600 mt-2">Tindakan ini tidak dapat dibatalkan.</p>
              </div>

              <label className="block mt-4 text-sm text-gray-700">
                Ketik <span className="font-semibold">{targetHapus.nama}</span> untuk mengonfirmasi:
              </label>
              <input
                type="text"
                value={ketikNama}
                onChange={e => setKetikNama(e.target.value)}
                autoFocus
                className="mt-1.5 w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
              />
            </div>

            <div className="px-6 py-4 bg-gray-50 rounded-b-xl flex justify-end gap-2">
              <button
                onClick={tutupHapus}
                className="px-4 py-2 text-sm font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={konfirmasiHapus}
                disabled={ketikNama.trim() !== targetHapus.nama || isMenghapus}
                className="px-4 py-2 text-sm font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isMenghapus ? 'Menghapus...' : 'Hapus permanen'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Panel rincian riwayat */}
      {(detail || isLoadingDetail) && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,.45)' }}
          onClick={() => { setDetail(null); setLoadingDetail(false) }}
        >
          <div
            className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col"
            onClick={e => e.stopPropagation()}
          >
            {isLoadingDetail || !detail ? (
              <div className="py-20 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <>
                <div className="px-6 py-4 border-b border-gray-200 flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">{detail.siswa.nama}</h2>
                    <p className="text-sm text-gray-500">
                      {detail.siswa.username} · terdaftar {tanggal(detail.siswa.created_at)}
                    </p>
                  </div>
                  <button onClick={() => setDetail(null)} className="text-gray-400 hover:text-gray-600" aria-label="Tutup">
                    <X size={20} />
                  </button>
                </div>

                {/* Ringkasan */}
                <div className="px-6 py-4 grid grid-cols-2 sm:grid-cols-5 gap-3 border-b border-gray-200">
                  {[
                    ['Total', detail.ringkasan.total, 'text-gray-900'],
                    ['Aktif', detail.ringkasan.aktif, 'text-blue-600'],
                    ['Dikembalikan', detail.ringkasan.dikembalikan, 'text-green-600'],
                    ['Ditolak', detail.ringkasan.ditolak, 'text-red-600'],
                    ['Terlambat', detail.ringkasan.terlambat, 'text-amber-600'],
                  ].map(([label, nilai, warna]) => (
                    <div key={label as string} className="text-center">
                      <p className={`text-xl font-bold ${warna}`}>{nilai as number}</p>
                      <p className="text-[11px] text-gray-500 uppercase tracking-wide">{label as string}</p>
                    </div>
                  ))}
                </div>

                {/* Riwayat */}
                <div className="overflow-y-auto flex-1 px-6 py-4">
                  {detail.riwayat.length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-10">
                      Siswa ini belum pernah meminjam buku.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {detail.riwayat.map(r => (
                        <div key={r.id} className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900 truncate">{r.judul}</p>
                            <p className="text-xs text-gray-500 truncate">{r.penulis} · {r.kategori_nama}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              Diajukan {tanggal(r.tanggal_pinjam)}
                              {r.tanggal_kembali && ` · dikembalikan ${tanggal(r.tanggal_kembali)}`}
                            </p>
                          </div>
                          <div className="flex flex-col items-end gap-1 flex-shrink-0">
                            <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${WARNA_STATUS[r.status]}`}>
                              {r.status}
                            </span>
                            {r.hari_terlambat !== null && r.hari_terlambat > 0 && (
                              <span className="text-[11px] font-bold text-red-600">
                                telat {r.hari_terlambat} hari
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminStudentsPage
