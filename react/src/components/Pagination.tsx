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
  if (totalPages <= 1) return null

  const pages = getPageNumbers(currentPage, totalPages)

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
    <div className="flex items-center justify-center gap-1.5 mt-8 mb-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
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
            onClick={() => onPageChange(page)}
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
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
        style={btnBase}
      >
        Berikutnya →
      </button>
    </div>
  )
}

export default Pagination
