// CAT-01: grid of book cards | CAT-02: search debounced ?q= | CAT-03: category filter | CAT-04: pagination URL-synced
import { useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router'
import { Search, X } from 'lucide-react'
import Navbar from '../components/Navbar'
import BookCard from '../components/BookCard'
import SkeletonCard from '../components/SkeletonCard'
import CarouselRow from '../components/CarouselRow'
import Pagination from '../components/Pagination'
import EmptyState from '../components/EmptyState'
import useDebounce from '../hooks/useDebounce'
import useJudulHalaman from '../hooks/useJudulHalaman'
import useAuthStore from '../store/authStore'
import api from '../services/api'
import type { Book, Category, ApiResponse, PaginatedResponse } from '../types'

const LIMIT = 12

// Dipakai bersama oleh dropdown kategori dan dropdown urutan agar keduanya
// tidak pernah berbeda gaya saat salah satunya disunting.
const GAYA_SELECT: React.CSSProperties = {
  background: 'var(--bg-input)',
  border: '1.5px solid var(--border)',
  borderRadius: '999px',
  color: 'var(--text)',
  fontFamily: 'var(--font-ui)',
  outline: 'none',
  cursor: 'pointer',
}

function CatalogPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const searchBarRef = useRef<HTMLDivElement>(null)
  const [searchParams, setSearchParams] = useSearchParams()

  const page = Number(searchParams.get('page') ?? '1')
  const kategoriId = searchParams.get('kategori') ?? ''
  // 'terbaru' adalah default backend, jadi tidak pernah ditulis ke URL agar
  // tautan katalog polos tetap bersih.
  const urutan = searchParams.get('sort') ?? 'terbaru'
  const [searchInput, setSearchInput] = useState(searchParams.get('q') ?? '')
  const debouncedSearch = useDebounce(searchInput, 400)

  const [books, setBooks] = useState<Book[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [totalPages, setTotalPages] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [personalRecs, setPersonalRecs] = useState<Book[]>([])
  const [popularRecs, setPopularRecs] = useState<Book[]>([])
  const [isLoadingPersonal, setIsLoadingPersonal] = useState(false)
  const [isLoadingPopular, setIsLoadingPopular] = useState(false)

  useJudulHalaman(
    'Katalog Buku',
    'Telusuri koleksi buku Perpustakaan SMPN 1 Kemang. Cari berdasarkan judul, '
    + 'penulis, atau kategori, lalu ajukan peminjaman secara daring lewat LIBRA.',
  )

  useEffect(() => {
    api.get<ApiResponse<Category[]>>('/categories')
      .then(res => setCategories(res.data.data))
      .catch(() => {})
  }, [])

  // Fetch personal recs (authenticated only) + popular books on mount — non-blocking, silent failure (D-08)
  useEffect(() => {
    if (isAuthenticated) {
      setIsLoadingPersonal(true)
      api.get<ApiResponse<Book[]>>('/recommend/personal', { params: { limit: 5 } })
        .then(res => setPersonalRecs(Array.isArray(res.data.data) ? res.data.data.slice(0, 5) : []))
        .catch(() => setPersonalRecs([]))
        .finally(() => setIsLoadingPersonal(false))
    }

    setIsLoadingPopular(true)
    api.get<ApiResponse<Book[]>>('/popular', { params: { limit: 5 } })
      .then(res => setPopularRecs(Array.isArray(res.data.data) ? res.data.data.slice(0, 5) : []))
      .catch(() => setPopularRecs([]))
      .finally(() => setIsLoadingPopular(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  // Sync debounced search to URL — resets to page 1
  useEffect(() => {
    setSearchParams((prev) => {
      const updated = new URLSearchParams(prev)
      if (debouncedSearch) {
        updated.set('q', debouncedSearch)
      } else {
        updated.delete('q')
      }
      updated.delete('page')
      return updated
    }, { replace: true })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch])

  // Fetch books when URL params change
  useEffect(() => {
    setIsLoading(true)
    const q = searchParams.get('q') ?? ''
    const kategori = searchParams.get('kategori') ?? ''
    const sort = searchParams.get('sort') ?? ''
    const currentPage = Number(searchParams.get('page') ?? '1')

    const params: Record<string, string | number> = { page: currentPage, limit: LIMIT }
    // CRITICAL: param must be 'q' — BookController.php reads $_GET['q']
    if (q) params.q = q
    if (kategori) params.kategori_id = kategori
    if (sort) params.sort = sort

    api.get<ApiResponse<PaginatedResponse<Book>>>('/books', { params })
      .then(res => {
        const data = res.data.data
        setBooks(data.items)
        setTotalPages(data.total_pages)
        setTotalItems(data.total)
      })
      .catch(() => {
        setBooks([])
        setTotalPages(1)
        setTotalItems(0)
      })
      .finally(() => setIsLoading(false))
  }, [searchParams])

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSearchParams((prev) => {
      const updated = new URLSearchParams(prev)
      if (e.target.value) {
        updated.set('kategori', e.target.value)
      } else {
        updated.delete('kategori')
      }
      updated.delete('page')
      return updated
    })
  }

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSearchParams((prev) => {
      const updated = new URLSearchParams(prev)
      if (e.target.value === 'terbaru') {
        updated.delete('sort')
      } else {
        updated.set('sort', e.target.value)
      }
      updated.delete('page')   // urutan berubah, nomor halaman lama tidak lagi bermakna
      return updated
    })
  }

  const handlePageChange = (newPage: number) => {
    setSearchParams((prev) => {
      const updated = new URLSearchParams(prev)
      updated.set('page', String(newPage))
      return updated
    })
    if (searchBarRef.current) {
      const top = searchBarRef.current.getBoundingClientRect().top + window.scrollY - 68
      window.scrollTo({ top, behavior: 'smooth' })
    }
  }

  const handleReset = useCallback(() => {
    setSearchInput('')
    setSearchParams({})
  }, [setSearchParams])

  const RecSection = ({ title, badge, books: recBooks, isLoadingRec }: { title: string; badge: string; books: Book[]; isLoadingRec: boolean }) => (
    <div className="mt-6">
      <div className="flex items-center gap-2.5 mb-3">
        <span className="text-base font-extrabold" style={{ color: 'var(--text)' }}>{title}</span>
        <span
          className="text-[11px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider"
          style={{ background: 'var(--accent-soft)', color: 'var(--accent-txt)' }}
        >
          {badge}
        </span>
      </div>
      <CarouselRow className="gap-3 sm:gap-4 pb-3 pr-4">
        {isLoadingRec
          ? Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex-shrink-0 w-[140px] sm:w-[180px] lg:w-[210px]" style={{ scrollSnapAlign: 'start' }}>
                <SkeletonCard />
              </div>
            ))
          : recBooks.map(book => (
              <div key={book.id} className="flex-shrink-0 w-[140px] sm:w-[180px] lg:w-[210px]" style={{ scrollSnapAlign: 'start' }}>
                <BookCard book={book} />
              </div>
            ))
        }
      </CarouselRow>
    </div>
  )

  return (
    <>
      <Navbar />

      {/* Dekorasi karakter — fixed di pojok bawah, di belakang konten */}
      <img
        src="/laki_bg.png"
        alt=""
        aria-hidden="true"
        className="hidden sm:block fixed bottom-0 left-0 pointer-events-none select-none"
        style={{ height: 220, zIndex: 0, opacity: 0.88 }}
      />
      <img
        src="/cewe_bg.png"
        alt=""
        aria-hidden="true"
        className="hidden sm:block fixed bottom-0 right-0 pointer-events-none select-none"
        style={{ height: 220, zIndex: 0, opacity: 0.88 }}
      />

      <div className="pt-[60px]" style={{ position: 'relative', zIndex: 1 }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

          {/* Page heading */}
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '32px', fontWeight: 800, color: 'var(--text)', lineHeight: 1.15 }}>
            Temukan Buku{' '}
            <span style={{ color: 'var(--accent)' }}>Favoritmu</span>
          </h1>

          {/* REC-02: "Untukmu" — hanya untuk user yang sudah login (D-08) */}
          {isAuthenticated && (isLoadingPersonal || personalRecs.length > 0) && (
            <RecSection title="Untukmu" badge="Rekomendasi" books={personalRecs} isLoadingRec={isLoadingPersonal} />
          )}

          {/* REC-03: "Populer" — hidden if empty (D-08) */}
          {(isLoadingPopular || popularRecs.length > 0) && (
            <RecSection title="Populer" badge="Trending" books={popularRecs} isLoadingRec={isLoadingPopular} />
          )}

          {/* Search + filter row — pada layar sempit kedua dropdown turun ke
              baris sendiri agar kolom pencarian tidak terjepit */}
          <div ref={searchBarRef} className="flex flex-col sm:flex-row gap-2.5 sm:items-center mt-6">
            <div className="relative flex-1">
              <Search
                size={18}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
                style={{ color: 'var(--text-3)' }}
              />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Cari buku, penulis, atau kategori..."
                className="w-full pl-10 pr-10 py-3 text-sm font-medium transition-all duration-200"
                style={{
                  background: 'var(--bg-input)',
                  border: '1.5px solid var(--border)',
                  borderRadius: '999px',
                  color: 'var(--text)',
                  fontFamily: 'var(--font-ui)',
                  outline: 'none',
                }}
                onFocus={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(217,119,6,.12)' }}
                onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none' }}
              />
              {searchInput && (
                <button
                  onClick={() => setSearchInput('')}
                  aria-label="Hapus pencarian"
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: 'var(--text-3)' }}
                >
                  <X size={16} />
                </button>
              )}
            </div>

            <div className="flex gap-2.5">
              <select
                value={kategoriId}
                onChange={handleCategoryChange}
                aria-label="Saring menurut kategori"
                className="py-3 px-4 text-sm font-bold flex-1 sm:flex-initial sm:flex-shrink-0 transition-all duration-200"
                style={GAYA_SELECT}
              >
                <option value="">Semua Kategori</option>
                {categories.map(cat => (
                  <option key={cat.id} value={String(cat.id)}>{cat.nama}</option>
                ))}
              </select>

              <select
                value={urutan}
                onChange={handleSortChange}
                aria-label="Urutkan hasil"
                className="py-3 px-4 text-sm font-bold flex-1 sm:flex-initial sm:flex-shrink-0 transition-all duration-200"
                style={GAYA_SELECT}
              >
                <option value="terbaru">Terbaru</option>
                <option value="az">Judul A–Z</option>
              </select>
            </div>
          </div>

          {!isLoading && (
            <p className="text-sm font-semibold mt-3" style={{ color: 'var(--text-3)' }}>
              Menampilkan {totalItems} buku
            </p>
          )}

          {/* Book grid */}
          <div className="grid grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-2.5 sm:gap-4 mt-5">
            {isLoading
              ? Array.from({ length: LIMIT }).map((_, i) => <SkeletonCard key={i} />)
              : books.length === 0
                ? <EmptyState onReset={handleReset} />
                : books.map(book => <BookCard key={book.id} book={book} />)
            }
          </div>

          {!isLoading && books.length > 0 && (
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </div>
      </div>
    </>
  )
}

export default CatalogPage
