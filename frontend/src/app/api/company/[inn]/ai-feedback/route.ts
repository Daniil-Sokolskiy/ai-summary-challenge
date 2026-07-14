import { NextResponse, type NextRequest } from 'next/server'
import { backendHttpClient } from '@/lib/backendHttpClient'
import { handleBackendError, validateInn } from '@/lib/apiUtils'
import { transformKeys } from '@/lib/transformKeys'

interface RouteContext {
  params: Promise<{ inn: string }>
}

interface FeedbackBody {
  is_like: boolean
}

function parseBody(raw: unknown): FeedbackBody | null {
  if (raw === null || typeof raw !== 'object') return null
  const isLike = (raw as { is_like?: unknown }).is_like
  if (typeof isLike !== 'boolean') return null
  return { is_like: isLike }
}

export async function POST(request: NextRequest, { params }: RouteContext) {
  const requestId = request.headers.get('x-request-id') ?? crypto.randomUUID()
  const { inn } = await params

  const innError = validateInn(inn)
  if (innError) return innError

  const body = parseBody(await request.json().catch(() => null))
  if (!body) {
    return NextResponse.json({ detail: 'Ожидается поле is_like' }, { status: 400 })
  }

  try {
    const response = await backendHttpClient.post(`/v1/company/${inn}/ai-feedback`, body, {
      headers: { 'x-request-id': requestId },
    })

    return NextResponse.json(transformKeys(response.data), {
      headers: { 'Cache-Control': 'no-store' },
    })
  } catch (error) {
    return handleBackendError(error, {
      requestId,
      logMessage: 'Не удалось отправить оценку ИИ-описания',
      meta: { inn },
    })
  }
}
