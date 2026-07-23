// Bell + dropdown panel berisi 20 notif terakhir.
// Polling: tiap 30 detik + saat window focus.
import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router'
import { Bell, CheckCheck, BookOpen, BookX, PackageCheck, AlertTriangle } from 'lucide-react'
import api from '../services/api'
import type { NotificationItem, NotificationsResponse, ApiResponse } from '../types'

const POLL_INTERVAL_MS = 30_000

function relativeTime(mysqlDate: string): string {
  const d = new Date(mysqlDate.replace(' ', 'T'))
  const diffSec = Math.max(0, (Date.now() - d.getTime()) / 1000)
  if (diffSec < 60)        return 'baru saja'
  if (diffSec < 3600)      return `${Math.floor(diffSec / 60)} menit lalu`
  if (diffSec < 86400)     return `${Math.floor(diffSec / 3600)} jam lalu`
  if (diffSec < 7 * 86400) return `${Math.floor(diffSec / 86400)} hari lalu`
  return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
}

function iconFor(type: NotificationItem['type']) {
  switch (type) {
    case 'approved': return { Icon: BookOpen,     color: 'var(--accent)' }
    case 'rejected': return { Icon: BookX,        color: 'var(--unavail)' }
    case 'returned': return { Icon: PackageCheck, color: 'var(--avail)' }
    case 'info':     return { Icon: AlertTriangle, color: '#c2410c' }
  }
}

function NotificationBell() {
  const navigate = useNavigate()
  const [open, setOpen]       = useState(false)
  const [items, setItems]     = useState<NotificationItem[]>([])
  const [unread, setUnread]   = useState(0)
  const panelRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const fetchNotifs = useCallback(() => {
    api.get<ApiResponse<NotificationsResponse>>('/notifications', { params: { limit: 20 } })
      .then(res => {
        setItems(res.data.data.items)
        setUnread(res.data.data.unread)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    fetchNotifs()
    const id = setInterval(fetchNotifs, POLL_INTERVAL_MS)
    const onFocus = () => fetchNotifs()
    window.addEventListener('focus', onFocus)
    return () => {
      clearInterval(id)
      window.removeEventListener('focus', onFocus)
    }
  }, [fetchNotifs])

  // Tutup panel saat klik di luar
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (
        panelRef.current && !panelRef.current.contains(e.target as Node) &&
        buttonRef.current && !buttonRef.current.contains(e.target as Node)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const handleClickItem = async (item: NotificationItem) => {
    if (!item.is_read && typeof item.id === 'number') {
      try { await api.post('/notifications/mark-read', { ids: [item.id] }) } catch {}
    }
    setOpen(false)
    if (item.link_url) navigate(item.link_url)
    fetchNotifs()
  }

  const handleMarkAll = async () => {
    try {
      await api.post('/notifications/mark-read', { ids: [] })
      fetchNotifs()
    } catch {}
  }

  // Reminder due-date (id string "reminder-N") tidak bisa ditandai dibaca —
  // hilang sendiri saat buku dikembalikan. "Tandai semua" hanya relevan kalau
  // ada notif asli (id integer) yang belum dibaca.
  const hasUnreadReal = items.some(i => typeof i.id === 'number' && !i.is_read)

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setOpen(o => !o)}
        aria-label={unread > 0 ? `${unread} notifikasi baru` : 'Notifikasi'}
        className="relative p-2 rounded-full transition-all duration-200 hover:bg-[var(--bg-subtle)]"
        style={{ color: 'var(--text-3)' }}
      >
        <Bell size={18} />
        {unread > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 text-[10px] font-extrabold rounded-full px-1.5 py-0 flex items-center justify-center"
            style={{
              background: 'var(--unavail)',
              color: '#fff',
              minWidth: 18,
              height: 18,
              border: '2px solid var(--nav-bg)',
            }}
          >
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          ref={panelRef}
          className="absolute right-0 mt-2 z-50 overflow-hidden flex flex-col"
          style={{
            width: 360,
            maxHeight: 'min(70vh, 480px)',
            background: 'var(--bg-card)',
            border: '1.5px solid var(--border)',
            borderRadius: '16px',
            boxShadow: 'var(--shadow-lg)',
          }}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b flex-shrink-0" style={{ borderColor: 'var(--border)' }}>
            <p className="text-sm font-extrabold" style={{ color: 'var(--text)' }}>
              Notifikasi {unread > 0 && <span style={{ color: 'var(--accent)' }}>({unread})</span>}
            </p>
            {hasUnreadReal && (
              <button
                onClick={handleMarkAll}
                className="text-xs font-bold flex items-center gap-1 transition-colors"
                style={{ color: 'var(--accent)' }}
              >
                <CheckCheck size={12} />
                Tandai semua
              </button>
            )}
          </div>

          <div className="overflow-y-auto flex-1">
            {items.length === 0 ? (
              <div className="text-center py-10 px-4">
                <Bell size={32} className="mx-auto opacity-30 mb-2" style={{ color: 'var(--text-3)' }} />
                <p className="text-sm font-bold" style={{ color: 'var(--text-2)' }}>
                  Belum ada notifikasi
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-3)' }}>
                  Update peminjaman akan muncul di sini.
                </p>
              </div>
            ) : (
              items.map(item => {
                const { Icon, color } = iconFor(item.type)
                return (
                  <button
                    key={item.id}
                    onClick={() => handleClickItem(item)}
                    className="w-full text-left flex gap-3 px-4 py-3 border-b transition-colors"
                    style={{
                      borderColor: 'var(--border)',
                      background: item.is_read ? 'transparent' : 'var(--accent-soft)',
                    }}
                    onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-subtle)' }}
                    onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = item.is_read ? 'transparent' : 'var(--accent-soft)' }}
                  >
                    <div
                      className="flex-shrink-0 rounded-full flex items-center justify-center"
                      style={{ width: 32, height: 32, background: 'var(--bg-card)', border: `1.5px solid ${color}` }}
                    >
                      <Icon size={14} style={{ color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-extrabold leading-snug" style={{ color: 'var(--text)' }}>
                        {item.title}
                      </p>
                      {item.body && (
                        <p className="text-xs mt-0.5 line-clamp-2" style={{ color: 'var(--text-3)' }}>
                          {item.body}
                        </p>
                      )}
                      <p className="text-[10px] font-bold mt-1" style={{ color: 'var(--text-3)' }}>
                        {relativeTime(item.created_at)}
                      </p>
                    </div>
                    {!item.is_read && (
                      <span
                        className="flex-shrink-0 self-center rounded-full"
                        style={{ width: 8, height: 8, background: 'var(--accent)' }}
                        aria-label="Belum dibaca"
                      />
                    )}
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationBell
