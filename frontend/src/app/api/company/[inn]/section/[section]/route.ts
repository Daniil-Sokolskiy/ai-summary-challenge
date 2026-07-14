import { NextResponse, type NextRequest } from 'next/server'
import { backendHttpClient } from '@/lib/backendHttpClient'
import { handleBackendError, validateInn } from '@/lib/apiUtils'
import { transformKeys } from '@/lib/transformKeys'

/**
 * Белый список секций. Значение из URL уходит в путь запроса к бэкенду,
 * поэтому пропускаем только известные.
 */
const VALID_SECTIONS = new Set([
  'court-cases',
  'enforcement',
  'contracts',
  'licenses',
  'inspections',
  'relations',
  'changes',
])

interface RouteContext {
  params: Promise<{ inn: string; section: string }>
}

export async function GET(request: NextRequest, { params }: RouteContext) {
  const requestId = request.headers.get('x-request-id') ?? crypto.randomUUID()
  const { inn, section } = await params

  const innError = validateInn(inn)
  if (innError) return innError

  if (!VALID_SECTIONS.has(section)) {
    return NextResponse.json({ detail: 'Неизвестный раздел' }, { status: 400 })
  }

  try {
    const response = await backendHttpClient.get(`/v1/company/${inn}/section/${section}`, {
      headers: { 'x-request-id': requestId },
    })

    return NextResponse.json(transformKeys(response.data), {
      headers: { 'Cache-Control': 'private, no-cache' },
    })
  } catch (error) {
    return handleBackendError(error, {
      requestId,
      logMessage: 'Не удалось получить раздел карточки',
      meta: { inn, section },
    })
  }
}
