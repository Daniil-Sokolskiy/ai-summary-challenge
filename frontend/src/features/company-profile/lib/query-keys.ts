import type { ProfileSection } from '../types'

export const profileKeys = {
  all: (inn: string) => ['profile', 'company', inn] as const,
  summary: (inn: string) => ['profile', 'company', inn, 'summary'] as const,
  section: (inn: string, section: ProfileSection) =>
    ['profile', 'company', inn, 'section', section] as const,
  aiDescription: (inn: string) => ['profile', 'company', inn, 'ai-description'] as const,
}
