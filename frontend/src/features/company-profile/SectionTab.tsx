'use client'

import { SectionCard } from './components/SectionCard'
import type { ProfileSection } from './types'

interface SectionTabProps {
  inn: string
  section: ProfileSection
}

/** Отдельная вкладка секции: тот же блок, но без ограничения на число строк. */
export function SectionTab({ inn, section }: SectionTabProps) {
  return <SectionCard inn={inn} section={section} />
}
