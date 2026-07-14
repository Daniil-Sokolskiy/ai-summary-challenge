import axios from 'axios'
import { publicEnv } from '@/config/env'

/**
 * Клиент браузера. Ходит ТОЛЬКО в `/api/*` — прямые вызовы бэкенда из браузера
 * запрещены (BACKEND_URL живёт на сервере).
 *
 * Таймаут 60с: генерация ИИ-описания — самая долгая операция в продукте,
 * и обрывать её на клиенте раньше времени нет смысла, пользователь всё равно
 * ждёт результат. Остальные ручки отвечают за десятки миллисекунд.
 */
export const httpClient = axios.create({
  baseURL: publicEnv.apiUrl,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})
