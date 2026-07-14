import { formatMoney, formatNumber } from '@/lib/utils'
import type { CompanySummary } from '../types'

interface StatCardProps {
  label: string
  value: string
  hint?: string
}

function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className='rounded-card border border-line bg-white p-4'>
      <div className='text-xs uppercase tracking-wide text-ink-muted'>{label}</div>
      <div className='mt-1.5 text-lg font-semibold text-ink'>{value}</div>
      {hint && <div className='mt-0.5 text-xs text-ink-muted'>{hint}</div>}
    </div>
  )
}

interface StatCardsProps {
  summary: CompanySummary
}

export function StatCards({ summary }: StatCardsProps) {
  const profitHint =
    summary.profit !== null && summary.profit < 0 ? 'Убыток по итогам года' : undefined

  return (
    <div className='grid grid-cols-1 gap-3 sm:grid-cols-3'>
      <StatCard label='Выручка' value={formatMoney(summary.revenue)} hint='За последний год' />
      <StatCard label='Прибыль' value={formatMoney(summary.profit)} hint={profitHint} />
      <StatCard label='Сотрудников' value={formatNumber(summary.headcount)} hint='По данным ФНС' />
    </div>
  )
}
