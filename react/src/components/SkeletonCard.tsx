function SkeletonCard() {
  return (
    <div
      className="overflow-hidden"
      style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border)', borderRadius: '16px', boxShadow: 'var(--shadow-sm)' }}
    >
      <div className="w-full aspect-[3/4] animate-pulse" style={{ background: 'var(--bg-subtle)' }} />
      <div className="p-4 space-y-2">
        <div className="h-3 rounded-full animate-pulse w-4/5" style={{ background: 'var(--bg-subtle)' }} />
        <div className="h-3 rounded-full animate-pulse w-3/5" style={{ background: 'var(--bg-subtle)' }} />
        <div className="h-3 rounded-full animate-pulse w-2/5" style={{ background: 'var(--bg-subtle)' }} />
      </div>
    </div>
  )
}

export default SkeletonCard
