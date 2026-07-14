import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { DEMO_COMPANIES } from '@/features/company-profile/data/companies'

export default function HomePage() {
  return (
    <div>
      <div className='mb-6'>
        <h1 className='text-2xl font-semibold text-ink'>Компании в базе</h1>
        <p className='mt-1 text-sm text-ink-muted'>
          Откройте карточку, чтобы посмотреть реквизиты, финансы и ИИ-описание компании.
        </p>
      </div>

      <ul className='divide-y divide-line overflow-hidden rounded-card border border-line bg-white'>
        {DEMO_COMPANIES.map((company) => (
          <li key={company.inn}>
            <Link
              href={`/company/${company.inn}`}
              className='flex items-center gap-4 px-5 py-4 transition hover:bg-surface'
            >
              <div className='min-w-0 flex-1'>
                <div className='truncate font-medium text-ink'>{company.name}</div>
                <div className='mt-0.5 text-sm text-ink-muted'>
                  ИНН {company.inn} · {company.city} · {company.industry}
                </div>
              </div>
              <ChevronRight className='h-5 w-5 shrink-0 text-ink-muted' aria-hidden='true' />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
