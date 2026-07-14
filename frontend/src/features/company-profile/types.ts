/** Секции карточки, кроме сводки. Совпадают с путями бэкенда `/section/{section}`. */
export type ProfileSection =
  | 'court-cases'
  | 'enforcement'
  | 'contracts'
  | 'licenses'
  | 'inspections'
  | 'relations'
  | 'changes'

export const PROFILE_SECTIONS: readonly ProfileSection[] = [
  'court-cases',
  'enforcement',
  'contracts',
  'licenses',
  'inspections',
  'relations',
  'changes',
] as const

/** Русские подписи вкладок. */
export const SECTION_TITLES: Record<ProfileSection, string> = {
  'court-cases': 'Арбитраж',
  enforcement: 'Исполнительные производства',
  contracts: 'Госконтракты',
  licenses: 'Лицензии',
  inspections: 'Проверки',
  relations: 'Связи',
  changes: 'История изменений',
}

/** Счётчики строк по секциям — приходят вместе со сводкой, рисуют бейджи вкладок. */
export interface SectionCounts {
  courtCases: number
  enforcement: number
  contracts: number
  licenses: number
  inspections: number
  relations: number
  changes: number
}

/** Секция → поле счётчика в сводке. Пути и поля названы по-разному, связываем явно. */
export const SECTION_COUNT_KEYS: Record<ProfileSection, keyof SectionCounts> = {
  'court-cases': 'courtCases',
  enforcement: 'enforcement',
  contracts: 'contracts',
  licenses: 'licenses',
  inspections: 'inspections',
  relations: 'relations',
  changes: 'changes',
}

export interface CompanySummary {
  inn: string
  name: string
  status: string
  registrationDate: string | null
  city: string | null
  mainOkvedCode: string | null
  mainOkvedName: string | null
  revenue: number | null
  profit: number | null
  headcount: number | null
  sectionCounts: SectionCounts
}

/**
 * Значение ячейки в строке секции. Набор колонок у каждой секции свой
 * (у арбитража — номер дела и сумма иска, у лицензий — орган и срок),
 * поэтому строка — это map, а не запись с фиксированными полями.
 */
export type SectionCellValue = string | number | boolean | null

export type SectionRow = Record<string, SectionCellValue>

export interface SectionResponse {
  section: string
  total: number
  items: SectionRow[]
}

export interface AiDescription {
  inn: string
  description: string
  generatedAt: string | null
  cached: boolean
  score: number | null
  isLlm: boolean
  history: string[]
}

export interface AiFeedbackResponse {
  accepted: boolean
  triggeredRegeneration: boolean
}
