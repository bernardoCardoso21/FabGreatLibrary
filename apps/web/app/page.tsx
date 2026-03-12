'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { apiGetSets } from '@/lib/api'

type HealthStatus = 'loading' | 'ok' | 'error'

export default function Home() {
  const [status, setStatus] = useState<HealthStatus>('loading')
  const [stats, setStats] = useState<{ sets: number; printings: number } | null>(null)

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
    fetch(`${apiUrl}/health`)
      .then(res => res.json())
      .then(data => setStatus(data.status === 'ok' ? 'ok' : 'error'))
      .catch(() => setStatus('error'))

    apiGetSets()
      .then(sets => {
        const printings = sets.reduce((sum, s) => sum + s.printing_count, 0)
        setStats({ sets: sets.length, printings })
      })
      .catch(() => {})
  }, [])

  const badgeVariant =
    status === 'ok' ? 'default' : status === 'error' ? 'destructive' : 'secondary'
  const badgeLabel =
    status === 'loading' ? 'Checking…' : status === 'ok' ? 'Online' : 'Unreachable'

  return (
    <main className="flex min-h-[calc(100vh-57px)] flex-col items-center justify-center bg-background p-8">
      <div className="w-full max-w-2xl space-y-10 text-center">
        {/* Hero */}
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
            FabGreat Library
          </h1>
          <p className="mx-auto max-w-lg text-lg text-muted-foreground">
            Your Flesh &amp; Blood collection tracker. Browse every set, track
            every printing, manage your collection down to foiling and edition.
          </p>
        </div>

        {/* CTAs */}
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link href="/sets">
            <Button size="lg" className="w-full sm:w-auto">Browse Sets</Button>
          </Link>
          <Link href="/register">
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              Create Account
            </Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="ghost" className="w-full sm:w-auto">
              Try Demo
            </Button>
          </Link>
        </div>

        {/* Live stats bar */}
        {stats && (
          <div className="mx-auto flex max-w-md justify-center divide-x rounded-lg border bg-muted/30 py-4">
            <div className="flex-1 px-6 text-center">
              <div className="text-2xl font-bold">{stats.sets}</div>
              <div className="text-xs text-muted-foreground">Sets</div>
            </div>
            <div className="flex-1 px-6 text-center">
              <div className="text-2xl font-bold">
                {stats.printings.toLocaleString()}
              </div>
              <div className="text-xs text-muted-foreground">Printings</div>
            </div>
          </div>
        )}

        {/* API status */}
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <span>API</span>
          <Badge variant={badgeVariant}>{badgeLabel}</Badge>
        </div>
      </div>
    </main>
  )
}
