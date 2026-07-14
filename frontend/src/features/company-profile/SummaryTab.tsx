'use client'

import { AiDescriptionBlock } from './components/AiDescriptionBlock'
import { LazySection } from './components/LazySection'
import { SectionCard } from './components/SectionCard'
import { PROFILE_SECTIONS } from './types'

/** Сколько строк секции показываем в превью на сводке. */
const PREVIEW_ROWS = 3

interface SummaryTabProps {
  inn: string
}

/**
 * Сводка: ИИ-описание сверху, ниже — превью всех секций карточки.
 * Превью подгружаются лениво, по мере прокрутки.
 */
export function SummaryTab({ inn }: SummaryTabProps) {
  return (
    <div className='space-y-4'>
      <AiDescriptionBlock inn={inn} />

      {PROFILE_SECTIONS.map((section) => (
        <LazySection key={section}>
          <SectionCard inn={inn} section={section} limit={PREVIEW_ROWS} />
        </LazySection>
      ))}
    </div>
  )
}
