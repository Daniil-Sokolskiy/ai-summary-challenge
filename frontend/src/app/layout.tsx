import type { Metadata } from 'next'
import Link from 'next/link'
import type { ReactNode } from 'react'
import { Providers } from './providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'Картотека — проверка контрагентов',
  description: 'Карточка компании: реквизиты, финансы, арбитраж, госконтракты, проверки.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang='ru'>
      <body>
        <Providers>
          <div className='min-h-screen'>
            <header className='border-b border-line bg-white'>
              <div className='mx-auto flex max-w-5xl items-center justify-between px-4 py-4'>
                <Link href='/' className='text-lg font-semibold text-ink'>
                  Картотека
                </Link>
                <span className='text-sm text-ink-muted'>Проверка контрагентов</span>
              </div>
            </header>

            <main className='mx-auto max-w-5xl px-4 py-8'>{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
