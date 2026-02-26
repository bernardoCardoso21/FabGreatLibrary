'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type HealthStatus = 'loading' | 'ok' | 'error'

export default function Home() {
  const [status, setStatus] = useState<HealthStatus>('loading')

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
    fetch(`${apiUrl}/health`)
      .then(res => res.json())
      .then(data => setStatus(data.status === 'ok' ? 'ok' : 'error'))
      .catch(() => setStatus('error'))
  }, [])

  const badgeVariant =
    status === 'ok' ? 'default' : status === 'error' ? 'destructive' : 'secondary'
  const badgeLabel =
    status === 'loading' ? 'Checking…' : status === 'ok' ? 'Online' : 'Unreachable'

  return (
    <main className="flex min-h-[calc(100vh-57px)] items-center justify-center bg-background p-8">
      <div className="w-full max-w-lg space-y-8 text-center">
        <div className="space-y-3">
          <h1 className="text-4xl font-bold tracking-tight">FabGreat Library</h1>
          <p className="text-lg text-muted-foreground">
            Track your Flesh &amp; Blood card collection across all 90+ sets and 14,000+ printings.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link href="/sets">
            <Button size="lg" className="w-full sm:w-auto">Browse Sets</Button>
          </Link>
          <Link href="/register">
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              Create Account
            </Button>
          </Link>
        </div>

        <Card className="text-left">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">API status</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-3">
            <Badge variant={badgeVariant}>{badgeLabel}</Badge>
            <code className="text-xs text-muted-foreground">
              {process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}
            </code>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
