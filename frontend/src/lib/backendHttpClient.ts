import axios from 'axios'
import { getServerEnv } from '@/config/env'

const { backendUrl } = getServerEnv()

/**
 * Серверный клиент: route handlers, server components, server actions.
 * Никогда не импортируется в `'use client'`-файлы — `getServerEnv()` там бросит.
 */
export const backendHttpClient = axios.create({
  baseURL: backendUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})
