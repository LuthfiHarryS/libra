// Admin layout nav. Desktop: fixed left sidebar (w-64). Mobile: off-canvas
// drawer toggled by a top bar hamburger, with backdrop.
// Active link detection: useLocation().pathname.startsWith(path)
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { LayoutDashboard, BookOpen, BookMarked, LibraryBig, LogOut, Menu, X } from 'lucide-react'
import useAuthStore from '../store/authStore'

const NAV_LINKS = [
  { to: '/admin/dashboard', label: 'Dashboard',       icon: LayoutDashboard },
  { to: '/admin/buku',      label: 'Kelola Buku',     icon: BookOpen        },
  { to: '/admin/pinjaman',  label: 'Kelola Pinjaman', icon: BookMarked      },
]

function AdminSidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const [open, setOpen] = useState(false)

  const handleLogout = () => {
    setOpen(false)
    logout()
    navigate('/login')
  }

  const isActive = (path: string) => location.pathname.startsWith(path)

  return (
    <>
      {/* Mobile top bar — hamburger di kiri (drawer keluar dari kiri) */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-gray-900 flex items-center gap-3 px-4 z-30">
        <button
          onClick={() => setOpen(true)}
          aria-label="Buka menu"
          className="p-2 -ml-2 text-gray-200 hover:text-white"
        >
          <Menu size={22} />
        </button>
        <div className="flex items-baseline gap-2">
          <span className="text-white text-lg font-bold">LIBRA</span>
          <span className="text-gray-400 text-xs">Admin Panel</span>
        </div>
      </div>

      {/* Backdrop (mobile, when drawer open) */}
      {open && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar / drawer */}
      <aside
        className={`w-64 fixed top-0 left-0 h-screen bg-gray-900 flex flex-col z-50 transition-transform duration-300 ${
          open ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0`}
      >
        {/* Logo area */}
        <div className="px-4 py-6 border-b border-gray-700 flex items-start justify-between">
          <div>
            <p className="text-white text-lg font-bold">LIBRA</p>
            <p className="text-gray-400 text-xs mt-0.5">Admin Panel</p>
          </div>
          {/* Close button (mobile only) */}
          <button
            onClick={() => setOpen(false)}
            aria-label="Tutup menu"
            className="md:hidden p-1 text-gray-400 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_LINKS.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={`flex items-center gap-3 px-3 py-2 text-sm font-semibold rounded-lg transition-colors ${
                isActive(to)
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}

          {/* Lihat katalog publik — tetap login, tidak keluar dari CMS */}
          <div className="pt-2 mt-2 border-t border-gray-700">
            <Link
              to="/katalog"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-3 py-2 text-sm font-semibold rounded-lg transition-colors text-gray-300 hover:bg-gray-700 hover:text-white"
            >
              <LibraryBig size={18} />
              Lihat Katalog
            </Link>
          </div>
        </nav>

        {/* Keluar button */}
        <div className="px-3 py-4 border-t border-gray-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 w-full text-sm font-semibold text-gray-300 hover:text-red-400 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            Keluar
          </button>
        </div>
      </aside>
    </>
  )
}

export default AdminSidebar
