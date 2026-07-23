// UI-SPEC §NotFoundPage Layout
// lucide FileQuestion icon 80px text-gray-300
// "404" text-6xl, heading text-xl, body text-sm
// Primary button "Kembali ke Katalog"
import { useNavigate } from 'react-router'
import { FileQuestion } from 'lucide-react'

function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <FileQuestion size={80} className="text-gray-300" />
      <h1 className="text-6xl font-bold text-gray-200 mt-4">404</h1>
      <h2 className="text-xl font-semibold text-gray-600 mt-2">Halaman tidak ditemukan</h2>
      <p className="text-sm text-gray-400 mt-2 text-center">
        Halaman yang kamu cari tidak ada atau sudah dipindah.
      </p>
      <button
        onClick={() => navigate('/katalog')}
        className="mt-6 px-4 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 active:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors duration-150"
      >
        Kembali ke Katalog
      </button>
    </div>
  )
}

export default NotFoundPage
