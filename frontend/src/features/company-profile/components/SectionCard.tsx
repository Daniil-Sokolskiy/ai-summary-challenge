'use client'

import { AlertCircle } from 'lucide-react'
import { useProfileSection } from '../hooks/useProfileSection'
import { SECTION_TITLES, type ProfileSection } from '../types'
import { SectionTable } from './SectionTable'
import { Skeleton } from './Skeleton'

interface SectionCardProps {
  inn: string
  section: ProfileSection
  /** Сколько строк показать. Не задан — показываем все (режим отдельной вкладки). */
  limit?: number
}

export function SectionCard({ inn, section, limit }: SectionCardProps) {
  const { data, isLoading, isError, refetch } = useProfileSection(inn, section)

  return (
    <section className='rounded-card border border-line bg-white p-5'>
      <div className='mb-4 flex items-baseline justify-between gap-3'>
        <h2 className='text-base font-semibold text-ink'>{SECTION_TITLES[section]}</h2>
        {data && (
          <span className='shrink-0 text-sm text-ink-muted'>
            {data.total > 0 ? `Всего: ${data.total}` : 'Нет записей'}
          </span>
        )}
      </div>

      {isLoading && (
        <div className='space-y-2'>
          <Skeleton className='h-8 w-full rounded' />
          <Skeleton className='h-8 w-full rounded' />
          <Skeleton className='h-8 w-3/4 rounded' />
        </div>
      )}

      {isError && (
        <div className='flex items-center gap-3 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700'>
          <AlertCircle className='h-4 w-4 shrink-0' />
          <span className='flex-1'>Не удалось загрузить раздел</span>
          <button
            type='button'
            onClick={() => refetch()}
            className='font-semibold underline underline-offset-2'
          >
            Повторить
          </button>
        </div>
      )}

      {data && <SectionTable items={data.items} limit={limit} />}

      {data && limit !== undefined && data.total > limit && (
        <p className='mt-3 text-sm text-ink-muted'>
          Показаны первые {limit} из {data.total}. Полный список — на вкладке «
          {SECTION_TITLES[section]}».
        </p>
      )}
    </section>
  )
}
