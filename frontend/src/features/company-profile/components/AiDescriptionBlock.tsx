'use client'

import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Sparkles, ThumbsDown, ThumbsUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { fetchAiDescription, sendAiFeedback } from '../lib/api'
import { profileKeys } from '../lib/query-keys'
import type { AiDescription, AiFeedbackResponse } from '../types'
import { Modal } from './Modal'
import { Skeleton } from './Skeleton'

interface AiSection {
  title: string
  body: string
}

/**
 * Модель отдаёт markdown с заголовками второго уровня («## Финансовое состояние»).
 * Режем текст по ним: первый блок уходит в тизер на карточке, остальные — в модалку.
 */
function parseSections(text: string): AiSection[] {
  const cleaned = text.trim()
  const headingRegex = /^##\s+(.+)$/gm
  const matches = [...cleaned.matchAll(headingRegex)]

  if (matches.length === 0) {
    return cleaned ? [{ title: '', body: cleaned }] : []
  }

  const sections: AiSection[] = []

  // Текст до первого заголовка — вступление без названия.
  const firstMatchIndex = matches[0].index
  if (firstMatchIndex !== undefined && firstMatchIndex > 0) {
    const preamble = cleaned.slice(0, firstMatchIndex).trim()
    if (preamble) sections.push({ title: '', body: preamble })
  }

  for (let index = 0; index < matches.length; index += 1) {
    const match = matches[index]
    if (match.index === undefined) continue

    const bodyStart = match.index + match[0].length
    const nextMatch = matches[index + 1]
    const bodyEnd = nextMatch?.index ?? cleaned.length
    const body = cleaned.slice(bodyStart, bodyEnd).trim()

    if (body) sections.push({ title: match[1].trim(), body })
  }

  return sections
}

function AiDescriptionSkeleton() {
  return (
    <div className='flex items-center gap-4 rounded-card border border-brand/20 bg-brand-soft/40 p-4'>
      <div className='flex h-12 w-12 shrink-0 animate-shimmer items-center justify-center rounded-xl bg-brand'>
        <Sparkles className='h-5 w-5 text-white' />
      </div>
      <div className='min-w-0 flex-1'>
        <div className='mb-2 text-sm font-semibold text-ink'>
          ИИ собирает информацию о компании…
        </div>
        <Skeleton className='h-3 w-full rounded' />
        <Skeleton className='mt-2 h-3 w-2/3 rounded' />
      </div>
    </div>
  )
}

interface AiDescriptionBlockProps {
  inn: string
}

export function AiDescriptionBlock({ inn }: AiDescriptionBlockProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [feedbackSent, setFeedbackSent] = useState(false)

  const { data, isLoading } = useQuery<AiDescription>({
    queryKey: profileKeys.aiDescription(inn),
    queryFn: () => fetchAiDescription(inn),
    // Описание генерируется дорого, повторять запрос при неудаче не стоит:
    // это стоит денег и времени пользователя.
    retry: false,
    // Текст описания меняется редко — держим его свежим целый час, чтобы
    // переходы по вкладкам не дёргали генерацию заново.
    staleTime: 60 * 60 * 1000,
    // Кэш держим 10 минут: описания у нас длинные, и хранить их в памяти
    // вкладки дольше нет смысла.
    gcTime: 10 * 60 * 1000,
  })

  const feedbackMutation = useMutation<AiFeedbackResponse, Error, boolean>({
    mutationFn: (isLike: boolean) => sendAiFeedback(inn, isLike),
    onSuccess: () => setFeedbackSent(true),
  })

  const sections = useMemo(
    () => (data?.description ? parseSections(data.description) : []),
    [data?.description]
  )

  if (isLoading) {
    return <AiDescriptionSkeleton />
  }

  if (sections.length === 0) {
    return null
  }

  const teaser = sections[0]

  return (
    <>
      <button
        type='button'
        onClick={() => setIsOpen(true)}
        className={cn(
          'group flex w-full items-center gap-4 rounded-card border border-brand/20 bg-brand-soft/40 p-4 text-left transition',
          'hover:border-brand hover:bg-brand-soft'
        )}
      >
        <div className='flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand'>
          <Sparkles className='h-5 w-5 text-white' />
        </div>

        <div className='min-w-0 flex-1'>
          <div className='mb-1 text-sm font-semibold text-ink'>
            {teaser.title || 'Главное о компании'}
          </div>
          <p className='line-clamp-2 text-sm leading-relaxed text-ink-soft'>{teaser.body}</p>
        </div>

        <span className='shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition group-hover:bg-brand/90'>
          Показать
        </span>
      </button>

      <Modal open={isOpen} title='Описание компании' onClose={() => setIsOpen(false)}>
        <div className='p-6 sm:p-8'>
          <div className='mb-6 flex items-center gap-3'>
            <div className='flex h-10 w-10 items-center justify-center rounded-xl bg-brand'>
              <Sparkles className='h-5 w-5 text-white' />
            </div>
            <div>
              <h2 className='text-lg font-semibold text-ink'>Описание компании</h2>
              <p className='text-xs text-ink-muted'>
                Сгенерировано ИИ
                {data?.score !== null && data?.score !== undefined && ` · оценка ${data.score}/100`}
              </p>
            </div>
          </div>

          <div className='space-y-6'>
            {sections.map((section, index) => (
              <section key={`${section.title}-${index}`}>
                {section.title && (
                  <h3 className='mb-2 text-base font-semibold text-ink'>{section.title}</h3>
                )}
                <p className='whitespace-pre-line text-sm leading-relaxed text-ink-soft'>
                  {section.body}
                </p>
              </section>
            ))}
          </div>

          <div className='mt-8 flex flex-wrap items-center gap-3 border-t border-line pt-5'>
            {feedbackSent ? (
              <span className='text-sm text-ink-muted'>Спасибо за обратную связь!</span>
            ) : (
              <>
                <span className='text-sm text-ink-muted'>Описание было полезным?</span>
                <button
                  type='button'
                  aria-label='Да, полезно'
                  disabled={feedbackMutation.isPending}
                  onClick={() => feedbackMutation.mutate(true)}
                  className='flex h-9 w-9 items-center justify-center rounded-full border border-line text-ink-muted transition hover:border-brand hover:text-brand disabled:opacity-50'
                >
                  <ThumbsUp className='h-4 w-4' />
                </button>
                <button
                  type='button'
                  aria-label='Нет, не помогло'
                  disabled={feedbackMutation.isPending}
                  onClick={() => feedbackMutation.mutate(false)}
                  className='flex h-9 w-9 items-center justify-center rounded-full border border-line text-ink-muted transition hover:border-red-400 hover:text-red-500 disabled:opacity-50'
                >
                  <ThumbsDown className='h-4 w-4' />
                </button>
              </>
            )}
            {feedbackMutation.isError && (
              <span className='text-sm text-ink-muted'>Не удалось отправить. Попробуйте позже.</span>
            )}
          </div>
        </div>
      </Modal>
    </>
  )
}
