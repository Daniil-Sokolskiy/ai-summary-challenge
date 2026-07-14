import { QueryClient } from '@tanstack/react-query'

let browserQueryClient: QueryClient | undefined

function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Реестровые данные меняются в течение дня, поэтому политику
        // актуальности оставляем на усмотрение конкретных хуков.
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  })
}

export function getQueryClient(): QueryClient {
  // На сервере — новый клиент на каждый запрос, чтобы кэш одного пользователя
  // не утёк другому.
  if (typeof window === 'undefined') {
    return makeQueryClient()
  }
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient()
  }
  return browserQueryClient
}
