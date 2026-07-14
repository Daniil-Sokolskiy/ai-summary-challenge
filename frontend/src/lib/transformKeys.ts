function snakeToCamel(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_, letter: string) => letter.toUpperCase())
}

/**
 * Рекурсивно переводит snake_case-ключи ответа бэкенда в camelCase.
 * Применяется в прокси-роутах, поэтому клиент всегда работает с camelCase.
 */
export function transformKeys(input: unknown): unknown {
  if (Array.isArray(input)) {
    return input.map(transformKeys)
  }
  if (input !== null && typeof input === 'object') {
    return Object.fromEntries(
      Object.entries(input as Record<string, unknown>).map(([key, value]) => [
        snakeToCamel(key),
        transformKeys(value),
      ])
    )
  }
  return input
}
