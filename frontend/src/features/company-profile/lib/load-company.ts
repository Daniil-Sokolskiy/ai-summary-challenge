import axios from 'axios'
import { backendHttpClient } from '@/lib/backendHttpClient'
import { logger } from '@/lib/logger'
import { transformKeys } from '@/lib/transformKeys'
import type { CompanySummary } from '../types'

/**
 * Серверная загрузка сводки для префетча в RSC.
 * Возвращает null, если компании нет — страница отдаст 404.
 */
export async function loadCompanySummary(inn: string): Promise<CompanySummary | null> {
  try {
    const response = await backendHttpClient.get(`/v1/company/${inn}/summary`)
    return transformKeys(response.data) as CompanySummary
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    logger.error('Не удалось загрузить сводку для SSR', error, { inn })
    throw error
  }
}
