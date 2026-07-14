const DEFAULT_BACKEND_URL = 'http://api:8000'
const DEFAULT_PUBLIC_API_URL = '/api'

/**
 * Серверные переменные окружения. Бросает, если вызвана из браузера —
 * `BACKEND_URL` не должен попасть в клиентский бандл ни при каких условиях.
 */
export function getServerEnv(): { backendUrl: string } {
  if (typeof window !== 'undefined') {
    throw new Error('getServerEnv доступна только на сервере')
  }

  const raw = (process.env.BACKEND_URL || DEFAULT_BACKEND_URL).trim()

  try {
    return { backendUrl: new URL(raw).toString().replace(/\/$/, '') }
  } catch {
    throw new Error('BACKEND_URL должен быть валидным URL')
  }
}

/** Публичный конфиг — безопасно читать из клиентских компонентов. */
export const publicEnv = {
  apiUrl: (process.env.NEXT_PUBLIC_API_URL || DEFAULT_PUBLIC_API_URL).replace(/\/$/, ''),
}
