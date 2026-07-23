import { useState } from 'react'
import { NavLink, useNavigate, Link } from 'react-router'
import { Sun, Moon, Menu, X } from 'lucide-react'
import useAuthStore from '../store/authStore'
import useTheme from '../hooks/useTheme'
import NotificationBell from './NotificationBell'

function Navbar() {
  const logout = useAuthStore((state) => state.logout)
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = () => {
    setMenuOpen(false)
    logout()
    navigate('/katalog')
  }

  const closeMenu = () => setMenuOpen(false)

  const initials = user?.nama
    ? user.nama.split(' ').map((n: string) => n[0]).slice(0, 2).join('').toUpperCase()
    : 'U'

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3.5 py-1.5 rounded-full text-sm font-bold transition-all duration-200 ${
      isActive
        ? 'bg-[var(--accent-soft)] text-[var(--accent)]'
        : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--bg-subtle)]'
    }`

  const mobileLinkClass = ({ isActive }: { isActive: boolean }) =>
    `block px-4 py-3 rounded-xl text-sm font-bold transition-all duration-200 ${
      isActive
        ? 'bg-[var(--accent-soft)] text-[var(--accent)]'
        : 'text-[var(--text-2)] hover:bg-[var(--bg-subtle)]'
    }`

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 h-[60px] border-b flex items-center px-4 md:px-6"
      style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)', backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)' }}
    >
      {/* Logo */}
      <Link to="/katalog" onClick={closeMenu} style={{ fontFamily: 'var(--font-display)', color: 'var(--accent)', fontSize: '22px', fontWeight: 800, letterSpacing: '-0.5px', flexShrink: 0 }}>
        LIBRA
      </Link>

      {/* Desktop nav links */}
      <div className="hidden md:flex items-center gap-1 ml-6 flex-1">
        <NavLink to="/katalog" className={navLinkClass}>Katalog</NavLink>
        {isAuthenticated && user?.role === 'siswa' && (
          <>
            <NavLink to="/favorit" className={navLinkClass}>Favorit</NavLink>
            <NavLink to="/pinjaman" className={navLinkClass}>Pinjaman Saya</NavLink>
          </>
        )}
        {isAuthenticated && user?.role === 'admin' && (
          <NavLink to="/admin/dashboard" className={navLinkClass}>Panel Admin</NavLink>
        )}
      </div>

      {/* Spacer pushes right-side items to the edge on mobile */}
      <div className="flex-1 md:hidden" />

      {/* Right side */}
      <div className="flex items-center gap-1.5 md:gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggle}
          aria-label="Toggle tema"
          className="p-2 rounded-full transition-all duration-200 hover:bg-[var(--bg-subtle)]"
          style={{ color: 'var(--text-3)' }}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>

        {/* NotificationBell — siswa only, visible on all sizes */}
        {isAuthenticated && user?.role === 'siswa' && <NotificationBell />}

        {/* Desktop auth actions */}
        <div className="hidden md:flex items-center gap-2">
          {isAuthenticated ? (
            <>
              {user?.role === 'siswa' ? (
                <Link
                  to="/profil"
                  className="flex items-center gap-2 rounded-full px-3 py-1 border transition-all duration-200"
                  style={{ background: 'var(--bg-subtle)', borderColor: 'var(--border)' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--accent)' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border)' }}
                  title="Buka profil saya"
                >
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-extrabold text-white flex-shrink-0"
                    style={{ background: 'linear-gradient(135deg, var(--accent) 0%, var(--brand) 100%)' }}
                  >
                    {initials}
                  </div>
                  <span className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                    {user?.nama?.split(' ')[0] || 'Pengguna'}
                  </span>
                </Link>
              ) : (
                <Link
                  to="/admin/dashboard"
                  className="flex items-center gap-2 rounded-full px-3 py-1 border transition-all duration-200"
                  style={{ background: 'var(--bg-subtle)', borderColor: 'var(--border)' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--accent)' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border)' }}
                  title="Buka panel admin"
                >
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-extrabold text-white flex-shrink-0"
                    style={{ background: 'linear-gradient(135deg, var(--accent) 0%, var(--brand) 100%)' }}
                  >
                    {initials}
                  </div>
                  <span className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                    {user?.nama?.split(' ')[0] || 'Pengguna'}
                  </span>
                </Link>
              )}
              <button
                onClick={handleLogout}
                className="text-sm font-bold px-3 py-1.5 rounded-lg transition-all duration-200"
                style={{ color: 'var(--text-3)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--unavail)'; (e.currentTarget as HTMLButtonElement).style.background = 'var(--unavail-bg)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-3)'; (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
              >
                Keluar
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm font-bold px-4 py-1.5 rounded-full border-2 transition-all duration-200"
                style={{ borderColor: 'var(--accent)', color: 'var(--accent)', background: 'transparent' }}
                onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'var(--accent-soft)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'transparent' }}
              >
                Masuk
              </Link>
              <Link
                to="/daftar"
                className="text-sm font-bold px-4 py-1.5 rounded-full text-white transition-all duration-200"
                style={{ background: 'var(--accent)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'var(--accent-h)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'var(--accent)' }}
              >
                Daftar
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen(o => !o)}
          aria-label={menuOpen ? 'Tutup menu' : 'Buka menu'}
          aria-expanded={menuOpen}
          className="md:hidden p-2 rounded-full transition-all duration-200 hover:bg-[var(--bg-subtle)]"
          style={{ color: 'var(--text-2)' }}
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <div
          className="md:hidden absolute top-full left-0 right-0 border-b flex flex-col gap-1 px-3 py-3"
          style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)', boxShadow: 'var(--shadow-lg)', backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)' }}
        >
          <NavLink to="/katalog" onClick={closeMenu} className={mobileLinkClass}>Katalog</NavLink>
          {isAuthenticated && user?.role === 'siswa' && (
            <>
              <NavLink to="/favorit" onClick={closeMenu} className={mobileLinkClass}>Favorit</NavLink>
              <NavLink to="/pinjaman" onClick={closeMenu} className={mobileLinkClass}>Pinjaman Saya</NavLink>
              <NavLink to="/profil" onClick={closeMenu} className={mobileLinkClass}>Profil Saya</NavLink>
            </>
          )}
          {isAuthenticated && user?.role === 'admin' && (
            <NavLink to="/admin/dashboard" onClick={closeMenu} className={mobileLinkClass}>Panel Admin</NavLink>
          )}

          <div className="border-t my-1" style={{ borderColor: 'var(--border)' }} />

          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="block text-left px-4 py-3 rounded-xl text-sm font-bold transition-all duration-200"
              style={{ color: 'var(--unavail)' }}
            >
              Keluar
            </button>
          ) : (
            <div className="flex flex-col gap-2 px-1 pt-1">
              <Link
                to="/login"
                onClick={closeMenu}
                className="text-sm font-bold px-4 py-2.5 rounded-xl border-2 text-center transition-all duration-200"
                style={{ borderColor: 'var(--accent)', color: 'var(--accent)', background: 'transparent' }}
              >
                Masuk
              </Link>
              <Link
                to="/daftar"
                onClick={closeMenu}
                className="text-sm font-bold px-4 py-2.5 rounded-xl text-white text-center transition-all duration-200"
                style={{ background: 'var(--accent)' }}
              >
                Daftar
              </Link>
            </div>
          )}
        </div>
      )}
    </nav>
  )
}

export default Navbar
