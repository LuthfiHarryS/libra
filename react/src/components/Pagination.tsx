import { useState, useEffect, useRef } from 'react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

function getPageNumbers(currentPage: number, totalPages: number): (number | '...')[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }
  const pages: (number | '...')[] = [1]
  if (currentPage > 3) pages.push('...')
  const start = Math.max(2, currentPage - 1)
  const end = Math.min(totalPages - 1, currentPage + 1)
  for (let i = start; i <= end; i++) pages.push(i)
  if (currentPage < totalPages - 2) pages.push('...')
  pages.push(totalPages)
  return pages
}

function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  // Nilai kotak isian dipisahkan dari currentPage agar pengguna bisa mengetik
  // bebas — termasuk mengosongkannya sesaat — tanpa memicu perpindahan halaman.
  const [input, setInput] = useState(String(currentPage))
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { setInput(String(currentPage)) }, [currentPage])

  if (totalPages <= 1) return null

  const pages = getPageNumbers(currentPage, totalPages)

  const pindah = (tujuan: number) => {
    const n = Math.min(totalPages, Math.max(1, Math.round(tujuan)))
    if (n !== currentPage) onPageChange(n)
    setInput(String(n))
  }

  const terapkanInput = () => {
    const n = parseInt(input, 10)
    if (Number.isNaN(n)) {
      setInput(String(currentPage))   // kembalikan ke nilai sah bila tidak terbaca
      return
    }
    pindah(n)
  }

  // Roda mouse menaikkan/menurunkan nomor halaman. Dipasang lewat ref, bukan
  // atribut onWheel, karena React memasang listener wheel sebagai passive
  // sehingga preventDefault() di dalamnya diabaikan dan halaman ikut menggulir.
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      if (document.activeElement !== el) return
      e.preventDefault()
      pindah(currentPage + (e.deltaY < 0 ? 1 : -1))
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  })

  const btnBase: React.CSSProperties = {
    border: '1.5px solid var(--border)',
    background: 'var(--bg-card)',
    color: 'var(--text-2)',
    borderRadius: '999px',
    fontFamily: 'var(--font-ui)',
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'all 200ms',
  }

  return (
    <div className="mt-8 mb-8 flex flex-col items-center gap-3">
      <div className="flex items-center justify-center gap-1.5 flex-wrap">
        <button
          onClick={() => pindah(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          style={btnBase}
        >
          ← Sebelumnya
        </button>

        {pages.map((page, idx) =>
          page === '...' ? (
            <span key={`ellipsis-${idx}`} className="px-1 text-sm" style={{ color: 'var(--text-3)' }}>
              ...
            </span>
          ) : (
            <button
              key={page}
              onClick={() => pindah(page)}
              className="w-9 h-9 text-sm"
              style={page === currentPage
                ? { ...btnBase, background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' }
                : btnBase
              }
            >
              {page}
            </button>
          )
        )}

        <button
          onClick={() => pindah(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          style={btnBase}
        >
          Berikutnya →
        </button>
      </div>

      {/* Lompat ke halaman tertentu — diketik, ditekan panah atas/bawah, atau
          digulir dengan roda mouse saat kotak ini sedang aktif. */}
      <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-3)' }}>
        <label htmlFor="lompat-halaman" style={{ fontFamily: 'var(--font-ui)' }}>
          Ke halaman
        </label>
        <input
          ref={inputRef}
          id="lompat-halaman"
          type="number"
          min={1}
          max={totalPages}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') { e.preventDefault(); terapkanInput() }
            if (e.key === 'ArrowUp')   { e.preventDefault(); pindah(currentPage + 1) }
            if (e.key === 'ArrowDown') { e.preventDefault(); pindah(currentPage - 1) }
          }}
          onBlur={terapkanInput}
          onFocus={e => e.currentTarget.select()}
          aria-label={`Nomor halaman, 1 sampai ${totalPages}`}
          className="w-16 px-2 py-1.5 text-sm text-center"
          style={{
            border: '1.5px solid var(--border)',
            background: 'var(--bg-input)',
            color: 'var(--text)',
            borderRadius: '999px',
            fontFamily: 'var(--font-ui)',
            fontWeight: 700,
            outline: 'none',
          }}
        />
        <span style={{ fontFamily: 'var(--font-ui)' }}>dari {totalPages}</span>
        <button
          onClick={terapkanInput}
          className="px-3 py-1.5 text-sm"
          style={{ ...btnBase, color: 'var(--accent)', borderColor: 'var(--accent)' }}
        >
          Buka
        </button>
      </div>
    </div>
  )
}

export default Pagination
