'use client'

import { Suspense } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiGetSets, apiUpdateMe, type SetSummary } from '@/lib/api'
import { useTokenValue } from '@/lib/auth'
import { useCollectionMode, setCollectionMode } from '@/lib/collection-mode'

const CATEGORIES = [
  { key: 'booster', label: 'Booster Sets', description: 'Main expansion sets' },
  { key: 'deck', label: 'Decks', description: 'Pre-constructed and starter decks' },
  { key: 'promo', label: 'Promos', description: 'Promotional and prize cards' },
] as const

const MODES = [
  { key: 'playset', label: 'Playset' },
  { key: 'master_set', label: 'Master Set' },
] as const

function CollectionModeToggle({ token }: { token: string }) {
  const mode = useCollectionMode()
  const queryClient = useQueryClient()

  function handleToggle(newMode: 'master_set' | 'playset') {
    if (newMode === mode) return
    setCollectionMode(newMode)
    apiUpdateMe(token, { collection_mode: newMode }).catch(() => {})
    queryClient.invalidateQueries({ queryKey: ['sets'] })
  }

  return (
    <div className="inline-flex rounded-lg border bg-muted p-0.5">
      {MODES.map(m => (
        <button
          key={m.key}
          onClick={() => handleToggle(m.key)}
          className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
            mode === m.key
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          {m.label}
        </button>
      ))}
    </div>
  )
}

function CompletionBar({ set, mode }: { set: SetSummary; mode: string }) {
  const label = mode === 'playset' ? 'cards' : 'printings'
  const pct = set.printing_count > 0
    ? Math.min(100, ((set.owned_count ?? 0) / set.printing_count) * 100)
    : 0

  return (
    <div className="space-y-1">
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        {set.owned_count} / {set.printing_count} {label}
      </p>
    </div>
  )
}

function CategoryPicker({ sets }: { sets: SetSummary[] }) {
  const counts = { booster: 0, deck: 0, promo: 0 } as Record<string, number>
  for (const s of sets) {
    counts[s.set_type] = (counts[s.set_type] ?? 0) + 1
  }

  return (
    <main className="mx-auto max-w-7xl p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Browse Sets</h1>
        <p className="mt-1 text-sm text-muted-foreground">Choose a category to explore</p>
      </div>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {CATEGORIES.map(cat => (
          <Link key={cat.key} href={`/sets?type=${cat.key}`}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md h-full">
              <CardHeader>
                <CardTitle className="text-xl">{cat.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{cat.description}</p>
                <p className="mt-2 text-2xl font-semibold">{counts[cat.key] ?? 0}</p>
                <p className="text-xs text-muted-foreground">sets</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  )
}

function SetGrid({ type, token }: { type: string; token: string | null }) {
  const label = CATEGORIES.find(c => c.key === type)?.label ?? 'Sets'
  const collectionMode = useCollectionMode()
  const mode = token ? collectionMode : undefined

  const { data: sets, isLoading, error } = useQuery<SetSummary[]>({
    queryKey: ['sets', token, type, mode],
    queryFn: () => apiGetSets(token, type, mode),
  })

  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl p-8">
        <p className="text-muted-foreground">Loading sets...</p>
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
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <Link href="/sets" className="text-sm text-muted-foreground hover:text-foreground">
            &larr; All categories
          </Link>
          <h1 className="text-3xl font-bold">{label}</h1>
        </div>
        <div className="flex items-center gap-4">
          {token && <CollectionModeToggle token={token} />}
          <p className="text-sm text-muted-foreground">{sets?.length ?? 0} sets</p>
        </div>
      </div>
      {sets?.length === 0 ? (
        <div className="rounded-lg border border-dashed py-12 text-center">
          <p className="text-lg font-medium">No sets available</p>
          <p className="mt-1 text-sm text-muted-foreground">The card catalog has not been imported yet.</p>
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
                  <CompletionBar set={set} mode={mode ?? 'playset'} />
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

function SetsPageInner() {
  const token = useTokenValue()
  const searchParams = useSearchParams()
  const type = searchParams.get('type')

  const { data: allSets, isLoading, error } = useQuery<SetSummary[]>({
    queryKey: ['sets', token],
    queryFn: () => apiGetSets(token),
    enabled: !type,
  })

  if (type) {
    return <SetGrid type={type} token={token} />
  }

  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl p-8">
        <p className="text-muted-foreground">Loading...</p>
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

  return <CategoryPicker sets={allSets ?? []} />
}

export default function SetsPage() {
  return (
    <Suspense fallback={<main className="mx-auto max-w-7xl p-8"><p className="text-muted-foreground">Loading...</p></main>}>
      <SetsPageInner />
    </Suspense>
  )
}
