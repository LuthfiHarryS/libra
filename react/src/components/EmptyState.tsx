import { BookX } from 'lucide-react'

interface EmptyStateProps {
  onReset: () => void
}

function EmptyState({ onReset }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center col-span-full">
      <BookX size={64} style={{ color: 'var(--text-3)' }} />
      <h3 className="text-lg font-extrabold mt-4" style={{ color: 'var(--text-2)' }}>Buku tidak ditemukan</h3>
      <p className="text-sm mt-2" style={{ color: 'var(--text-3)' }}>Tidak ada buku yang cocok dengan pencarianmu.</p>
      <button
        onClick={onReset}
        className="mt-4 px-5 py-2.5 text-sm font-bold rounded-full border-2 transition-all duration-200"
        style={{ borderColor: 'var(--accent)', color: 'var(--accent)', background: 'transparent' }}
        onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent-soft)' }}
        onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
      >
        Reset Pencarian
      </button>
    </div>
  )
}

export default EmptyState
