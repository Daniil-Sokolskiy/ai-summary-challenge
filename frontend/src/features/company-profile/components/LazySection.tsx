'use client'

import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Skeleton } from './Skeleton'

interface LazySectionProps {
  children: ReactNode
  /** Запас вокруг вьюпорта — начинаем монтировать чуть раньше, чем блок доедет до экрана. */
  rootMargin?: string
  /** Высота плейсхолдера: держит скроллбар на месте, пока секция не смонтирована. */
  minHeight?: number
}

/**
 * Монтирует детей, только пока плейсхолдер находится рядом с вьюпортом.
 *
 * На карточке семь тяжёлых секций с таблицами, и держать их все в DOM незачем:
 * пользователь обычно читает сводку и уходит. То, что уехало за экран, снимаем
 * с монтирования — экономим память на длинной карточке.
 */
export function LazySection({
  children,
  rootMargin = '200px 0px',
  minHeight = 220,
}: LazySectionProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const element = containerRef.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
        } else {
          setVisible(false)
        }
      },
      { rootMargin }
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [rootMargin])

  return (
    <div ref={containerRef}>
      {visible ? children : <Skeleton className='w-full' style={{ minHeight }} />}
    </div>
  )
}
