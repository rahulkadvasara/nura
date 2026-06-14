import { HealthCheck } from '@/components/health-check'

export default function HomePage() {
  return (
    <main className="container mx-auto p-8">
      <div className="flex min-h-screen flex-col items-center justify-center">
        <div className="text-center space-y-6">
          <h1 className="text-4xl font-bold tracking-tight">
            Welcome to Nura
          </h1>
          <p className="text-xl text-muted-foreground">
            Your Intelligent Healthcare Companion
          </p>
          
          <div className="mt-8">
            <HealthCheck />
          </div>
        </div>
      </div>
    </main>
  )
}