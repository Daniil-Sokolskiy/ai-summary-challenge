import { httpClient } from '@/lib/httpClient'
import type {
  AiDescription,
  AiFeedbackResponse,
  CompanySummary,
  ProfileSection,
  SectionResponse,
} from '../types'

export async function fetchCompanySummary(inn: string): Promise<CompanySummary> {
  const response = await httpClient.get<CompanySummary>(`/company/${inn}/summary`)
  return response.data
}

export async function fetchProfileSection(
  inn: string,
  section: ProfileSection
): Promise<SectionResponse> {
  const response = await httpClient.get<SectionResponse>(`/company/${inn}/section/${section}`)
  return response.data
}

export async function fetchAiDescription(inn: string): Promise<AiDescription> {
  const response = await httpClient.get<AiDescription>(`/company/${inn}/ai-description`)
  return response.data
}

export async function sendAiFeedback(inn: string, isLike: boolean): Promise<AiFeedbackResponse> {
  const response = await httpClient.post<AiFeedbackResponse>(`/company/${inn}/ai-feedback`, {
    is_like: isLike,
  })
  return response.data
}
