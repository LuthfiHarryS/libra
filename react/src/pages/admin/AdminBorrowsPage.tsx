// Kelola pinjaman: filter status + tanggal, bulk approve/reject, CSV export.
import { useState, useEffect, useCallback, useMemo } from 'react'
import { toast } from 'react-hot-toast'
import { X, Download, Check, Ban, Square, CheckSquare } from 'lucide-react'
import AdminSidebar from '../../components/AdminSidebar'
import api from '../../services/api'
import type { AdminBorrowItem, ApiResponse } from '../../types'

const STATUS_CHIP: Record<AdminBorrowItem['status'], string> = {
  'Pending':      'bg-yellow-100 text-yellow-700',
  'Dipinjam':     'bg-blue-100 text-blue-700',
  'Dikembalikan': 'bg-green-100 text-green-700',
  'Ditolak':      'bg-red-100 text-red-700',
}

type FilterTab = 'Semua' | AdminBorrowItem['status']
const FILTER_TABS: FilterTab[] = ['Semua', 'Pending', 'Dipinjam', 'Dikembalikan', 'Ditolak']

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Belum dikembalikan'
  try {
    const date = new Date(dateStr.replace(' ', 'T'))
    return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return 'Belum dikembalikan'
  }
}

function isoDate(mysql: string): string {
  return mysql.slice(0, 10)
}

type BorrowAction = 'approve' | 'reject' | 'return'
type BulkResponse = {
  success_count: number
  success_ids: number[]
  failed: { id: number | string; reason: string }[]
}

function AdminBorrowsPage() {
  const [borrows, setBorrows]             = useState<AdminBorrowItem[]>([])
  const [isLoading, setIsLoading]         = useState(true)
  const [activeFilter, setActiveFilter]   = useState<FilterTab>('Semua')
  const [dateFrom, setDateFrom]           = useState('')
  const [dateTo, setDateTo]               = useState('')
  const [actionLoading, setActionLoading] = useState<Record<number, boolean>>({})
  const [selectedIds, setSelectedIds]     = useState<Set<number>>(new Set())
  const [isBulkLoading, setIsBulkLoading] = useState(false)
  const [isExporting, setIsExporting]     = useState(false)

  const fetchBorrows = useCallback(() => {
    setIsLoading(true)
    api.get<ApiResponse<AdminBorrowItem[]>>('/admin/borrows')
      .then(res => setBorrows(res.data.data))
      .catch(() => setBorrows([]))
      .finally(() => setIsLoading(false))
  }, [])

  useEffect(() => { fetchBorrows() }, [fetchBorrows])

  const filtered = useMemo(() => borrows.filter(b => {
    if (activeFilter !== 'Semua' && b.status !== activeFilter) return false
    const d = isoDate(b.tanggal_pinjam)
    if (dateFrom && d < dateFrom) return false
    if (dateTo && d > dateTo)     return false
    return true
  }), [borrows, activeFilter, dateFrom, dateTo])

  // Hanya Pending yang bisa dipilih untuk bulk action
  const selectablePending = useMemo(() => filtered.filter(b => b.status === 'Pending'), [filtered])
  const allPendingSelected = selectablePending.length > 0
    && selectablePending.every(b => selectedIds.has(b.id))

  // Reset selection saat filter berubah (id mungkin di-filter out)
  useEffect(() => {
    setSelectedIds(prev => {
      const stillVisible = new Set<number>()
      const filteredIds = new Set(filtered.map(b => b.id))
      prev.forEach(id => { if (filteredIds.has(id)) stillVisible.add(id) })
      return stillVisible
    })
  }, [filtered])

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAllPending = () => {
    if (allPendingSelected) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(selectablePending.map(b => b.id)))
    }
  }

  const hasDateFilter = dateFrom !== '' || dateTo !== ''
  const clearDateFilter = () => { setDateFrom(''); setDateTo('') }

  const handleAction = async (id: number, action: BorrowAction) => {
    setActionLoading(prev => ({ ...prev, [id]: true }))
    try {
      await api.put(`/admin/borrow/${id}/${action}`)
      toast.success(
        action === 'approve' ? 'Peminjaman berhasil disetujui.' :
        action === 'reject'  ? 'Peminjaman berhasil ditolak.'   :
                               'Pengembalian berhasil dicatat.'
      )
      fetchBorrows()
    } catch {
      toast.error(
        action === 'approve' ? 'Gagal menyetujui peminjaman. Coba lagi.' :
        action === 'reject'  ? 'Gagal menolak peminjaman. Coba lagi.'    :
                               'Gagal mencatat pengembalian. Coba lagi.'
      )
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }))
    }
  }

  const handleBulk = async (action: 'approve' | 'reject') => {
    const ids = Array.from(selectedIds)
    if (ids.length === 0) return

    const verb = action === 'approve' ? 'setujui' : 'tolak'
    if (!window.confirm(`${ids.length} pinjaman akan di${verb}. Lanjutkan?`)) return

    setIsBulkLoading(true)
    try {
      const res = await api.post<ApiResponse<BulkResponse>>(`/admin/borrows/bulk-${action}`, { ids })
      const { success_count, failed } = res.data.data
      if (failed.length === 0) {
        toast.success(`${success_count} pinjaman berhasil di${verb}.`)
      } else {
        toast(`${success_count} berhasil, ${failed.length} gagal. Cek konsol untuk detail.`, { icon: '⚠️' })
        console.warn('Bulk action failed items:', failed)
      }
      setSelectedIds(new Set())
      fetchBorrows()
    } catch {
      toast.error(`Gagal menjalankan bulk ${verb}.`)
    } finally {
      setIsBulkLoading(false)
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const params: Record<string, string> = {}
      if (activeFilter !== 'Semua') params.status = activeFilter
      if (dateFrom) params.from = dateFrom
      if (dateTo)   params.to   = dateTo

      const res = await api.get('/admin/borrows/export', { params, responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv;charset=utf-8' }))
      const a = document.createElement('a')
      const ts = new Date().toISOString().slice(0, 10)
      a.href = url
      a.download = `pinjaman_${ts}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      toast.success('Laporan CSV berhasil diunduh.')
    } catch {
      toast.error('Gagal mengunduh laporan.')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="flex">
      <AdminSidebar />
      <main className="ml-0 md:ml-64 pt-14 md:pt-0 flex-1 min-w-0 min-h-screen bg-gray-50">
        <div className="px-4 md:px-8 py-6 md:py-8">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h1 className="text-2xl font-semibold text-gray-900">Kelola Pinjaman</h1>
            <button
              onClick={handleExport}
              disabled={isExporting || filtered.length === 0}
              className="px-4 py-2 text-sm font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              title="Unduh laporan CSV sesuai filter aktif"
            >
              <Download size={14} />
              {isExporting ? 'Mengunduh...' : 'Export CSV'}
            </button>
          </div>

          <div className="flex gap-2 flex-wrap mt-4">
            {FILTER_TABS.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveFilter(tab)}
                className={`px-3 py-2 rounded-full text-sm font-semibold border transition-colors duration-150 ${
                  activeFilter === tab
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="flex items-end gap-3 flex-wrap mt-4 p-4 bg-white rounded-xl border border-gray-200">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Tanggal pinjam dari</label>
              <input
                type="date"
                value={dateFrom}
                max={dateTo || undefined}
                onChange={e => setDateFrom(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Sampai</label>
              <input
                type="date"
                value={dateTo}
                min={dateFrom || undefined}
                onChange={e => setDateTo(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            {hasDateFilter && (
              <button
                onClick={clearDateFilter}
                className="px-3 py-2 text-sm font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg flex items-center gap-1.5 transition-colors"
              >
                <X size={14} />
                Reset
              </button>
            )}
            <p className="text-xs text-gray-500 ml-auto">
              Menampilkan <strong className="text-gray-900">{filtered.length}</strong> dari {borrows.length} pinjaman
            </p>
          </div>

          {selectedIds.size > 0 && (
            <div className="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center gap-3 flex-wrap">
              <p className="text-sm font-bold text-indigo-900">
                {selectedIds.size} pinjaman dipilih
              </p>
              <div className="flex gap-2 ml-auto">
                <button
                  onClick={() => handleBulk('approve')}
                  disabled={isBulkLoading}
                  className="px-3 py-2 text-xs font-semibold bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Check size={14} />
                  Setujui Semua
                </button>
                <button
                  onClick={() => handleBulk('reject')}
                  disabled={isBulkLoading}
                  className="px-3 py-2 text-xs font-semibold bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Ban size={14} />
                  Tolak Semua
                </button>
                <button
                  onClick={() => setSelectedIds(new Set())}
                  disabled={isBulkLoading}
                  className="px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                >
                  Batal
                </button>
              </div>
            </div>
          )}

          <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {isLoading ? (
              <div className="py-16 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-16 flex flex-col items-center justify-center text-center">
                {activeFilter === 'Semua' ? (
                  <>
                    <p className="text-lg font-semibold text-gray-500">Belum ada pinjaman</p>
                    <p className="text-sm text-gray-400 mt-2">Belum ada request peminjaman dari siswa.</p>
                  </>
                ) : (
                  <>
                    <p className="text-lg font-semibold text-gray-500">Tidak ada data</p>
                    <p className="text-sm text-gray-400 mt-2">Tidak ada pinjaman dengan status {activeFilter}.</p>
                  </>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[850px]">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-4 py-3 w-10">
                        {selectablePending.length > 0 && (
                          <button
                            onClick={toggleSelectAllPending}
                            aria-label={allPendingSelected ? 'Batalkan pilih semua Pending' : 'Pilih semua Pending'}
                            className="text-indigo-600 hover:text-indigo-700"
                          >
                            {allPendingSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                          </button>
                        )}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Siswa</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Buku</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Tanggal Pinjam</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Tanggal Kembali</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map(item => {
                      const isSelectable = item.status === 'Pending'
                      const isSelected   = selectedIds.has(item.id)
                      return (
                        <tr
                          key={item.id}
                          className={`border-b border-gray-100 transition-colors ${
                            isSelected ? 'bg-indigo-50/60' : 'hover:bg-gray-50'
                          }`}
                        >
                          <td className="px-4 py-3">
                            {isSelectable && (
                              <button
                                onClick={() => toggleSelect(item.id)}
                                aria-label={isSelected ? 'Batalkan pilih' : 'Pilih'}
                                className="text-indigo-600 hover:text-indigo-700"
                              >
                                {isSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                              </button>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm font-semibold text-gray-900">{item.user_nama}</span>
                          </td>
                          <td className="px-4 py-3">
                            <div>
                              <p className="text-sm font-semibold text-gray-900 max-w-[200px] truncate">{item.judul}</p>
                              <p className="text-xs text-gray-500 truncate">{item.penulis}</p>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-block px-2 py-1 rounded-full text-xs font-semibold ${STATUS_CHIP[item.status]}`}>
                              {item.status}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600">{formatDate(item.tanggal_pinjam)}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600">{formatDate(item.tanggal_kembali)}</span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2">
                              {item.status === 'Pending' && (
                                <button
                                  disabled={actionLoading[item.id]}
                                  onClick={() => handleAction(item.id, 'approve')}
                                  className="px-3 py-2 text-xs font-semibold bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  Setujui
                                </button>
                              )}
                              {item.status === 'Pending' && (
                                <button
                                  disabled={actionLoading[item.id]}
                                  onClick={() => handleAction(item.id, 'reject')}
                                  className="px-3 py-2 text-xs font-semibold bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  Tolak
                                </button>
                              )}
                              {item.status === 'Dipinjam' && (
                                <button
                                  disabled={actionLoading[item.id]}
                                  onClick={() => handleAction(item.id, 'return')}
                                  className="px-3 py-2 text-xs font-semibold bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  Catat Kembali
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default AdminBorrowsPage
