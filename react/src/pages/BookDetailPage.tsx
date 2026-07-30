// CAT-05: Full book detail with sinopsis and real-time stok
// BORROW-01: Submit borrow via POST /api/borrow
// BORROW-03: 3-condition canBorrow disable logic (D-12)
// D-21: optimistic toast + disable after borrow
import { useState, useEffect } from 'react'
import { useParams, Link, useLocation } from 'react-router'
import { toast } from 'react-hot-toast'
import { BookOpen, Loader2, ArrowLeft, Heart } from 'lucide-react'
import Navbar from '../components/Navbar'
import BookCard from '../components/BookCard'
import SkeletonCard from '../components/SkeletonCard'
import CarouselRow from '../components/CarouselRow'
import useAuthStore from '../store/authStore'
import api from '../services/api'
import type { BookDetail, BorrowItem, ApiResponse, Book } from '../types'

function BookDetailPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  const [book, setBook] = useState<BookDetail | null>(null)
  const [borrows, setBorrows] = useState<BorrowItem[]>([])
  const [isLoadingBook, setIsLoadingBook] = useState(true)
  const [isLoadingBorrows, setIsLoadingBorrows] = useState(true)
  const [isBorrowing, setIsBorrowing] = useState(false)
  // Optimistic disable after successful POST — prevents re-click before refetch
  const [hasBorrowed, setHasBorrowed] = useState(false)
  const [notFound, setNotFound] = useState(false)
  const [coverError, setCoverError] = useState(false)
  const [similarBooks, setSimilarBooks] = useState<Book[]>([])
  const [isLoadingRecs, setIsLoadingRecs] = useState(false)
  const [isFavorite, setIsFavorite] = useState(false)
  const [isTogglingFav, setIsTogglingFav] = useState(false)

  useEffect(() => {
    if (!id) return
    setIsLoadingBook(true)
    setCoverError(false)
    // Berpindah ke buku lain lewat panel rekomendasi hanya mengganti :id —
    // komponen ini tidak dilepas, sehingga state per-buku harus dibersihkan
    // sendiri. Tanpa ini, hasBorrowed dari buku sebelumnya ikut terbawa dan
    // tombol pinjam pada buku baru salah menampilkan "Menunggu persetujuan".
    setHasBorrowed(false)
    setNotFound(false)
    api.get<ApiResponse<BookDetail>>(`/books/${id}`)
      .then(res => {
        setBook(res.data.data)
        setIsFavorite(!!res.data.data.is_favorite)
      })
      .catch(err => {
        if (err.response?.status === 404) setNotFound(true)
        else toast.error('Gagal memuat detail buku.')
      })
      .finally(() => setIsLoadingBook(false))
  }, [id])

  useEffect(() => {
    if (!id || !isAuthenticated) {
      setIsLoadingBorrows(false)
      return
    }
    setIsLoadingBorrows(true)
    api.get<ApiResponse<BorrowItem[]>>('/borrow/status')
      .then(res => setBorrows(res.data.data))
      .catch(() => {})
      .finally(() => setIsLoadingBorrows(false))
  }, [id, isAuthenticated])

  // Fetch similar books — non-blocking, silent failure (D-07)
  useEffect(() => {
    if (!id) return
    setIsLoadingRecs(true)
    api.get<ApiResponse<Book[]>>(`/books/${id}/recommend`, { params: { limit: 5 } })
      .then(res => setSimilarBooks(Array.isArray(res.data.data) ? res.data.data.slice(0, 5) : []))
      .catch(() => setSimilarBooks([]))
      .finally(() => setIsLoadingRecs(false))
  }, [id])

  // D-12: three-condition canBorrow
  const activeCount = borrows.filter(b => b.status === 'Pending' || b.status === 'Dipinjam').length
  const thisBookActive = borrows.some(b => b.buku_id === Number(id) && (b.status === 'Pending' || b.status === 'Dipinjam'))
  const canBorrow = !hasBorrowed && book !== null && book.stok_tersedia > 0 && activeCount < 3 && !thisBookActive

  const disabledTooltip = hasBorrowed
    ? 'Menunggu persetujuan...'
    : book?.stok_tersedia === 0 ? 'Buku ini sedang tidak tersedia'
    : activeCount >= 3 ? 'Kamu sudah meminjam 3 buku. Kembalikan buku dulu ya!'
    : thisBookActive ? 'Kamu sudah meminjam buku ini'
    : ''

  const handleToggleFavorite = async () => {
    if (!isAuthenticated) {
      toast('Login dulu untuk simpan favorit ❤️', { icon: '🔑' })
      return
    }
    if (!book || isTogglingFav) return
    const next = !isFavorite
    setIsFavorite(next)
    setIsTogglingFav(true)
    try {
      if (next) await api.post('/favorites', { book_id: book.id })
      else      await api.delete(`/favorites/${book.id}`)
    } catch {
      setIsFavorite(!next)
      toast.error('Gagal menyimpan favorit. Coba lagi.')
    } finally {
      setIsTogglingFav(false)
    }
  }

  const handleBorrow = async () => {
    if (!id || !canBorrow) return
    setIsBorrowing(true)
    try {
      await api.post('/borrow', { book_id: Number(id) })
      toast.success('Permintaan peminjaman berhasil dikirim!')
      setHasBorrowed(true)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string } } }
      toast.error(axiosErr?.response?.data?.message ?? 'Gagal mengajukan peminjaman. Coba lagi.')
    } finally {
      setIsBorrowing(false)
    }
  }

  if (notFound) {
    return (
      <>
        <Navbar />
        <div className="pt-[60px]">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 text-center">
            <p style={{ color: 'var(--text-3)' }}>Buku tidak ditemukan.</p>
            <Link to="/katalog" className="text-sm mt-4 block hover:underline" style={{ color: 'var(--accent)' }}>
              ← Kembali ke Katalog
            </Link>
          </div>
        </div>
      </>
    )
  }

  if (isLoadingBook) {
    return (
      <>
        <Navbar />
        <div className="pt-[60px]">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
            <div className="h-4 rounded-full animate-pulse w-32 mb-6" style={{ background: 'var(--bg-subtle)' }} />
            <div className="flex gap-8 flex-col md:flex-row">
              <div className="w-full md:w-56 flex-shrink-0">
                <div className="w-full aspect-[3/4] animate-pulse" style={{ background: 'var(--bg-subtle)', borderRadius: '16px' }} />
              </div>
              <div className="flex-1 space-y-3">
                <div className="h-7 rounded-full animate-pulse w-4/5" style={{ background: 'var(--bg-subtle)' }} />
                <div className="h-4 rounded-full animate-pulse w-3/5" style={{ background: 'var(--bg-subtle)' }} />
                <div className="h-4 rounded-full animate-pulse w-2/5" style={{ background: 'var(--bg-subtle)' }} />
              </div>
            </div>
          </div>
        </div>
      </>
    )
  }

  if (!book) return null

  const isAvailable = book.stok_tersedia > 0

  return (
    <>
      <Navbar />
      <div className="pt-[60px]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          <Link
            to="/katalog"
            className="inline-flex items-center gap-1.5 text-sm font-bold mb-6 transition-colors"
            style={{ color: 'var(--accent)' }}
          >
            <ArrowLeft size={14} />
            Kembali ke Katalog
          </Link>

          <div className="flex gap-8 flex-col md:flex-row">
            {/* Cover */}
            <div className="w-full md:w-56 flex-shrink-0">
              {book.cover_url && !coverError ? (
                <img
                  src={book.cover_url}
                  alt={book.judul}
                  className="w-full aspect-[3/4] object-cover"
                  style={{ borderRadius: '16px', boxShadow: 'var(--shadow-md)' }}
                  onError={() => setCoverError(true)}
                />
              ) : (
                <div
                  className="w-full aspect-[3/4] flex items-center justify-center text-5xl"
                  style={{ borderRadius: '16px', boxShadow: 'var(--shadow-md)', background: 'var(--bg-subtle)' }}
                >
                  <BookOpen size={48} style={{ color: 'var(--text-3)' }} />
                </div>
              )}
            </div>

            {/* Info */}
            {/* min-w-0 wajib: kolom ini memuat korsel Buku Serupa yang lebarnya
                melebihi layar. Tanpa min-w-0, flex item memakai min-width:auto
                sehingga ikut melar dan membuat seluruh halaman meluber ke kanan
                — sinopsis terpotong dan kartu keluar dari viewport. */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-3">
                <h1 className="flex-1 text-2xl font-extrabold leading-tight" style={{ fontFamily: 'var(--font-display)', color: 'var(--text)' }}>
                  {book.judul}
                </h1>
                <button
                  type="button"
                  onClick={handleToggleFavorite}
                  disabled={isTogglingFav}
                  aria-label={isFavorite ? 'Hapus dari favorit' : 'Tambah ke favorit'}
                  className="flex-shrink-0 rounded-full p-2.5 transition-all duration-200 hover:scale-110 disabled:opacity-60"
                  style={{
                    background: isFavorite ? 'rgba(220,38,38,1)' : 'var(--bg-subtle)',
                    border: isFavorite ? '2px solid rgba(220,38,38,1)' : '2px solid var(--border)',
                  }}
                  title={isFavorite ? 'Hapus dari favorit' : 'Simpan ke favorit'}
                >
                  <Heart
                    size={18}
                    fill={isFavorite ? '#fff' : 'none'}
                    style={{ color: isFavorite ? '#fff' : '#dc2626' }}
                  />
                </button>
              </div>
              <p className="mt-1 font-semibold" style={{ color: 'var(--text-2)' }}>{book.penulis}</p>

              <span
                className="inline-block text-xs font-bold px-3 py-1 rounded-full mt-2"
                style={{ background: 'var(--accent-soft)', color: 'var(--accent-txt)' }}
              >
                {book.kategori_nama}
              </span>

              {/* Stock stats */}
              <div className="flex items-center gap-3 mt-4">
                <span
                  className="inline-block rounded-full px-3 py-1 text-sm font-bold"
                  style={isAvailable
                    ? { background: 'var(--avail-bg)', color: 'var(--avail)' }
                    : { background: 'var(--unavail-bg)', color: 'var(--unavail)' }
                  }
                >
                  {isAvailable ? 'Tersedia' : 'Habis'}
                </span>
                <span className="text-sm font-semibold" style={{ color: 'var(--text-3)' }}>
                  {book.stok_tersedia} dari {book.stok_total} eksemplar
                </span>
              </div>

              {/* Sinopsis */}
              {book.sinopsis && (
                <div className="mt-6">
                  <h2 className="text-base font-extrabold mb-2" style={{ color: 'var(--text)' }}>Sinopsis</h2>
                  <p
                    className="text-sm leading-relaxed whitespace-pre-line pl-4"
                    style={{ color: 'var(--text-2)', borderLeft: '3px solid var(--accent)' }}
                  >
                    {book.sinopsis}
                  </p>
                </div>
              )}

              {/* REC-01: Buku Serupa — hidden if empty and not loading (D-07) */}
              {(isLoadingRecs || similarBooks.length > 0) && (
                <div className="mt-6">
                  <div className="flex items-center gap-2 mb-3">
                    <h2 className="text-base font-extrabold" style={{ color: 'var(--text)' }}>Buku Serupa</h2>
                    <span
                      className="text-[11px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider"
                      style={{ background: 'var(--accent-soft)', color: 'var(--accent-txt)' }}
                    >
                      CBF
                    </span>
                  </div>
                  <CarouselRow className="gap-4 pb-3 -mx-4 px-4">
                    {isLoadingRecs
                      ? Array.from({ length: 5 }).map((_, i) => (
                          <div key={i} className="flex-shrink-0" style={{ width: 210, scrollSnapAlign: 'start' }}>
                            <SkeletonCard />
                          </div>
                        ))
                      : similarBooks.map(b => (
                          <div key={b.id} className="flex-shrink-0" style={{ width: 210, scrollSnapAlign: 'start' }}>
                            <BookCard book={b} />
                          </div>
                        ))
                    }
                  </CarouselRow>
                </div>
              )}

              {/* Borrow button — guest sees login prompt, siswa sees D-12 logic */}
              <div className="mt-6">
                {!isAuthenticated ? (
                  <Link
                    to="/login"
                    state={{ from: location }}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-extrabold text-white transition-all duration-200"
                    style={{ background: 'var(--accent)' }}
                    onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'var(--accent-h)' }}
                    onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'var(--accent)' }}
                  >
                    Masuk untuk Meminjam
                  </Link>
                ) : isLoadingBorrows ? (
                  <button
                    disabled
                    className="px-6 py-3 rounded-full text-sm font-extrabold flex items-center gap-2 cursor-not-allowed"
                    style={{ background: 'var(--bg-subtle)', color: 'var(--text-3)' }}
                  >
                    <Loader2 size={16} className="animate-spin" /> Memeriksa...
                  </button>
                ) : hasBorrowed ? (
                  <button
                    disabled
                    className="px-6 py-3 rounded-full text-sm font-extrabold cursor-not-allowed"
                    style={{ background: 'var(--bg-subtle)', color: 'var(--text-3)' }}
                  >
                    Menunggu Persetujuan
                  </button>
                ) : canBorrow ? (
                  <button
                    onClick={handleBorrow}
                    disabled={isBorrowing}
                    className="px-6 py-3 rounded-full text-sm font-extrabold text-white flex items-center gap-2 transition-all duration-200 disabled:opacity-50"
                    style={{ background: 'var(--accent)' }}
                    onMouseEnter={e => { if (!isBorrowing) (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent-h)' }}
                    onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent)' }}
                  >
                    {isBorrowing ? <><Loader2 size={16} className="animate-spin" /> Memproses...</> : 'Pinjam Buku Ini'}
                  </button>
                ) : (
                  <button
                    disabled
                    title={disabledTooltip}
                    className="px-6 py-3 rounded-full text-sm font-extrabold cursor-not-allowed"
                    style={{ background: 'var(--bg-subtle)', color: 'var(--text-3)' }}
                  >
                    Pinjam Buku Ini
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default BookDetailPage
