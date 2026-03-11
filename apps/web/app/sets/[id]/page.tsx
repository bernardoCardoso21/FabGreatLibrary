'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { use, useEffect, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  apiBulkApply,
  apiGetCollectionSummary,
  apiGetSetPrintings,
  apiUpsertItem,
  type PrintingFilters,
} from '@/lib/api'
import { useTokenValue } from '@/lib/auth'

// ── Display helpers ────────────────────────────────────────────────────────────

const FOILING_LABEL: Record<string, string> = {
  S: 'Standard',
  R: 'Rainbow',
  C: 'Cold',
  G: 'Gold Cold',
}
const FOILING_CLASS: Record<string, string> = {
  S: 'bg-slate-100 text-slate-700',
  R: 'bg-purple-100 text-purple-700',
  C: 'bg-blue-100 text-blue-700',
  G: 'bg-yellow-100 text-yellow-700',
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
  C: 'bg-slate-100 text-slate-600',
  R: 'bg-blue-100 text-blue-700',
  M: 'bg-purple-100 text-purple-700',
  L: 'bg-orange-100 text-orange-700',
  F: 'bg-red-100 text-red-700',
  T: 'bg-muted text-muted-foreground',
  P: 'bg-green-100 text-green-700',
}
const EDITION_LABEL: Record<string, string> = {
  A: 'Alpha',
  F: '1st Ed',
  U: 'Unlimited',
  N: '—',
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

// ── Page ──────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20

export default function SetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: setId } = use(params)
  const queryClient = useQueryClient()

  const token = useTokenValue()

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [foilingFilter, setFoilingFilter] = useState('')
  const [rarityFilter, setRarityFilter] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())

  // Debounce search input
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  const filters: PrintingFilters = {
    page,
    page_size: PAGE_SIZE,
    ...(debouncedSearch && { q: debouncedSearch }),
    ...(foilingFilter && { foiling: foilingFilter }),
    ...(rarityFilter && { rarity: rarityFilter }),
  }

  const printingsQuery = useQuery({
    queryKey: ['set-printings', setId, filters],
    queryFn: () => apiGetSetPrintings(setId, filters),
  })

  const collectionQuery = useQuery({
    queryKey: ['collection', setId],
    queryFn: () => apiGetCollectionSummary(token!, setId),
    enabled: !!token,
  })

  // Map printing.id → qty
  const ownedMap = useMemo(() => {
    const m = new Map<string, number>()
    for (const item of collectionQuery.data ?? []) {
      m.set(item.printing.id, item.qty)
    }
    return m
  }, [collectionQuery.data])

  // +1 mutation
  const incrementMutation = useMutation({
    mutationFn: ({ printingId, qty }: { printingId: string; qty: number }) =>
      apiUpsertItem(token!, printingId, qty),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection', setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
    },
  })

  // Bulk mutation
  const bulkMutation = useMutation({
    mutationFn: (action: 'mark_playset' | 'clear') =>
      apiBulkApply(
        token!,
        [...selected].map(id => ({ printing_id: id, action })),
      ),
    onSuccess: () => {
      setSelected(new Set())
      queryClient.invalidateQueries({ queryKey: ['collection', setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
    },
  })

  const items = printingsQuery.data?.items ?? []
  const total = printingsQuery.data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const setInfo = items[0]?.set

  function toggleSelect(id: string) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === items.length && items.length > 0) {
      setSelected(new Set())
    } else {
      setSelected(new Set(items.map(p => p.id)))
    }
  }

  function changeFilter(setter: (v: string) => void, value: string) {
    setter(value)
    setPage(1)
    setSelected(new Set())
  }

  return (
    <main className="mx-auto max-w-7xl space-y-4 p-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/sets" className="hover:text-foreground">Sets</Link>
        <span>/</span>
        <span>{setInfo?.name ?? '…'}</span>
        {setInfo && (
          <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{setInfo.code}</span>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Search cards…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="h-8 w-52"
        />
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
        {(debouncedSearch || foilingFilter || rarityFilter) && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8"
            onClick={() => {
              setSearch('')
              setFoilingFilter('')
              setRarityFilter('')
              setPage(1)
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      {/* Bulk action bar */}
      {selected.size > 0 && token && (
        <div className="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
          <span className="text-sm font-medium">{selected.size} selected</span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => bulkMutation.mutate('mark_playset')}
            disabled={bulkMutation.isPending}
          >
            Mark Playset (3×)
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
      {printingsQuery.isLoading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : printingsQuery.error ? (
        <p className="text-destructive">Failed to load printings.</p>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground">No printings found.</p>
      ) : (
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
                {token && <th className="w-16 px-3 py-2 text-center font-medium">Qty</th>}
                {token && <th className="w-16 px-3 py-2 text-left font-medium" />}
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map(printing => {
                const qty = ownedMap.get(printing.id) ?? 0
                const isPending =
                  incrementMutation.isPending &&
                  incrementMutation.variables?.printingId === printing.id
                return (
                  <tr
                    key={printing.id}
                    className={`hover:bg-muted/30 ${selected.has(printing.id) ? 'bg-muted/20' : ''}`}
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
                      <div className="font-medium">{printing.card.name}</div>
                      <div className="font-mono text-xs text-muted-foreground">
                        {printing.printing_id}
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
                      <td className="px-3 py-2 text-center font-mono">
                        {qty > 0 ? (
                          <span className="font-semibold">{qty}</span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    )}
                    {token && (
                      <td className="px-3 py-2">
                        <Button
                          size="sm"
                          variant={qty > 0 ? 'outline' : 'ghost'}
                          className="h-7 px-2"
                          disabled={isPending}
                          onClick={() =>
                            incrementMutation.mutate({
                              printingId: printing.id,
                              qty: qty + 1,
                            })
                          }
                        >
                          +1
                        </Button>
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of {total}
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
