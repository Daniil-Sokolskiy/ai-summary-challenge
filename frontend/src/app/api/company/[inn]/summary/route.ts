import { NextResponse, type NextRequest } from 'next/server'
import { backendHttpClient } from '@/lib/backendHttpClient'
import { handleBackendError, validateInn } from '@/lib/apiUtils'
import { transformKeys } from '@/lib/transformKeys'

interface RouteContext {
  params: Promise<{ inn: string }>
}

export async function GET(request: NextRequest, { params }: RouteContext) {
  const requestId = request.headers.get('x-request-id') ?? crypto.randomUUID()
  const { inn } = await params

  const innError = validateInn(inn)
  if (innError) return innError

  try {
    const response = await backendHttpClient.get(`/v1/company/${inn}/summary`, {
      headers: { 'x-request-id': requestId },
    })

    return NextResponse.json(transformKeys(response.data), {
      headers: { 'Cache-Control': 'private, no-cache' },
    })
  } catch (error) {
    return handleBackendError(error, {
      requestId,
      logMessage: 'Не удалось получить сводку по компании',
      meta: { inn },
    })
  }
}
