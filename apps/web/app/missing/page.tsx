'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  apiCreateWishlist,
  apiDeleteWishlist,
  apiGetMissing,
  apiGetSets,
  apiGetWishlists,
  type MissingFilters,
  type WishlistFilter,
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

export default function MissingPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const token = useTokenValue()

  useEffect(() => {
    if (token === null) {
      router.push('/login')
    }
  }, [token, router])

  // Filter state
  const [setIdFilter, setSetIdFilter] = useState('')
  const [foilingFilter, setFoilingFilter] = useState('')
  const [rarityFilter, setRarityFilter] = useState('')
  const [page, setPage] = useState(1)

  // Wishlist panel state
  const [wishlistName, setWishlistName] = useState('')
  const [wishlistError, setWishlistError] = useState('')

  const filters: MissingFilters = {
    page,
    page_size: PAGE_SIZE,
    ...(setIdFilter && { set_id: setIdFilter }),
    ...(foilingFilter && { foiling: foilingFilter }),
    ...(rarityFilter && { rarity: rarityFilter }),
  }

  const missingQuery = useQuery({
    queryKey: ['missing', filters],
    queryFn: () => apiGetMissing(token!, filters),
    enabled: !!token,
  })

  const setsQuery = useQuery({
    queryKey: ['sets', token],
    queryFn: () => apiGetSets(token),
    enabled: !!token,
  })

  const wishlistsQuery = useQuery({
    queryKey: ['wishlists'],
    queryFn: () => apiGetWishlists(token!),
    enabled: !!token,
  })

  const createWishlistMutation = useMutation({
    mutationFn: ({ name, filter }: { name: string; filter: WishlistFilter }) =>
      apiCreateWishlist(token!, name, filter),
    onSuccess: () => {
      setWishlistName('')
      setWishlistError('')
      queryClient.invalidateQueries({ queryKey: ['wishlists'] })
    },
    onError: (err: Error) => {
      setWishlistError(err.message)
    },
  })

  const deleteWishlistMutation = useMutation({
    mutationFn: (id: string) => apiDeleteWishlist(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlists'] })
    },
  })

  const wishlist = wishlistsQuery.data?.[0] ?? null

  function loadWishlist() {
    if (!wishlist) return
    const f = wishlist.filter_json
    setSetIdFilter(f.set_id ?? '')
    setFoilingFilter(f.foiling ?? '')
    setRarityFilter(f.rarity ?? '')
    setPage(1)
  }

  function saveWishlist() {
    if (!wishlistName.trim()) return
    const filter: WishlistFilter = {}
    if (setIdFilter) filter.set_id = setIdFilter
    if (foilingFilter) filter.foiling = foilingFilter
    if (rarityFilter) filter.rarity = rarityFilter
    createWishlistMutation.mutate({ name: wishlistName.trim(), filter })
  }

  function changeFilter(setter: (v: string) => void, value: string) {
    setter(value)
    setPage(1)
  }

  if (!token) return null

  const items = missingQuery.data?.items ?? []
  const total = missingQuery.data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <main className="mx-auto max-w-7xl space-y-4 p-6">
      <h1 className="text-xl font-semibold">Missing Printings</h1>

      {/* Wishlist panel */}
      <div className="rounded-lg border bg-muted/30 p-4">
        {wishlist ? (
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-medium">Saved wishlist:</span>
            <span className="text-sm">{wishlist.name}</span>
            <Button size="sm" variant="outline" onClick={loadWishlist}>
              Load filters
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => deleteWishlistMutation.mutate(wishlist.id)}
              disabled={deleteWishlistMutation.isPending}
            >
              Delete
            </Button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <Input
              placeholder="Wishlist name…"
              value={wishlistName}
              onChange={e => setWishlistName(e.target.value)}
              className="h-8 w-48"
            />
            <Button
              size="sm"
              onClick={saveWishlist}
              disabled={!wishlistName.trim() || createWishlistMutation.isPending}
            >
              Save current filter
            </Button>
            {wishlistError && (
              <span className="text-sm text-destructive">{wishlistError}</span>
            )}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          className="h-8 rounded-md border border-input bg-background px-3 text-sm"
          value={setIdFilter}
          onChange={e => changeFilter(setSetIdFilter, e.target.value)}
        >
          <option value="">All sets</option>
          {(setsQuery.data ?? []).map(s => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.code})
            </option>
          ))}
        </select>
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
        {(setIdFilter || foilingFilter || rarityFilter) && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8"
            onClick={() => {
              setSetIdFilter('')
              setFoilingFilter('')
              setRarityFilter('')
              setPage(1)
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      {/* Count */}
      {!missingQuery.isLoading && (
        <p className="text-sm text-muted-foreground">
          {total} missing printing{total !== 1 ? 's' : ''}
        </p>
      )}

      {/* Table */}
      {missingQuery.isLoading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : missingQuery.error ? (
        <p className="text-destructive">Failed to load missing printings.</p>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground">No missing printings found.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Card</th>
                <th className="px-3 py-2 text-left font-medium">Set</th>
                <th className="px-3 py-2 text-left font-medium">Type</th>
                <th className="px-3 py-2 text-left font-medium">Edition</th>
                <th className="px-3 py-2 text-left font-medium">Foiling</th>
                <th className="px-3 py-2 text-left font-medium">Rarity</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map(printing => (
                <tr key={printing.id} className="hover:bg-muted/30">
                  <td className="px-3 py-2">
                    <div className="font-medium">{printing.card.name}</div>
                    <div className="font-mono text-xs text-muted-foreground">
                      {printing.printing_id}
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <div>{printing.set.name}</div>
                    <div className="font-mono text-xs text-muted-foreground">
                      {printing.set.code}
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
                </tr>
              ))}
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
