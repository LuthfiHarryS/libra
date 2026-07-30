// Add/edit book form modal — used by AdminBooksPage
// cover: file upload (POST /api/books/upload-cover) dilakukan saat form submit, bukan saat pilih file
import { useState, useEffect, useRef } from 'react'
import { toast } from 'react-hot-toast'
import { Loader2, X, Upload, Image } from 'lucide-react'
import api from '../services/api'
import type { Book, Category, ApiResponse } from '../types'

interface BookFormModalProps {
  book: Book | null
  categories: Category[]
  onClose: () => void
  onSuccess: () => void
}

function BookFormModal({ book, categories, onClose, onSuccess }: BookFormModalProps) {
  const [judul, setJudul]           = useState(book?.judul ?? '')
  const [penulis, setPenulis]       = useState(book?.penulis ?? '')
  const [isbn, setIsbn]             = useState(book?.isbn ?? '')
  const [sinopsis, setSinopsis]     = useState('')
  const [stokTotal, setStokTotal]   = useState(book?.stok_total ?? 1)
  const [kategoriId, setKategoriId] = useState(book?.kategori_id ?? (categories[0]?.id ?? 0))
  const [isLoading, setIsLoading]   = useState(false)
  const [isLoadingSinopsis, setIsLoadingSinopsis] = useState(false)

  // Cover: file baru dipilih admin, atau URL existing dari DB
  const [coverFile, setCoverFile]       = useState<File | null>(null)
  const [coverPreview, setCoverPreview] = useState<string | null>(book?.cover_url ?? null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setJudul(book?.judul ?? '')
    setPenulis(book?.penulis ?? '')
    setIsbn(book?.isbn ?? '')
    setSinopsis('')
    setStokTotal(book?.stok_total ?? 1)
    setKategoriId(book?.kategori_id ?? (categories[0]?.id ?? 0))
    setCoverFile(null)
    setCoverPreview(book?.cover_url ?? null)
  }, [book, categories])

  // Sinopsis tidak ikut dikirim oleh GET /books (daftar), hanya oleh GET /books/:id.
  // Tanpa pengambilan ini, kolom sinopsis selalu tampil kosong dan penyimpanan
  // akan MENGHAPUS sinopsis yang sudah ada di basis data.
  useEffect(() => {
    if (!book) return
    let dibatalkan = false
    setIsLoadingSinopsis(true)
    api.get<ApiResponse<{ sinopsis: string | null }>>(`/books/${book.id}`)
      .then(res => { if (!dibatalkan) setSinopsis(res.data.data.sinopsis ?? '') })
      .catch(() => { if (!dibatalkan) toast.error('Gagal memuat sinopsis buku.') })
      .finally(() => { if (!dibatalkan) setIsLoadingSinopsis(false) })
    return () => { dibatalkan = true }
  }, [book])

  // Cleanup object URL saat komponen unmount atau file berubah
  useEffect(() => {
    return () => {
      if (coverPreview && coverPreview.startsWith('blob:')) {
        URL.revokeObjectURL(coverPreview)
      }
    }
  }, [coverPreview])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error('Hanya file JPG, PNG, atau WebP yang diizinkan.')
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Ukuran file maksimal 5 MB.')
      return
    }

    // Revoke previous blob URL kalau ada
    if (coverPreview?.startsWith('blob:')) URL.revokeObjectURL(coverPreview)

    setCoverFile(file)
    setCoverPreview(URL.createObjectURL(file))
  }

  const handleRemoveCover = () => {
    if (coverPreview?.startsWith('blob:')) URL.revokeObjectURL(coverPreview)
    setCoverFile(null)
    setCoverPreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!judul.trim() || !penulis.trim()) {
      toast.error('Judul dan penulis wajib diisi.')
      return
    }
    if (isLoadingSinopsis) {
      toast('Menunggu data buku selesai dimuat...')
      return
    }
    setIsLoading(true)

    try {
      // Upload cover dulu kalau ada file baru
      let finalCoverUrl: string | null = coverFile ? null : (coverPreview ?? null)
      if (coverFile) {
        const formData = new FormData()
        formData.append('cover', coverFile)
        const uploadRes = await api.post<ApiResponse<{ cover_url: string }>>(
          '/books/upload-cover',
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
        finalCoverUrl = uploadRes.data.data.cover_url
      }

      const payload = {
        judul: judul.trim(),
        penulis: penulis.trim(),
        isbn: isbn.trim() || null,
        sinopsis: sinopsis.trim() || null,
        cover_url: finalCoverUrl,
        stok_total: Number(stokTotal),
        kategori_id: Number(kategoriId),
      }

      if (book) {
        await api.put<ApiResponse<Book>>(`/books/${book.id}`, payload)
        toast.success('Buku berhasil diperbarui.')
      } else {
        await api.post<ApiResponse<Book>>('/books', payload)
        toast.success('Buku berhasil ditambahkan.')
      }
      onSuccess()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string } } }
      const message = axiosErr?.response?.data?.message
        ?? (book ? 'Gagal memperbarui buku.' : 'Gagal menambahkan buku.')
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {book ? 'Edit Buku' : 'Tambah Buku'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">

            {/* Cover upload */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Cover Buku</label>
              <div className="flex gap-4 items-start">
                {/* Preview */}
                <div
                  className="w-20 h-28 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center flex-shrink-0 overflow-hidden bg-gray-50"
                >
                  {coverPreview ? (
                    <img src={coverPreview} alt="Preview cover" className="w-full h-full object-cover" />
                  ) : (
                    <Image size={24} className="text-gray-300" />
                  )}
                </div>

                {/* Controls */}
                <div className="flex-1 space-y-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileChange}
                    className="hidden"
                    id="cover-file-input"
                  />
                  <label
                    htmlFor="cover-file-input"
                    className="flex items-center gap-2 px-3 py-2 text-sm font-semibold text-indigo-600 border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors cursor-pointer w-fit"
                  >
                    <Upload size={14} />
                    {coverPreview ? 'Ganti Foto' : 'Pilih Foto'}
                  </label>
                  {coverPreview && (
                    <button
                      type="button"
                      onClick={handleRemoveCover}
                      className="block text-xs font-semibold text-red-500 hover:text-red-700 transition-colors"
                    >
                      Hapus cover
                    </button>
                  )}
                  <p className="text-xs text-gray-400">JPG, PNG, WebP · Maks. 5 MB</p>
                  {coverFile && (
                    <p className="text-xs text-indigo-500 font-medium">✓ {coverFile.name}</p>
                  )}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Judul *</label>
              <input
                type="text"
                value={judul}
                onChange={(e) => setJudul(e.target.value)}
                required
                placeholder="Judul buku"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-gray-400"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Penulis *</label>
              <input
                type="text"
                value={penulis}
                onChange={(e) => setPenulis(e.target.value)}
                required
                placeholder="Nama penulis"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-gray-400"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">ISBN</label>
              <input
                type="text"
                value={isbn}
                onChange={(e) => setIsbn(e.target.value)}
                placeholder="ISBN (opsional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-gray-400"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Sinopsis</label>
              <textarea
                rows={3}
                value={sinopsis}
                onChange={(e) => setSinopsis(e.target.value)}
                placeholder="Deskripsi singkat buku (opsional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-gray-400 resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Stok Total *</label>
                <input
                  type="number"
                  min={1}
                  value={stokTotal}
                  onChange={(e) => setStokTotal(Number(e.target.value))}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Kategori *</label>
                <select
                  value={kategoriId}
                  onChange={(e) => setKategoriId(Number(e.target.value))}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.nama}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-100 flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Batalkan
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 text-sm font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {isLoading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Menyimpan...
                </>
              ) : 'Simpan Buku'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default BookFormModal
