import { NextResponse, type NextRequest } from 'next/server'
import { backendHttpClient } from '@/lib/backendHttpClient'
import { handleBackendError, validateInn } from '@/lib/apiUtils'
import { logger } from '@/lib/logger'
import { transformKeys } from '@/lib/transformKeys'

interface RouteContext {
  params: Promise<{ inn: string }>
}

export async function GET(request: NextRequest, { params }: RouteContext) {
  const startedAt = Date.now()
  const requestId = request.headers.get('x-request-id') ?? crypto.randomUUID()
  const { inn } = await params

  const innError = validateInn(inn)
  if (innError) return innError

  try {
    const response = await backendHttpClient.get<{ cached?: boolean }>(
      `/v1/company/${inn}/ai-description`,
      {
        headers: { 'x-request-id': requestId },
        // 25с: дольше держать воркер Next.js на одном запросе нельзя — пул воркеров
        // общий на всё приложение, и висящие соединения выедают его на пустом месте.
        timeout: 25000,
      }
    )

    logger.info('Получено ИИ-описание компании', {
      request_id: requestId,
      inn,
      duration: Date.now() - startedAt,
      cached: Boolean(response.data.cached),
    })

    // Cache-Control ставим сами, а не проксируем с бэкенда: описание может быть
    // перегенерировано по фидбэку пользователей, и застрявшая копия в CDN
    // держала бы старый текст.
    return NextResponse.json(transformKeys(response.data), {
      headers: { 'Cache-Control': 'private, no-cache' },
    })
  } catch (error) {
    return handleBackendError(error, {
      requestId,
      logMessage: 'Не удалось получить ИИ-описание компании',
      meta: { inn, duration: Date.now() - startedAt },
    })
  }
}
