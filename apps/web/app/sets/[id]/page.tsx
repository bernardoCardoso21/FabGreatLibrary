'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { use, useEffect, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  apiBulkApply,
  apiGetCollectionSummary,
  apiGetSetCards,
  apiGetSetPrintings,
  type PlaysetCardItem,
  type PlaysetFilters,
  type PrintingFilters,
} from '@/lib/api'
import { useTokenValue } from '@/lib/auth'
import { useCollectionMode } from '@/lib/collection-mode'

// ── Display helpers ────────────────────────────────────────────────────────────

const FOILING_LABEL: Record<string, string> = {
  S: 'Standard',
  R: 'Rainbow',
  C: 'Cold',
  G: 'Gold Cold',
}
const FOILING_CLASS: Record<string, string> = {
  S: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  R: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  C: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  G: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
}
const RARITY_LABEL: Record<string, string> = {
  C: 'Common',
  R: 'Rare',
  M: 'Majestic',
  L: 'Legendary',
  F: 'Fabled',
  T: 'Token',
  P: 'Promo',
}
const RARITY_CLASS: Record<string, string> = {
  C: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
  R: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  M: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  L: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
  F: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  T: 'bg-muted text-muted-foreground',
  P: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
}
const EDITION_LABEL: Record<string, string> = {
  A: 'Alpha',
  F: '1st Ed',
  U: 'Unlimited',
  N: '\u2014',
}

function FoilingBadge({ code }: { code: string }) {
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-xs font-medium ${FOILING_CLASS[code] ?? 'bg-muted text-muted-foreground'}`}
    >
      {FOILING_LABEL[code] ?? code}
    </span>
  )
}

function RarityBadge({ code }: { code: string }) {
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-xs font-medium ${RARITY_CLASS[code] ?? 'bg-muted text-muted-foreground'}`}
    >
      {RARITY_LABEL[code] ?? code}
    </span>
  )
}

// ── Pitch indicator ──────────────────────────────────────────────────────────

const PITCH_CLASS: Record<number, string> = {
  1: 'bg-red-500',
  2: 'bg-yellow-500',
  3: 'bg-blue-500',
}

function PitchDot({ pitch }: { pitch: number | null | undefined }) {
  if (pitch == null) return null
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${PITCH_CLASS[pitch] ?? 'bg-muted'}`}
      title={`Pitch ${pitch}`}
    />
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20

export default function SetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: setId } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()

  const token = useTokenValue()
  const collectionMode = useCollectionMode()
  const isPlayset = token ? collectionMode === 'playset' : false

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [foilingFilter, setFoilingFilter] = useState('')
  const [rarityFilter, setRarityFilter] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setPage(1)
    setSelected(new Set())
    setFoilingFilter('')
  }, [isPlayset])

  // ── Master set mode queries ──────────────────────────────────────────────

  const printingFilters: PrintingFilters = {
    page,
    page_size: PAGE_SIZE,
    ...(debouncedSearch && { q: debouncedSearch }),
    ...(foilingFilter && { foiling: foilingFilter }),
    ...(rarityFilter && { rarity: rarityFilter }),
  }

  const printingsQuery = useQuery({
    queryKey: ['set-printings', setId, printingFilters],
    queryFn: () => apiGetSetPrintings(setId, printingFilters),
    enabled: !isPlayset,
  })

  const collectionQuery = useQuery({
    queryKey: ['collection', setId],
    queryFn: () => apiGetCollectionSummary(token!, setId),
    enabled: !!token && !isPlayset,
  })

  const ownedMap = useMemo(() => {
    const m = new Map<string, number>()
    for (const item of collectionQuery.data ?? []) {
      m.set(item.printing.id, item.qty)
    }
    return m
  }, [collectionQuery.data])

  // ── Playset mode queries ─────────────────────────────────────────────────

  const playsetFilters: PlaysetFilters = {
    page,
    page_size: PAGE_SIZE,
    ...(debouncedSearch && { q: debouncedSearch }),
    ...(rarityFilter && { rarity: rarityFilter }),
  }

  const playsetQuery = useQuery({
    queryKey: ['set-cards', setId, playsetFilters, token],
    queryFn: () => apiGetSetCards(setId, playsetFilters, token),
    enabled: isPlayset,
  })

  // ── Mutations ────────────────────────────────────────────────────────────

  const bulkMutation = useMutation({
    mutationFn: (action: 'mark_playset' | 'clear') =>
      apiBulkApply(
        token!,
        [...selected].map(id => ({ printing_id: id, action })),
      ),
    onSuccess: () => {
      setSelected(new Set())
      queryClient.invalidateQueries({ queryKey: ['collection', setId] })
      queryClient.invalidateQueries({ queryKey: ['set-cards', setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
    },
  })

  // ── Derived values ───────────────────────────────────────────────────────

  const printingItems = printingsQuery.data?.items ?? []
  const playsetItems = playsetQuery.data?.items ?? []
  const total = isPlayset
    ? (playsetQuery.data?.total ?? 0)
    : (printingsQuery.data?.total ?? 0)
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const setInfo = printingItems[0]?.set
  const isLoading = isPlayset ? playsetQuery.isLoading : printingsQuery.isLoading
  const isError = isPlayset ? playsetQuery.error : printingsQuery.error

  function toggleSelect(id: string) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (isPlayset) return
    if (selected.size === printingItems.length && printingItems.length > 0) {
      setSelected(new Set())
    } else {
      setSelected(new Set(printingItems.map(p => p.id)))
    }
  }

  function changeFilter(setter: (v: string) => void, value: string) {
    setter(value)
    setPage(1)
    setSelected(new Set())
  }

  const hasFilters = !!(debouncedSearch || foilingFilter || rarityFilter)

  function clearFilters() {
    setSearch('')
    setFoilingFilter('')
    setRarityFilter('')
    setPage(1)
  }

  return (
    <main className="mx-auto max-w-7xl space-y-4 p-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <button onClick={() => router.back()} className="hover:text-foreground">
          &larr; Back
        </button>
        <span>/</span>
        <span>{setInfo?.name ?? '...'}</span>
        {setInfo && (
          <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{setInfo.code}</span>
        )}
        {token && (
          <span className="ml-auto rounded bg-muted px-2 py-0.5 text-xs font-medium">
            {isPlayset ? 'Playset' : 'Master Set'}
          </span>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Search cards..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="h-8 w-52"
        />
        {!isPlayset && (
          <select
            className="h-8 rounded-md border border-input bg-background px-3 text-sm"
            value={foilingFilter}
            onChange={e => changeFilter(setFoilingFilter, e.target.value)}
          >
            <option value="">All foilings</option>
            {Object.entries(FOILING_LABEL).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        )}
        <select
          className="h-8 rounded-md border border-input bg-background px-3 text-sm"
          value={rarityFilter}
          onChange={e => changeFilter(setRarityFilter, e.target.value)}
        >
          <option value="">All rarities</option>
          {Object.entries(RARITY_LABEL).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        {hasFilters && (
          <Button variant="ghost" size="sm" className="h-8" onClick={clearFilters}>
            Clear filters
          </Button>
        )}
      </div>

      {/* Bulk action bar (master set mode only) */}
      {selected.size > 0 && token && !isPlayset && (
        <div className="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
          <span className="text-sm font-medium">{selected.size} selected</span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => bulkMutation.mutate('mark_playset')}
            disabled={bulkMutation.isPending}
          >
            Mark Playset (3x)
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => bulkMutation.mutate('clear')}
            disabled={bulkMutation.isPending}
          >
            Clear
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())}>
            Deselect all
          </Button>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : isError ? (
        <p className="text-destructive">Failed to load.</p>
      ) : (isPlayset ? playsetItems.length === 0 : printingItems.length === 0) ? (
        <div className="rounded-lg border border-dashed py-12 text-center">
          <p className="text-lg font-medium">No {isPlayset ? 'cards' : 'printings'} found</p>
          {hasFilters ? (
            <p className="mt-1 text-sm text-muted-foreground">
              Try adjusting your filters or{' '}
              <button className="underline hover:text-foreground" onClick={clearFilters}>
                clear all filters
              </button>
            </p>
          ) : (
            <p className="mt-1 text-sm text-muted-foreground">This set has no {isPlayset ? 'cards' : 'printings'} yet.</p>
          )}
        </div>
      ) : isPlayset ? (
        <PlaysetTable
          items={playsetItems}
          token={token}
          setId={setId}
        />
      ) : (
        <MasterSetTable
          items={printingItems}
          token={token}
          ownedMap={ownedMap}
          selected={selected}
          toggleSelect={toggleSelect}
          toggleAll={toggleAll}
          setId={setId}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {(page - 1) * PAGE_SIZE + 1}--{Math.min(page * PAGE_SIZE, total)} of {total}
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
            >
              Previous
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={page >= totalPages}
              onClick={() => setPage(p => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </main>
  )
}

// ── Playset table ────────────────────────────────────────────────────────────

function PlaysetTable({
  items,
  token,
  setId,
}: {
  items: PlaysetCardItem[]
  token: string | null
  setId: string
}) {
  const queryClient = useQueryClient()

  const actionMutation = useMutation({
    mutationFn: ({ printingId, action }: { printingId: string; action: 'increment' | 'decrement' }) =>
      apiBulkApply(token!, [{ printing_id: printingId, action }]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['set-cards', setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
    },
  })

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="border-b bg-muted/40">
          <tr>
            <th className="px-3 py-2 text-left font-medium">Card</th>
            <th className="px-3 py-2 text-left font-medium">Type</th>
            <th className="px-3 py-2 text-left font-medium">Rarity</th>
            {token && <th className="w-32 px-3 py-2 text-center font-medium">Owned / Target</th>}
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map(card => {
            const owned = card.owned_qty ?? 0
            const complete = owned >= card.target
            const isPending =
              actionMutation.isPending &&
              actionMutation.variables?.printingId === card.default_printing_id
            return (
              <tr
                key={card.id}
                className={`hover:bg-muted/30 ${complete ? 'opacity-60' : ''}`}
              >
                <td className="px-3 py-2">
                  <div className="flex items-center gap-3">
                    {card.image_url ? (
                      <Image
                        src={card.image_url}
                        alt={card.name}
                        width={160}
                        height={224}
                        className="shrink-0 rounded object-cover"
                        unoptimized
                      />
                    ) : (
                      <div className="flex h-[224px] w-[160px] shrink-0 items-center justify-center rounded bg-muted text-xs text-muted-foreground">
                        ?
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{card.name}</span>
                      <PitchDot pitch={card.pitch} />
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2 text-muted-foreground">
                  {card.hero_class ?? card.card_type}
                </td>
                <td className="px-3 py-2">
                  <RarityBadge code={card.rarity} />
                </td>
                {token && (
                  <td className="px-3 py-2">
                    <div className="flex items-center justify-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 w-7 p-0"
                        disabled={isPending || owned === 0}
                        onClick={() =>
                          actionMutation.mutate({
                            printingId: card.default_printing_id,
                            action: 'decrement',
                          })
                        }
                      >
                        -
                      </Button>
                      <span className={`font-mono min-w-[3rem] text-center ${complete ? 'text-green-600 font-semibold' : ''}`}>
                        {owned} / {card.target}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 w-7 p-0"
                        disabled={isPending || owned >= card.target}
                        onClick={() =>
                          actionMutation.mutate({
                            printingId: card.default_printing_id,
                            action: 'increment',
                          })
                        }
                      >
                        +
                      </Button>
                    </div>
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── Master set table ─────────────────────────────────────────────────────────

function MasterSetTable({
  items,
  token,
  ownedMap,
  selected,
  toggleSelect,
  toggleAll,
  setId,
}: {
  items: { id: string; printing_id: string; edition: string; foiling: string; rarity: string; image_url: string | null; card: { name: string; hero_class: string | null; card_type: string } }[]
  token: string | null
  ownedMap: Map<string, number>
  selected: Set<string>
  toggleSelect: (id: string) => void
  toggleAll: () => void
  setId: string
}) {
  const queryClient = useQueryClient()

  const actionMutation = useMutation({
    mutationFn: ({ printingId, action }: { printingId: string; action: 'increment' | 'decrement' }) =>
      apiBulkApply(token!, [{ printing_id: printingId, action }]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection', setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
    },
  })

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="border-b bg-muted/40">
          <tr>
            {token && (
              <th className="w-10 px-3 py-2 text-left">
                <Checkbox
                  checked={items.length > 0 && selected.size === items.length}
                  onCheckedChange={toggleAll}
                />
              </th>
            )}
            <th className="px-3 py-2 text-left font-medium">Card</th>
            <th className="px-3 py-2 text-left font-medium">Type</th>
            <th className="px-3 py-2 text-left font-medium">Edition</th>
            <th className="px-3 py-2 text-left font-medium">Foiling</th>
            <th className="px-3 py-2 text-left font-medium">Rarity</th>
            {token && <th className="w-32 px-3 py-2 text-center font-medium">Owned</th>}
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map(printing => {
            const qty = ownedMap.get(printing.id) ?? 0
            const target = printing.card.card_type.startsWith('Hero') ? 1 : 3
            const complete = qty >= target
            const isPending =
              actionMutation.isPending &&
              actionMutation.variables?.printingId === printing.id
            return (
              <tr
                key={printing.id}
                className={`hover:bg-muted/30 ${selected.has(printing.id) ? 'bg-muted/20' : ''} ${complete ? 'opacity-60' : ''}`}
              >
                {token && (
                  <td className="px-3 py-2">
                    <Checkbox
                      checked={selected.has(printing.id)}
                      onCheckedChange={() => toggleSelect(printing.id)}
                    />
                  </td>
                )}
                <td className="px-3 py-2">
                  <div className="flex items-center gap-3">
                    {printing.image_url ? (
                      <Image
                        src={printing.image_url}
                        alt={printing.card.name}
                        width={160}
                        height={224}
                        className="shrink-0 rounded object-cover"
                        unoptimized
                      />
                    ) : (
                      <div className="flex h-[224px] w-[160px] shrink-0 items-center justify-center rounded bg-muted text-xs text-muted-foreground">
                        ?
                      </div>
                    )}
                    <div>
                      <div className="font-medium">{printing.card.name}</div>
                      <div className="font-mono text-xs text-muted-foreground">
                        {printing.printing_id}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2 text-muted-foreground">
                  {printing.card.hero_class ?? printing.card.card_type}
                </td>
                <td className="px-3 py-2">
                  {EDITION_LABEL[printing.edition] ?? printing.edition}
                </td>
                <td className="px-3 py-2">
                  <FoilingBadge code={printing.foiling} />
                </td>
                <td className="px-3 py-2">
                  <RarityBadge code={printing.rarity} />
                </td>
                {token && (
                  <td className="px-3 py-2">
                    <div className="flex items-center justify-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 w-7 p-0"
                        disabled={isPending || qty === 0}
                        onClick={() =>
                          actionMutation.mutate({
                            printingId: printing.id,
                            action: 'decrement',
                          })
                        }
                      >
                        -
                      </Button>
                      <span className={`font-mono min-w-[3rem] text-center ${complete ? 'text-green-600 font-semibold' : ''}`}>
                        {qty} / {target}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 w-7 p-0"
                        disabled={isPending || qty >= target}
                        onClick={() =>
                          actionMutation.mutate({
                            printingId: printing.id,
                            action: 'increment',
                          })
                        }
                      >
                        +
                      </Button>
                    </div>
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
