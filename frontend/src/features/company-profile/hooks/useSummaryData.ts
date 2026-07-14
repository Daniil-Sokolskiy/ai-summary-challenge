'use client'

import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import { fetchCompanySummary } from '../lib/api'
import { profileKeys } from '../lib/query-keys'
import type { CompanySummary } from '../types'

/**
 * Шапка карточки: реквизиты, финансы, счётчики секций.
 *
 * Сводку префетчит серверный компонент страницы и отдаёт через HydrationBoundary,
 * поэтому на клиенте она уже в кэше. `staleTime: Infinity` — чтобы гидратация
 * не спровоцировала немедленный повторный запрос за теми же данными; если кэш
 * пуст (клиентская навигация), запрос всё равно уйдёт.
 */
export function useSummaryData(inn: string): UseQueryResult<CompanySummary> {
  return useQuery<CompanySummary>({
    queryKey: profileKeys.summary(inn),
    queryFn: () => fetchCompanySummary(inn),
    staleTime: Infinity,
  })
}
