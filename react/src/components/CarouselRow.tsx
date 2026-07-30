// Pembungkus baris kartu yang dapat digeser, dengan tombol panah kiri/kanan.
//
// Tanpa tombol, baris ini hanya bisa digeser dengan roda mendatar atau sapuan
// layar sentuh — sulit dilakukan pengguna desktop yang memakai mouse biasa.
//
// Tombol disembunyikan saat tidak ada yang bisa digeser ke arah tersebut, dan
// seluruhnya disembunyikan di layar kecil karena di sana sapuan jari sudah wajar.
import { useRef, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface CarouselRowProps {
  children: ReactNode
  /** Kelas tambahan untuk wadah yang menggulir (jarak antar kartu, padding). */
  className?: string
}

function CarouselRow({ children, className = '' }: CarouselRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [bisaKiri, setBisaKiri] = useState(false)
  const [bisaKanan, setBisaKanan] = useState(false)

  const perbaruiTombol = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    // Toleransi 4px: pembulatan subpiksel membuat scrollLeft tidak pernah
    // persis sama dengan batasnya, sehingga tombol bisa tampak aktif terus.
    setBisaKiri(el.scrollLeft > 4)
    setBisaKanan(el.scrollLeft + el.clientWidth < el.scrollWidth - 4)
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    perbaruiTombol()
    el.addEventListener('scroll', perbaruiTombol, { passive: true })

    // Kartu dimuat setelah data tiba, sehingga lebar isi berubah setelah
    // render pertama. ResizeObserver menjaga tombol tetap sesuai keadaan.
    const ro = new ResizeObserver(perbaruiTombol)
    ro.observe(el)
    Array.from(el.children).forEach(c => ro.observe(c))

    return () => {
      el.removeEventListener('scroll', perbaruiTombol)
      ro.disconnect()
    }
  }, [perbaruiTombol, children])

  const geser = (arah: 'kiri' | 'kanan') => {
    const el = scrollRef.current
    if (!el) return
    // Geser sebesar 80% lebar tampak agar selalu ada kartu yang tetap terlihat
    // sebagai penanda posisi.
    const jarak = el.clientWidth * 0.8
    el.scrollBy({ left: arah === 'kiri' ? -jarak : jarak, behavior: 'smooth' })
  }

  const gayaTombol: React.CSSProperties = {
    background: 'var(--bg-card)',
    border: '1.5px solid var(--border)',
    color: 'var(--text)',
    boxShadow: 'var(--shadow-md)',
  }

  return (
    <div className="relative">
      <div
        ref={scrollRef}
        className={`flex overflow-x-auto ${className}`}
        style={{ scrollSnapType: 'x mandatory', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none' }}
      >
        {children}
      </div>

      {bisaKiri && (
        <button
          onClick={() => geser('kiri')}
          aria-label="Geser ke kiri"
          className="hidden sm:flex absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 w-9 h-9 rounded-full items-center justify-center transition-transform duration-150 hover:scale-110"
          style={gayaTombol}
        >
          <ChevronLeft size={18} />
        </button>
      )}

      {bisaKanan && (
        <button
          onClick={() => geser('kanan')}
          aria-label="Geser ke kanan"
          className="hidden sm:flex absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10 w-9 h-9 rounded-full items-center justify-center transition-transform duration-150 hover:scale-110"
          style={gayaTombol}
        >
          <ChevronRight size={18} />
        </button>
      )}
    </div>
  )
}

export default CarouselRow
