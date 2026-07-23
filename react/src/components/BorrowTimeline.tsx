// Visual progress untuk siklus peminjaman:
//   Diajukan → Disetujui → Dipinjam → Dikembalikan
//   atau Diajukan → Ditolak
// Stage di-derive dari status + tanggal field.
import { Clock, CheckCircle2, BookOpen, PackageCheck, XCircle } from 'lucide-react'
import type { BorrowItem } from '../types'

type Stage = {
  key: string
  label: string
  Icon: typeof Clock
  done: boolean
  active: boolean
  rejected?: boolean
}

function buildStages(item: BorrowItem): Stage[] {
  const isPending      = item.status === 'Pending'
  const isApproved     = item.status === 'Dipinjam'
  const isReturned     = item.status === 'Dikembalikan'
  const isRejected     = item.status === 'Ditolak'

  if (isRejected) {
    return [
      { key: 'diajukan', label: 'Diajukan',  Icon: Clock,    done: true, active: false },
      { key: 'ditolak',  label: 'Ditolak',   Icon: XCircle,  done: true, active: true, rejected: true },
    ]
  }

  return [
    { key: 'diajukan',     label: 'Diajukan',     Icon: Clock,         done: true,                    active: isPending },
    { key: 'disetujui',    label: 'Disetujui',    Icon: CheckCircle2,  done: isApproved || isReturned, active: false },
    { key: 'dipinjam',     label: 'Dipinjam',     Icon: BookOpen,      done: isReturned,              active: isApproved },
    { key: 'dikembalikan', label: 'Dikembalikan', Icon: PackageCheck,  done: isReturned,              active: isReturned },
  ]
}

function BorrowTimeline({ item }: { item: BorrowItem }) {
  const stages = buildStages(item)

  return (
    <div className="flex items-center w-full" role="list" aria-label="Status peminjaman">
      {stages.map((stage, idx) => {
        const { Icon } = stage
        const isLast = idx === stages.length - 1

        const dotColor   = stage.rejected
          ? 'var(--unavail)'
          : stage.done
            ? 'var(--accent)'
            : stage.active
              ? 'var(--accent)'
              : 'var(--border)'

        const iconColor  = stage.done || stage.active ? '#fff' : 'var(--text-3)'
        const labelColor = stage.rejected
          ? 'var(--unavail)'
          : stage.done || stage.active
            ? 'var(--text)'
            : 'var(--text-3)'

        const lineColor = stages[idx + 1]?.done || stages[idx + 1]?.active
          ? 'var(--accent)'
          : 'var(--border)'

        return (
          <div key={stage.key} className="flex items-center flex-1 last:flex-none" role="listitem">
            <div className="flex flex-col items-center min-w-0">
              <div
                className="rounded-full flex items-center justify-center transition-colors"
                style={{
                  width: 32,
                  height: 32,
                  background: dotColor,
                  border: stage.done || stage.active ? 'none' : '2px solid var(--border)',
                  boxShadow: stage.active ? '0 0 0 4px rgba(217,119,6,.15)' : 'none',
                }}
                aria-current={stage.active ? 'step' : undefined}
              >
                <Icon size={16} style={{ color: iconColor }} />
              </div>
              <span
                className="text-[10px] font-extrabold mt-1 text-center whitespace-nowrap"
                style={{ color: labelColor, letterSpacing: '.02em' }}
              >
                {stage.label}
              </span>
            </div>
            {!isLast && (
              <div
                className="flex-1 h-[2px] mx-1 mb-4 transition-colors"
                style={{ background: lineColor }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

export default BorrowTimeline
