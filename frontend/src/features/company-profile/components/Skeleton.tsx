import { cn } from '@/lib/utils'
import type { CSSProperties } from 'react'

interface SkeletonProps {
  className?: string
  style?: CSSProperties
}

export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      aria-hidden='true'
      style={style}
      className={cn('animate-shimmer rounded-card bg-line/70', className)}
    />
  )
}
