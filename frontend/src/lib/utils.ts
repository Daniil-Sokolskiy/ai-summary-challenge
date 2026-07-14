import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

/** Валидный формат ИНН: 10 цифр (ЮЛ) или 12 (ИП). */
export const INN_RE = /^\d{10}$|^\d{12}$/

const MONEY_FORMATTER = new Intl.NumberFormat('ru-RU', {
  maximumFractionDigits: 0,
})

/** 128500000 → «128 500 000 ₽». Null/undefined → «—». */
export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${MONEY_FORMATTER.format(value)} ₽`
}

/** 47 → «47». Null/undefined → «—». */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return MONEY_FORMATTER.format(value)
}

/** «2011-03-14» → «14.03.2011». Мусор на входе отдаём как есть. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString('ru-RU')
}
