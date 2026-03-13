'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { apiGetSets } from '@/lib/api'

export default function Home() {
  const [stats, setStats] = useState<{ sets: number; printings: number } | null>(null)

  useEffect(() => {
    apiGetSets()
      .then(sets => {
        const printings = sets.reduce((sum, s) => sum + s.printing_count, 0)
        setStats({ sets: sets.length, printings })
      })
      .catch(() => {})
  }, [])

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

        {/* CTA */}
        <div className="flex justify-center">
          <Link href="/sets">
            <Button size="lg">Browse Sets</Button>
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
      </div>
    </main>
  )
}
