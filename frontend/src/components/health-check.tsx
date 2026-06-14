'use client'

import { useQuery } from '@tanstack/react-query'
import { healthService } from '@/services/health'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'

export function HealthCheck() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: healthService.checkHealth,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Checking system status...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-destructive" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Badge variant="destructive" className="mb-2">
            Unhealthy
          </Badge>
          <p className="text-sm text-muted-foreground">
            Unable to connect to the backend service
          </p>
        </CardContent>
      </Card>
    )
  }

  const getStatusColor = (status: string) => {
    return status === 'connected' || status === 'healthy' 
      ? 'text-green-600' 
      : 'text-red-600'
  }

  const getStatusIcon = (status: string) => {
    return status === 'connected' || status === 'healthy'
      ? <CheckCircle className="h-4 w-4 text-green-600" />
      : <XCircle className="h-4 w-4 text-red-600" />
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getStatusIcon(data?.status || '')}
          System Health
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Overall Status</span>
          <Badge variant={data?.status === 'healthy' ? 'default' : 'destructive'}>
            {data?.status}
          </Badge>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm">Application</span>
          <span className="text-sm font-medium">{data?.app}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm">Environment</span>
          <span className="text-sm font-medium">{data?.environment}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm">MongoDB</span>
          <span className={`text-sm font-medium ${getStatusColor(data?.mongodb || '')}`}>
            {data?.mongodb}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm">Qdrant</span>
          <span className={`text-sm font-medium ${getStatusColor(data?.qdrant || '')}`}>
            {data?.qdrant}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}