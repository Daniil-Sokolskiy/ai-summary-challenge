import { Building2 } from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'
import type { CompanySummary } from '../types'

interface HeroSectionProps {
  summary: CompanySummary
}

function statusClass(status: string): string {
  const lowered = status.toLowerCase()
  if (lowered.startsWith('действ')) return 'bg-emerald-50 text-emerald-700 ring-emerald-200'
  if (lowered.startsWith('ликвид')) return 'bg-red-50 text-red-700 ring-red-200'
  return 'bg-amber-50 text-amber-700 ring-amber-200'
}

export function HeroSection({ summary }: HeroSectionProps) {
  return (
    <header className='rounded-card border border-line bg-white p-6'>
      <div className='flex items-start gap-4'>
        <div className='flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-surface text-ink-muted'>
          <Building2 className='h-6 w-6' />
        </div>

        <div className='min-w-0 flex-1'>
          <div className='mb-2 flex flex-wrap items-center gap-3'>
            <h1 className='text-xl font-semibold text-ink sm:text-2xl'>{summary.name}</h1>
            <span
              className={cn(
                'rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset',
                statusClass(summary.status)
              )}
            >
              {summary.status}
            </span>
          </div>

          <dl className='flex flex-wrap gap-x-6 gap-y-1 text-sm text-ink-soft'>
            <div className='flex gap-1.5'>
              <dt className='text-ink-muted'>ИНН:</dt>
              <dd className='font-medium text-ink'>{summary.inn}</dd>
            </div>
            {summary.city && (
              <div className='flex gap-1.5'>
                <dt className='text-ink-muted'>Город:</dt>
                <dd>{summary.city}</dd>
              </div>
            )}
            <div className='flex gap-1.5'>
              <dt className='text-ink-muted'>Регистрация:</dt>
              <dd>{formatDate(summary.registrationDate)}</dd>
            </div>
          </dl>

          {summary.mainOkvedCode && (
            <p className='mt-3 text-sm text-ink-muted'>
              Основной вид деятельности:{' '}
              <span className='text-ink-soft'>
                {summary.mainOkvedCode} — {summary.mainOkvedName}
              </span>
            </p>
          )}
        </div>
      </div>
    </header>
  )
}
