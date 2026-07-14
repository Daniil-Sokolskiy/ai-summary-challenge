'use client'

import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import { fetchProfileSection } from '../lib/api'
import { profileKeys } from '../lib/query-keys'
import type { ProfileSection, SectionResponse } from '../types'

/**
 * Данные одной секции карточки (арбитраж, госконтракты, проверки...).
 *
 * Секции — живые реестровые данные: суды и исполнительные производства
 * обновляются в течение дня, поэтому политику актуальности задаёт глобальный
 * дефолт QueryClient, а не хук. Свои `staleTime` здесь не выставляем, чтобы
 * не расходиться с остальным приложением.
 */
export function useProfileSection(
  inn: string,
  section: ProfileSection,
  options?: { enabled?: boolean }
): UseQueryResult<SectionResponse> {
  return useQuery<SectionResponse>({
    queryKey: profileKeys.section(inn, section),
    queryFn: () => fetchProfileSection(inn, section),
    enabled: options?.enabled ?? true,
  })
}
