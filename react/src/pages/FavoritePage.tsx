// Daftar buku yang di-favorit siswa. Heart click memanggil ulang load — list shrink.
import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router'
import { Heart } from 'lucide-react'
import Navbar from '../components/Navbar'
import BookCard from '../components/BookCard'
import SkeletonCard from '../components/SkeletonCard'
import api from '../services/api'
import type { Book, ApiResponse } from '../types'

function FavoritePage() {
  const [books, setBooks] = useState<Book[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const load = useCallback(() => {
    setIsLoading(true)
    api.get<ApiResponse<Book[]>>('/favorites')
      .then(res => setBooks(res.data.data.map(b => ({ ...b, is_favorite: true }))))
      .catch(() => setBooks([]))
      .finally(() => setIsLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  // Hapus card dari list saat user un-favorite di sini (heart click)
  const handleFavoriteChange = (bookId: number, isFavorite: boolean) => {
    if (!isFavorite) {
      setBooks(prev => prev.filter(b => b.id !== bookId))
    }
  }

  return (
    <>
      <Navbar />
      <div className="pt-[60px]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
          <div className="flex items-center gap-2">
            <Heart size={24} className="fill-red-500 text-red-500" />
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 800, color: 'var(--text)' }}>
              Favorit Saya
            </h1>
          </div>
          <p className="text-sm font-semibold mt-1" style={{ color: 'var(--text-3)' }}>
            {isLoading ? 'Memuat...' : `${books.length} buku tersimpan`}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 mt-6">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)
            ) : books.length === 0 ? (
              <div className="col-span-full text-center py-16">
                <Heart size={48} className="mx-auto opacity-30" style={{ color: 'var(--text-3)' }} />
                <p className="font-bold mt-3" style={{ color: 'var(--text-2)' }}>
                  Belum ada buku favorit
                </p>
                <p className="text-sm mt-1" style={{ color: 'var(--text-3)' }}>
                  Klik ikon hati pada buku di katalog untuk menyimpan favorit.
                </p>
                <Link
                  to="/katalog"
                  className="inline-block mt-4 text-sm font-extrabold px-5 py-2 rounded-full text-white"
                  style={{ background: 'var(--accent)' }}
                >
                  Cari Buku
                </Link>
              </div>
            ) : (
              books.map(book => (
                <BookCard key={book.id} book={book} onFavoriteChange={handleFavoriteChange} />
              ))
            )}
          </div>
        </div>
      </div>
    </>
  )
}

export default FavoritePage
