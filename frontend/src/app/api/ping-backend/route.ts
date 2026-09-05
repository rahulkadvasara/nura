import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
  
  // Format target health URL
  const healthUrl = apiBaseUrl.endsWith('/') ? `${apiBaseUrl}health` : `${apiBaseUrl}/health`

  try {
    const res = await fetch(healthUrl, {
      cache: 'no-store',
      headers: {
        'User-Agent': 'Nura-Vercel-Cron-KeepAlive/1.0',
      },
    })

    const data = await res.json()

    return NextResponse.json({
      success: true,
      timestamp: new Date().toISOString(),
      health_url: healthUrl,
      backend_status: data,
    })
  } catch (err: any) {
    return NextResponse.json(
      {
        success: false,
        timestamp: new Date().toISOString(),
        health_url: healthUrl,
        error: err.message || 'Failed to connect to backend',
      },
      { status: 500 }
    )
  }
}
