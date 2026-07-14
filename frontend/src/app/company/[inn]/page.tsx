import { dehydrate, HydrationBoundary } from '@tanstack/react-query'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { getQueryClient } from '@/lib/queryClient'
import { INN_RE } from '@/lib/utils'
import { CompanyCard } from '@/features/company-profile/CompanyCard'
import { loadCompanySummary } from '@/features/company-profile/lib/load-company'
import { profileKeys } from '@/features/company-profile/lib/query-keys'

interface CompanyPageProps {
  params: Promise<{ inn: string }>
}

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { inn } = await params

  if (!INN_RE.test(inn)) {
    notFound()
  }

  const summary = await loadCompanySummary(inn)
  if (!summary) {
    notFound()
  }

  // Префетчим сводку: это шапка карточки, она нужна в первом же кадре и должна
  // приехать в HTML, а не догружаться после гидратации. Остальные блоки карточки
  // тянутся на клиенте по мере необходимости.
  const queryClient = getQueryClient()
  queryClient.setQueryData(profileKeys.summary(inn), summary)

  return (
    <div>
      <Link
        href='/'
        className='mb-5 inline-flex items-center gap-1.5 text-sm text-ink-muted transition hover:text-ink'
      >
        <ArrowLeft className='h-4 w-4' />
        Все компании
      </Link>

      <HydrationBoundary state={dehydrate(queryClient)}>
        <CompanyCard inn={inn} />
      </HydrationBoundary>
    </div>
  )
}
