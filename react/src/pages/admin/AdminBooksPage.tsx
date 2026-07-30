// ADMIN-01: Book management table — list, add, edit, delete with BookFormModal
// GET /api/books (paginated, limit 20) — uses existing endpoint from Phase 2
// POST /api/books — add book
// PUT /api/books/:id — edit book
// DELETE /api/books/:id — delete book (with browser confirm())
// Per D-04, UI-SPEC §AdminBooksPage Contract
import { useState, useEffect, useCallback } from 'react'
import { Plus, BookX, Search, X } from 'lucide-react'
import { toast } from 'react-hot-toast'
import AdminSidebar from '../../components/AdminSidebar'
import BookFormModal from '../../components/BookFormModal'
import Pagination from '../../components/Pagination'
import useDebounce from '../../hooks/useDebounce'
import api from '../../services/api'
import type { Book, Category, ApiResponse, PaginatedResponse } from '../../types'

function AdminBooksPage() {
  const [books, setBooks]           = useState<Book[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoading, setIsLoading]   = useState(true)
  const [page, setPage]             = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalBooks, setTotalBooks] = useState(0)
  const [showModal, setShowModal]   = useState(false)
  const [modalBook, setModalBook]   = useState<Book | null>(null)  // null = add mode

  // Pencarian dan penyaringan memakai parameter q dan kategori_id pada endpoint
  // /books yang sama dengan halaman katalog, sehingga tidak perlu endpoint baru.
  const [searchInput, setSearchInput] = useState('')
  const [kategoriId, setKategoriId]   = useState('')
  const search = useDebounce(searchInput, 400)

  const fetchBooks = useCallback(() => {
    setIsLoading(true)
    const params: Record<string, string | number> = { page, limit: 20 }
    if (search) params.q = search
    if (kategoriId) params.kategori_id = kategoriId

    api.get<ApiResponse<PaginatedResponse<Book>>>('/books', { params })
      .then(res => {
        setBooks(res.data.data.items)
        setTotalPages(res.data.data.total_pages)
        setTotalBooks(res.data.data.total ?? res.data.data.items.length)
      })
      .catch(() => setBooks([]))
      .finally(() => setIsLoading(false))
  }, [page, search, kategoriId])

  useEffect(() => { fetchBooks() }, [fetchBooks])

  // Kembali ke halaman pertama setiap kali kriteria berubah, agar hasil
  // pencarian tidak dibuka pada halaman yang sudah tidak ada lagi.
  useEffect(() => { setPage(1) }, [search, kategoriId])

  useEffect(() => {
    api.get<ApiResponse<Category[]>>('/categories')
      .then(res => setCategories(res.data.data))
      .catch(() => {})
  }, [])

  const handleOpenAdd = () => {
    setModalBook(null)
    setShowModal(true)
  }

  const handleOpenEdit = (book: Book) => {
    setModalBook(book)
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setModalBook(null)
  }

  const handleModalSuccess = () => {
    handleCloseModal()
    fetchBooks()
  }

  const handleDelete = async (book: Book) => {
    // Peringatan menyebut riwayat peminjaman secara eksplisit: sejak buku yang
    // pernah dipinjam dapat dihapus, riwayatnya ikut hilang dan itu tidak
    // terlihat dari tabel.
    const konfirmasi = confirm(
      `Hapus buku "${book.judul}"?\n\n` +
      `Riwayat peminjaman buku ini dan semua penandaan favorit akan ikut terhapus.\n` +
      `Tindakan ini tidak dapat dibatalkan.`
    )
    if (!konfirmasi) return

    try {
      const res = await api.delete<ApiResponse<{ riwayat_terhapus: number }>>(`/books/${book.id}`)
      const n = res.data.data?.riwayat_terhapus ?? 0
      toast.success(n > 0
        ? `Buku dihapus beserta ${n} riwayat peminjaman.`
        : 'Buku berhasil dihapus.')
      fetchBooks()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string } } }
      toast.error(axiosErr?.response?.data?.message ?? 'Gagal menghapus buku. Periksa koneksi dan coba lagi.')
    }
  }

  return (
    <div className="flex">
      <AdminSidebar />
      <main className="ml-0 md:ml-64 pt-14 md:pt-0 flex-1 min-w-0 min-h-screen bg-gray-50">
        <div className="px-4 md:px-8 py-6 md:py-8">
          {/* Page header */}
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-semibold text-gray-900">Kelola Buku</h1>
            <button
              onClick={handleOpenAdd}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
            >
              <Plus size={16} />
              Tambah Buku
            </button>
          </div>

          {/* Pencarian dan penyaringan */}
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={searchInput}
                onChange={e => setSearchInput(e.target.value)}
                placeholder="Cari judul, penulis, atau kata kunci..."
                className="w-full pl-9 pr-9 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
              {searchInput && (
                <button
                  onClick={() => setSearchInput('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label="Hapus pencarian"
                >
                  <X size={15} />
                </button>
              )}
            </div>

            <select
              value={kategoriId}
              onChange={e => setKategoriId(e.target.value)}
              className="sm:w-52 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Semua kategori</option>
              {categories.map(k => (
                <option key={k.id} value={k.id}>{k.nama}</option>
              ))}
            </select>
          </div>

          {/* Ringkasan hasil — membantu admin tahu apakah penyaringan sedang aktif */}
          {!isLoading && (
            <p className="mt-3 text-sm text-gray-500">
              {search || kategoriId
                ? <>Menampilkan <span className="font-semibold text-gray-700">{totalBooks}</span> buku hasil pencarian.</>
                : <>Total <span className="font-semibold text-gray-700">{totalBooks}</span> buku dalam koleksi.</>}
            </p>
          )}

          {/* Books table */}
          <div className="mt-4 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {isLoading ? (
              <div className="py-16 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : books.length === 0 ? (
              // Inline empty state — EmptyState.tsx only supports catalog search reset, not custom heading/body
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <BookX size={48} className="text-gray-300" />
                {search || kategoriId ? (
                  <>
                    <h3 className="text-lg font-semibold text-gray-500 mt-4">Tidak ada buku yang cocok</h3>
                    <p className="text-sm text-gray-400 mt-2">
                      Coba kata kunci lain atau ubah penyaring kategori.
                    </p>
                    <button
                      onClick={() => { setSearchInput(''); setKategoriId('') }}
                      className="mt-4 px-4 py-2 text-sm font-semibold text-indigo-600 border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors"
                    >
                      Hapus filter
                    </button>
                  </>
                ) : (
                  <>
                    <h3 className="text-lg font-semibold text-gray-500 mt-4">Belum ada buku</h3>
                    <p className="text-sm text-gray-400 mt-2">Tambahkan buku pertama menggunakan tombol di atas.</p>
                  </>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Judul</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Penulis</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Kategori</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500">Stok</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {books.map(book => (
                    <tr key={book.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-sm font-semibold text-gray-900 max-w-[240px] truncate block">{book.judul}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-gray-600 max-w-[160px] truncate block">{book.penulis}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-gray-600">{book.kategori_nama}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-sm text-gray-900 font-semibold">{book.stok_tersedia}/{book.stok_total}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleOpenEdit(book)}
                            className="px-3 py-2 text-xs font-semibold text-indigo-600 border border-indigo-300 rounded-md hover:bg-indigo-50 transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(book)}
                            className="px-3 py-2 text-xs font-semibold text-red-600 border border-red-300 rounded-md hover:bg-red-50 transition-colors"
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

          {/* Pagination — only show if more than 1 page */}
          {!isLoading && totalPages > 1 && (
            <div className="mt-6">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={(p) => { setPage(p); window.scrollTo(0, 0) }}
              />
            </div>
          )}
        </div>
      </main>

      {/* BookFormModal — rendered outside main so it overlays the sidebar too */}
      {showModal && (
        <BookFormModal
          book={modalBook}
          categories={categories}
          onClose={handleCloseModal}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  )
}

export default AdminBooksPage
