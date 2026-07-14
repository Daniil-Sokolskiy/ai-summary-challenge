import { formatDate, formatMoney, formatNumber } from '@/lib/utils'
import type { SectionCellValue, SectionRow } from '../types'

/** Служебные поля — в таблицу не выводим. */
const HIDDEN_COLUMNS = new Set(['id', 'inn', 'companyId'])

/** Подписи известных колонок. Незнакомый ключ разворачиваем эвристикой. */
const COLUMN_LABELS: Record<string, string> = {
  caseNumber: 'Номер дела',
  court: 'Суд',
  role: 'Роль',
  category: 'Категория',
  amount: 'Сумма',
  status: 'Статус',
  startedAt: 'Дата начала',
  openedAt: 'Возбуждено',
  signedAt: 'Подписан',
  issuedAt: 'Выдана',
  validUntil: 'Действует до',
  changedAt: 'Дата изменения',
  date: 'Дата',
  startDate: 'Начало',
  endDate: 'Окончание',
  number: 'Номер',
  issuer: 'Кем выдана',
  authority: 'Орган',
  department: 'Подразделение ФССП',
  subject: 'Предмет',
  activity: 'Вид деятельности',
  customer: 'Заказчик',
  customerName: 'Заказчик',
  price: 'Цена',
  kind: 'Вид',
  type: 'Тип',
  result: 'Результат',
  violationsFound: 'Нарушения',
  debtAmount: 'Сумма долга',
  bailiff: 'Пристав',
  relatedInn: 'ИНН связанной компании',
  relatedName: 'Связанная компания',
  relationType: 'Тип связи',
  sharePercent: 'Доля, %',
  field: 'Поле',
  previousValue: 'Было',
  newValue: 'Стало',
  source: 'Источник',
  description: 'Описание',
}

function humanizeKey(key: string): string {
  const withSpaces = key.replace(/([A-Z])/g, ' $1').toLowerCase().trim()
  return withSpaces.charAt(0).toUpperCase() + withSpaces.slice(1)
}

function columnLabel(key: string): string {
  return COLUMN_LABELS[key] ?? humanizeKey(key)
}

const MONEY_KEY_RE = /(amount|sum|price|revenue|profit|debt)/i
const DATE_KEY_RE = /(date|at)$/i

function formatCell(key: string, value: SectionCellValue): string {
  if (value === null) return '—'
  if (typeof value === 'boolean') return value ? 'Да' : 'Нет'
  if (typeof value === 'number') {
    return MONEY_KEY_RE.test(key) ? formatMoney(value) : formatNumber(value)
  }
  if (DATE_KEY_RE.test(key)) return formatDate(value)
  return value
}

interface SectionTableProps {
  items: SectionRow[]
  /** Сколько строк показать. Остальные скрываем — на превью сводки нужно 3-5. */
  limit?: number
}

export function SectionTable({ items, limit }: SectionTableProps) {
  if (items.length === 0) {
    return <p className='py-6 text-center text-sm text-ink-muted'>Записей не найдено</p>
  }

  const visibleItems = limit ? items.slice(0, limit) : items
  const columns = Object.keys(visibleItems[0]).filter((key) => !HIDDEN_COLUMNS.has(key))

  return (
    <div className='overflow-x-auto'>
      <table className='w-full min-w-[520px] border-collapse text-sm'>
        <thead>
          <tr className='border-b border-line text-left'>
            {columns.map((column) => (
              <th
                key={column}
                scope='col'
                className='whitespace-nowrap px-3 py-2 text-xs font-semibold uppercase tracking-wide text-ink-muted'
              >
                {columnLabel(column)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visibleItems.map((item, rowIndex) => (
            <tr key={rowIndex} className='border-b border-line/60 last:border-0'>
              {columns.map((column) => (
                <td key={column} className='px-3 py-2.5 align-top text-ink-soft'>
                  {formatCell(column, item[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
