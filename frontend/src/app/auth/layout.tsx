import { GuestRoute } from '@/components/auth/GuestRoute'
import { ReactNode } from 'react'
import Link from 'next/link'

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <GuestRoute>
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8 bg-white p-8 rounded-xl shadow-sm border border-slate-100">
          <div className="text-center">
            <Link href="/" className="inline-block">
              <h2 className="text-3xl font-bold tracking-tight text-primary">
                Nura
              </h2>
            </Link>
          </div>
          {children}
        </div>
      </div>
    </GuestRoute>
  )
}
