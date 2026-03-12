'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiGetSets, type SetSummary } from '@/lib/api'
import { useTokenValue } from '@/lib/auth'

export default function SetsPage() {
  const token = useTokenValue()

  const { data: sets, isLoading, error } = useQuery<SetSummary[]>({
    queryKey: ['sets', token],
    queryFn: () => apiGetSets(token),
  })

  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl p-8">
        <p className="text-muted-foreground">Loading sets…</p>
      </main>
    )
  }

  if (error) {
    return (
      <main className="mx-auto max-w-7xl p-8">
        <p className="text-destructive">Failed to load sets.</p>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-7xl p-8">
      <div className="mb-6 flex items-baseline justify-between">
        <h1 className="text-3xl font-bold">Sets</h1>
        <p className="text-sm text-muted-foreground">{sets?.length ?? 0} sets</p>
      </div>
      {sets?.length === 0 ? (
        <div className="rounded-lg border border-dashed py-12 text-center">
          <p className="text-lg font-medium">No sets available</p>
          <p className="mt-1 text-sm text-muted-foreground">The card catalog hasn't been imported yet.</p>
        </div>
      ) : (
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {sets?.map(set => (
          <Link key={set.id} href={`/sets/${set.id}`}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md h-full">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base leading-tight">{set.name}</CardTitle>
                  <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground">
                    {set.code}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                {token && set.owned_count !== null ? (
                  <div className="space-y-1">
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{
                          width: `${Math.min(100, (set.owned_count / set.printing_count) * 100)}%`,
                        }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {set.owned_count} / {set.printing_count} owned
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">{set.printing_count} printings</p>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
      )}
    </main>
  )
}
