import { useState } from 'react'
import { Link } from 'react-router'
import { BookOpen, Heart } from 'lucide-react'
import { toast } from 'react-hot-toast'
import api from '../services/api'
import useAuthStore from '../store/authStore'
import type { Book } from '../types'

interface BookCardProps {
  book: Book
  onFavoriteChange?: (bookId: number, isFavorite: boolean) => void
}

// Palette warna gradien untuk placeholder buku tanpa cover
const GRADIENTS = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)',
]

type CoverState = 'db' | 'openlibrary' | 'none'

function BookCard({ book, onFavoriteChange }: BookCardProps) {
  const [coverState, setCoverState] = useState<CoverState>(
    book.cover_url ? 'db' : book.isbn ? 'openlibrary' : 'none'
  )
  const [isFavorite, setIsFavorite] = useState(!!book.is_favorite)
  const isAuthenticated = useAuthStore(s => s.isAuthenticated)
  const isAvailable = book.stok_tersedia > 0

  const gradient = GRADIENTS[book.id % GRADIENTS.length]
  const openLibrarySrc = book.isbn
    ? `https://covers.openlibrary.org/b/isbn/${book.isbn.replace(/-/g, '')}-M.jpg`
    : null

  const handleImgError = () => {
    if (coverState === 'db' && openLibrarySrc) {
      setCoverState('openlibrary')
    } else {
      setCoverState('none')
    }
  }

  // Open Library mengembalikan gambar "no cover" berukuran 1x1 px — deteksi via naturalWidth
  const handleImgLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    if (coverState === 'openlibrary' && e.currentTarget.naturalWidth < 10) {
      setCoverState('none')
    }
  }

  const coverSrc =
    coverState === 'db' ? book.cover_url! :
    coverState === 'openlibrary' ? openLibrarySrc! :
    null

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!isAuthenticated) {
      toast('Login dulu untuk simpan favorit ❤️', { icon: '🔑' })
      return
    }

    const next = !isFavorite
    setIsFavorite(next)
    onFavoriteChange?.(book.id, next)

    try {
      if (next) await api.post('/favorites', { book_id: book.id })
      else      await api.delete(`/favorites/${book.id}`)
    } catch {
      setIsFavorite(!next)
      onFavoriteChange?.(book.id, !next)
      toast.error('Gagal menyimpan favorit. Coba lagi.')
    }
  }

  return (
    <Link
      to={`/buku/${book.id}`}
      className="block relative overflow-hidden transition-all duration-200"
      style={{
        background: 'var(--bg-card)',
        border: '1.5px solid var(--border)',
        borderRadius: '16px',
        boxShadow: 'var(--shadow-sm)',
      }}
      onMouseEnter={e => {
        const el = e.currentTarget as HTMLAnchorElement
        el.style.transform = 'translateY(-4px)'
        el.style.boxShadow = 'var(--shadow-lg)'
        el.style.borderColor = 'var(--accent)'
      }}
      onMouseLeave={e => {
        const el = e.currentTarget as HTMLAnchorElement
        el.style.transform = 'translateY(0)'
        el.style.boxShadow = 'var(--shadow-sm)'
        el.style.borderColor = 'var(--border)'
      }}
    >
      <span
        className="absolute top-2 right-2 z-10 text-[10px] font-extrabold px-2 py-0.5 rounded-full"
        style={isAvailable
          ? { background: 'var(--avail-bg)', color: 'var(--avail)' }
          : { background: 'var(--unavail-bg)', color: 'var(--unavail)' }
        }
      >
        {isAvailable ? 'Tersedia' : 'Habis'}
      </span>

      <button
        type="button"
        onClick={handleToggleFavorite}
        aria-label={isFavorite ? 'Hapus dari favorit' : 'Tambah ke favorit'}
        className="absolute top-2 left-2 z-10 rounded-full p-1.5 transition-all duration-200 hover:scale-110"
        style={{
          background: isFavorite ? 'rgba(220,38,38,.95)' : 'rgba(255,255,255,.88)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          boxShadow: '0 2px 6px rgba(0,0,0,.12)',
        }}
      >
        <Heart
          size={16}
          fill={isFavorite ? '#fff' : 'none'}
          style={{ color: isFavorite ? '#fff' : '#dc2626' }}
        />
      </button>

      <div className="w-full aspect-[3/4] overflow-hidden" style={{ background: 'var(--bg-subtle)' }}>
        {coverSrc ? (
          <img
            src={coverSrc}
            alt={book.judul}
            className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
            onError={handleImgError}
            onLoad={handleImgLoad}
          />
        ) : (
          // Gradient placeholder dengan inisial judul
          <div
            className="w-full h-full flex flex-col items-center justify-center gap-3 px-4"
            style={{ background: gradient }}
          >
            <BookOpen size={36} style={{ color: 'rgba(255,255,255,0.7)' }} />
            <p className="text-center text-xs font-bold leading-tight line-clamp-3" style={{ color: 'rgba(255,255,255,0.9)' }}>
              {book.judul}
            </p>
          </div>
        )}
      </div>

      <div className="p-2.5 md:p-4">
        <p className="text-[13px] md:text-sm font-extrabold line-clamp-2 leading-snug" style={{ color: 'var(--text)' }}>
          {book.judul}
        </p>
        <p className="text-[11px] md:text-xs font-semibold mt-1 md:mt-1.5 truncate" style={{ color: 'var(--text-3)' }}>
          {book.penulis}
        </p>
        <span
          className="inline-block text-[10px] md:text-[11px] font-bold px-2 md:px-2.5 py-0.5 md:py-1 rounded-full mt-1.5 md:mt-2 max-w-full truncate"
          style={{ background: 'var(--accent-soft)', color: 'var(--accent-txt)' }}
        >
          {book.kategori_nama}
        </span>
      </div>
    </Link>
  )
}

export default BookCard
