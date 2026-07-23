// Verified against PHP API controllers (Phase 2 + 4)

// From GET /api/books items — NOTE: no sinopsis in list response
export interface Book {
  id: number
  judul: string
  penulis: string
  isbn: string | null
  cover_url: string | null
  stok_total: number
  stok_tersedia: number
  created_at: string
  kategori_id: number
  kategori_nama: string
  is_favorite?: boolean
}

// From GET /api/books/:id — extends Book with sinopsis
export interface BookDetail extends Book {
  sinopsis: string | null
  updated_at: string
}

// From GET /api/borrow/status items
export interface BorrowItem {
  id: number
  buku_id: number
  judul: string
  penulis: string
  cover_url: string | null
  status: 'Pending' | 'Dipinjam' | 'Dikembalikan' | 'Ditolak'
  tanggal_pinjam: string
  tanggal_approve: string | null
  tanggal_reject: string | null
  tanggal_kembali: string | null
}

// From POST /api/auth/login data.user
export interface AuthUser {
  id: number
  nama: string
  username: string
  role: string
}

// Generic PHP response envelope — all endpoints use this
export interface ApiResponse<T> {
  success: boolean
  data: T
  message: string
}

// For GET /api/books pagination wrapper
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// From GET /api/categories
export interface Category {
  id: number
  nama: string
}

// Phase 7: Admin borrow record — includes user info + all admin date fields
export interface AdminBorrowItem {
  id: number
  user_id: number
  user_nama: string
  buku_id: number
  judul: string
  penulis: string
  status: 'Pending' | 'Dipinjam' | 'Dikembalikan' | 'Ditolak'
  tanggal_pinjam: string
  tanggal_kembali: string | null
  tanggal_approve: string | null
  tanggal_reject: string | null
}

// Phase 7: GET /api/admin/dashboard response shape
export interface TopBook {
  id: number
  judul: string
  penulis: string
  borrow_count: number
}

export interface OverdueBorrow {
  id: number
  user_nama: string
  judul: string
  tanggal_approve: string
  days_overdue: number
}

export interface DashboardStats {
  total_buku: number
  pinjaman_aktif: number
  pending_count: number
  total_siswa: number
  top_books: TopBook[]
  overdue: OverdueBorrow[]
}

// Phase 7: GET /api/settings/logo response shape
export interface LogoSettings {
  logo_url: string | null
}

// Phase 7: ChatWidget message type (in-memory only)
export interface ChatMessage {
  role: 'user' | 'bot'
  text: string
}

// P3 — Notifikasi in-app. id boleh integer (persisted) atau string "reminder-N" (dinamis).
export interface NotificationItem {
  id: number | string
  type: 'approved' | 'rejected' | 'returned' | 'info'
  title: string
  body: string | null
  link_url: string | null
  is_read: boolean
  created_at: string
}

export interface NotificationsResponse {
  items: NotificationItem[]
  unread: number
}

// P3 — Statistik profile
export interface ProfileStats {
  total_pinjam: number
  total_active: number
  total_returned: number
  total_favorit: number
  top_kategori: string | null
}
