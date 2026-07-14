'use client'

import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { HeroSection } from './components/HeroSection'
import { Skeleton } from './components/Skeleton'
import { StatCards } from './components/StatCards'
import { useSummaryData } from './hooks/useSummaryData'
import { SectionTab } from './SectionTab'
import { SummaryTab } from './SummaryTab'
import {
  PROFILE_SECTIONS,
  SECTION_COUNT_KEYS,
  SECTION_TITLES,
  type CompanySummary,
  type ProfileSection,
} from './types'

type ActiveTab = 'summary' | ProfileSection

interface TabsProps {
  activeTab: ActiveTab
  summary: CompanySummary
  onSelect: (tab: ActiveTab) => void
}

function Tabs({ activeTab, summary, onSelect }: TabsProps) {
  return (
    <div role='tablist' className='flex flex-wrap gap-1 border-b border-line'>
      <button
        type='button'
        role='tab'
        aria-selected={activeTab === 'summary'}
        onClick={() => onSelect('summary')}
        className={cn(
          '-mb-px border-b-2 px-3 py-2.5 text-sm font-medium transition',
          activeTab === 'summary'
            ? 'border-brand text-brand'
            : 'border-transparent text-ink-muted hover:text-ink'
        )}
      >
        Сводка
      </button>

      {PROFILE_SECTIONS.map((section) => {
        const count = summary.sectionCounts[SECTION_COUNT_KEYS[section]]
        const isActive = activeTab === section

        return (
          <button
            key={section}
            type='button'
            role='tab'
            aria-selected={isActive}
            onClick={() => onSelect(section)}
            className={cn(
              '-mb-px flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-sm font-medium transition',
              isActive
                ? 'border-brand text-brand'
                : 'border-transparent text-ink-muted hover:text-ink'
            )}
          >
            {SECTION_TITLES[section]}
            {count > 0 && (
              <span className='rounded-full bg-surface px-1.5 py-0.5 text-xs text-ink-muted'>
                {count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

interface CompanyCardProps {
  inn: string
}

export function CompanyCard({ inn }: CompanyCardProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('summary')
  const { data: summary, isLoading, isError, refetch } = useSummaryData(inn)

  if (isLoading) {
    return (
      <div className='space-y-4'>
        <Skeleton className='h-32 w-full' />
        <Skeleton className='h-24 w-full' />
      </div>
    )
  }

  if (isError || !summary) {
    return (
      <div className='flex flex-col items-center gap-4 rounded-card border border-line bg-white p-12 text-center'>
        <AlertCircle className='h-8 w-8 text-red-500' />
        <div>
          <p className='font-semibold text-ink'>Не удалось загрузить карточку</p>
          <p className='mt-1 text-sm text-ink-muted'>
            Проверьте ИНН или повторите попытку через минуту.
          </p>
        </div>
        <button
          type='button'
          onClick={() => refetch()}
          className='rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand/90'
        >
          Повторить
        </button>
      </div>
    )
  }

  return (
    <div className='space-y-4'>
      <HeroSection summary={summary} />
      <StatCards summary={summary} />

      <Tabs activeTab={activeTab} summary={summary} onSelect={setActiveTab} />

      {activeTab === 'summary' ? (
        <SummaryTab inn={inn} />
      ) : (
        <SectionTab inn={inn} section={activeTab} />
      )}
    </div>
  )
}
