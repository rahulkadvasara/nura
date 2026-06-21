import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/lib/providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Nura - AI-Powered Healthcare Assistant',
  description: 'Your Intelligent Healthcare Companion',
}

import { Toaster } from 'sonner'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          {children}
        </QueryProvider>
        <Toaster position="top-center" richColors />
      </body>
    </html>
  )
}