// Dashboard stat card — label + numeric value + icon
// Per UI-SPEC §AdminDashboardPage Stat Cards
// Icon color controlled by caller via className on the icon element
import type { ReactNode } from 'react'

interface StatCardProps {
  label: string
  value: number | string
  icon: ReactNode
}

function StatCard({ label, value, icon }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl p-4 md:p-6 shadow-sm border border-gray-200 flex items-center gap-3 md:gap-4 min-w-0">
      <div className="flex-shrink-0">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs md:text-sm font-semibold text-gray-500">{label}</p>
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  )
}

export default StatCard
