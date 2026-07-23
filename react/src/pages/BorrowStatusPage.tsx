// Daftar pinjaman siswa dengan timeline visual + countdown jatuh tempo.
import { useState, useEffect } from 'react'
import { BookOpen } from 'lucide-react'
import Navbar from '../components/Navbar'
import BorrowTimeline from '../components/BorrowTimeline'
import DueCountdown from '../components/DueCountdown'
import api from '../services/api'
import type { BorrowItem, ApiResponse } from '../types'

type FilterTab = 'Semua' | BorrowItem['status']
const FILTER_TABS: FilterTab[] = ['Semua', 'Pending', 'Dipinjam', 'Dikembalikan', 'Ditolak']

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr.replace(' ', 'T'))
      .toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return '—'
  }
}

function SkeletonRow() {
  return (
    <div className="p-4" style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border)', borderRadius: '16px', boxShadow: 'var(--shadow-sm)' }}>
      <div className="flex gap-4">
        <div className="flex-shrink-0 rounded-[10px] animate-pulse" style={{ width: 52, height: 70, background: 'var(--bg-subtle)' }} />
        <div className="flex-1 space-y-2 py-1">
          <div className="h-4 rounded-full animate-pulse w-3/4" style={{ background: 'var(--bg-subtle)' }} />
          <div className="h-3 rounded-full animate-pulse w-1/2" style={{ background: 'var(--bg-subtle)' }} />
          <div className="h-5 rounded-full animate-pulse w-24 mt-2" style={{ background: 'var(--bg-subtle)' }} />
        </div>
      </div>
      <div className="h-10 mt-4 rounded-lg animate-pulse" style={{ background: 'var(--bg-subtle)' }} />
    </div>
  )
}

function BorrowStatusPage() {
  const [borrows, setBorrows] = useState<BorrowItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState<FilterTab>('Semua')
  const [coverErrors, setCoverErrors] = useState<Set<number>>(new Set())

  useEffect(() => {
    setIsLoading(true)
    api.get<ApiResponse<BorrowItem[]>>('/borrow/status')
      .then(res => setBorrows(res.data.data))
      .catch(() => setBorrows([]))
      .finally(() => setIsLoading(false))
  }, [])

  const filtered = activeFilter === 'Semua'
    ? borrows
    : borrows.filter(b => b.status === activeFilter)

  const countByStatus = (s: FilterTab) =>
    s === 'Semua' ? borrows.length : borrows.filter(b => b.status === s).length

  return (
    <>
      <Navbar />
      <div className="pt-[60px]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
          <div className="flex items-baseline justify-between flex-wrap gap-2">
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 800, color: 'var(--text)' }}>
              Pinjaman Saya
            </h1>
            <p className="text-sm font-bold" style={{ color: 'var(--text-3)' }}>
              {borrows.length} total pinjaman
            </p>
          </div>

          <div className="flex gap-2 flex-wrap mt-5">
            {FILTER_TABS.map(tab => {
              const count = countByStatus(tab)
              const isActive = activeFilter === tab
              return (
                <button
                  key={tab}
                  onClick={() => setActiveFilter(tab)}
                  className="text-sm font-bold px-4 py-1.5 rounded-full border-2 transition-all duration-200 inline-flex items-center gap-2"
                  style={isActive
                    ? { background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' }
                    : { background: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-2)' }
                  }
                >
                  {tab}
                  <span
                    className="text-[10px] font-extrabold px-1.5 rounded-full"
                    style={{
                      background: isActive ? 'rgba(255,255,255,.2)' : 'var(--bg-subtle)',
                      color: isActive ? '#fff' : 'var(--text-3)',
                      minWidth: 18,
                    }}
                  >
                    {count}
                  </span>
                </button>
              )
            })}
          </div>

          <div className="mt-5 flex flex-col gap-3">
            {isLoading ? (
              <><SkeletonRow /><SkeletonRow /><SkeletonRow /></>
            ) : filtered.length === 0 ? (
              <div className="text-center py-16">
                <p className="font-bold" style={{ color: 'var(--text-3)' }}>
                  {activeFilter === 'Semua'
                    ? 'Belum ada pinjaman. Cari buku menarik di Katalog! 📚'
                    : `Tidak ada pinjaman dengan status ${activeFilter}.`}
                </p>
              </div>
            ) : (
              filtered.map(item => (
                <div
                  key={item.id}
                  className="p-4 transition-all duration-200"
                  style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border)', borderRadius: '16px', boxShadow: 'var(--shadow-sm)' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--accent)'; (e.currentTarget as HTMLDivElement).style.boxShadow = 'var(--shadow-md)' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLDivElement).style.boxShadow = 'var(--shadow-sm)' }}
                >
                  <div className="flex gap-4">
                    <div
                      className="flex-shrink-0 flex items-center justify-center overflow-hidden"
                      style={{ width: 52, height: 70, borderRadius: '10px', background: 'var(--bg-subtle)' }}
                    >
                      {item.cover_url && !coverErrors.has(item.id) ? (
                        <img
                          src={item.cover_url}
                          alt={item.judul}
                          className="w-full h-full object-cover"
                          onError={() => setCoverErrors(prev => new Set(prev).add(item.id))}
                        />
                      ) : (
                        <BookOpen size={20} style={{ color: 'var(--text-3)' }} />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-extrabold line-clamp-2 leading-snug" style={{ color: 'var(--text)' }}>
                        {item.judul}
                      </p>
                      <p className="text-xs font-semibold mt-0.5 truncate" style={{ color: 'var(--text-3)' }}>
                        {item.penulis}
                      </p>

                      {item.status === 'Dipinjam' && (
                        <DueCountdown tanggalApprove={item.tanggal_approve} />
                      )}

                      <div className="mt-2 text-xs font-semibold flex flex-wrap gap-x-4 gap-y-0.5" style={{ color: 'var(--text-3)' }}>
                        <span>Diajukan: <strong style={{ color: 'var(--text-2)' }}>{formatDate(item.tanggal_pinjam)}</strong></span>
                        {item.tanggal_approve && (
                          <span>Disetujui: <strong style={{ color: 'var(--text-2)' }}>{formatDate(item.tanggal_approve)}</strong></span>
                        )}
                        {item.tanggal_reject && (
                          <span>Ditolak: <strong style={{ color: 'var(--text-2)' }}>{formatDate(item.tanggal_reject)}</strong></span>
                        )}
                        {item.tanggal_kembali && (
                          <span>Dikembalikan: <strong style={{ color: 'var(--text-2)' }}>{formatDate(item.tanggal_kembali)}</strong></span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
                    <BorrowTimeline item={item} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  )
}

export default BorrowStatusPage
