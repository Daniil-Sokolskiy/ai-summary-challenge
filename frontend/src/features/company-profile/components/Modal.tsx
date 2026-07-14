'use client'

import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}

/** Минимальная модалка: Escape, клик по подложке, блокировка скролла body. */
export function Modal({ open, title, onClose, children }: ModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', handleKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeButtonRef.current?.focus()

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className='fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 sm:p-8'
      onClick={onClose}
    >
      <div
        role='dialog'
        aria-modal='true'
        aria-label={title}
        className='relative w-full max-w-3xl rounded-card border border-line bg-white shadow-xl'
        onClick={(event) => event.stopPropagation()}
      >
        <button
          ref={closeButtonRef}
          type='button'
          onClick={onClose}
          aria-label='Закрыть'
          className='absolute right-4 top-4 rounded-lg p-1.5 text-ink-muted transition hover:bg-surface hover:text-ink'
        >
          <X className='h-5 w-5' />
        </button>
        {children}
      </div>
    </div>
  )
}
