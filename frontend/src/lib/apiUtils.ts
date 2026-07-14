import axios from 'axios'
import { NextResponse } from 'next/server'
import { logger } from '@/lib/logger'
import { INN_RE } from '@/lib/utils'

/** Проверка формата ИНН на входе в прокси. Возвращает 400 или null. */
export function validateInn(inn: string): NextResponse | null {
  if (!inn || !INN_RE.test(inn)) {
    return NextResponse.json({ detail: 'Неверный формат ИНН' }, { status: 400 })
  }
  return null
}

interface BackendErrorContext {
  requestId: string
  logMessage: string
  meta?: Record<string, string | number | boolean | undefined>
}

/**
 * Единая обработка ошибок бэкенда в прокси-роутах.
 *
 * Наружу отдаём только безопасное сообщение: тело ответа бэкенда может содержать
 * трейсбек, SQL или внутренние адреса, и светить это в браузер нельзя. Подробности
 * уходят в лог вместе с request_id — по нему инцидент разбирается в Kibana.
 * Любая 5xx схлопывается в 502 «Ошибка сервера»: для клиента это всё равно
 * «сервис недоступен», разбирать причину на фронте незачем.
 */
export function handleBackendError(error: unknown, context: BackendErrorContext): NextResponse {
  if (axios.isAxiosError(error) && error.response) {
    const status = error.response.status

    if (status !== 404) {
      logger.error(context.logMessage, error, {
        request_id: context.requestId,
        backend_status: status,
        ...context.meta,
      })
    }

    const safeMessage =
      status === 404 ? 'Не найдено' : status >= 500 ? 'Ошибка сервера' : 'Ошибка запроса'

    return NextResponse.json({ detail: safeMessage }, { status: status >= 500 ? 502 : status })
  }

  logger.error(context.logMessage, error, {
    request_id: context.requestId,
    ...context.meta,
  })

  return NextResponse.json({ detail: 'Ошибка сервера' }, { status: 502 })
}
