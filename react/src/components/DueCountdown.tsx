// "5 hari lagi" / "Hari ini!" / "Telat 2 hari!"
// Default durasi pinjam 7 hari sejak tanggal_approve.
// Tampil hanya untuk status Dipinjam.
import { CalendarClock, AlertTriangle } from 'lucide-react'

export const BORROW_DURATION_DAYS = 7

type Variant = 'safe' | 'warning' | 'urgent' | 'overdue'

function parseDate(mysqlDate: string): Date {
  return new Date(mysqlDate.replace(' ', 'T'))
}

function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}

function diffInDays(target: Date, from: Date): number {
  const ms = startOfDay(target).getTime() - startOfDay(from).getTime()
  return Math.round(ms / 86_400_000)
}

function pickVariant(daysLeft: number): Variant {
  if (daysLeft < 0)  return 'overdue'
  if (daysLeft <= 1) return 'urgent'
  if (daysLeft <= 3) return 'warning'
  return 'safe'
}

const PALETTE: Record<Variant, { bg: string; fg: string; border: string }> = {
  safe:    { bg: 'var(--avail-bg)',         fg: 'var(--avail)',          border: 'var(--avail)' },
  warning: { bg: 'var(--chip-pending-bg)',  fg: 'var(--chip-pending-tx)', border: 'var(--chip-pending-tx)' },
  urgent:  { bg: 'rgba(234,88,12,.12)',     fg: '#c2410c',                border: '#ea580c' },
  overdue: { bg: 'var(--unavail-bg)',       fg: 'var(--unavail)',         border: 'var(--unavail)' },
}

function buildLabel(daysLeft: number, dueDate: Date): string {
  const due = dueDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
  if (daysLeft < 0)   return `Telat ${Math.abs(daysLeft)} hari! (jatuh tempo ${due})`
  if (daysLeft === 0) return `Harus dikembalikan hari ini (${due})`
  if (daysLeft === 1) return `Besok jatuh tempo (${due})`
  return `${daysLeft} hari lagi (jatuh tempo ${due})`
}

function DueCountdown({ tanggalApprove }: { tanggalApprove: string | null }) {
  if (!tanggalApprove) return null

  const approveDate = parseDate(tanggalApprove)
  const dueDate     = new Date(approveDate)
  dueDate.setDate(dueDate.getDate() + BORROW_DURATION_DAYS)

  const daysLeft = diffInDays(dueDate, new Date())
  const variant  = pickVariant(daysLeft)
  const palette  = PALETTE[variant]
  const isAlert  = variant === 'urgent' || variant === 'overdue'

  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] font-extrabold px-2.5 py-1 rounded-full mt-1"
      style={{ background: palette.bg, color: palette.fg, border: `1px solid ${palette.border}` }}
      title={`Jatuh tempo: ${dueDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })}`}
    >
      {isAlert ? <AlertTriangle size={11} /> : <CalendarClock size={11} />}
      {buildLabel(daysLeft, dueDate)}
    </span>
  )
}

export default DueCountdown
