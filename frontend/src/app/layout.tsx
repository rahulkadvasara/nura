import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/lib/providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Nura - AI-Powered Healthcare Assistant',
  description: 'Your Intelligent Healthcare Companion',
}

import { Toaster } from 'sonner'
import { AuthProvider } from '@/components/auth/AuthProvider'
import { GoogleOAuthProvider } from '@react-oauth/google'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || 'dummy-client-id'

  return (
    <html lang="en">
      <body className={inter.className}>
        <GoogleOAuthProvider clientId={googleClientId}>
          <QueryProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </QueryProvider>
        </GoogleOAuthProvider>
        <Toaster position="top-center" richColors />
      </body>
    </html>
  )
}