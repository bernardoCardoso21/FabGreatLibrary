const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Response types (mirror backend schemas) ───────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: string
  refresh_token: string
}

export interface UserResponse {
  id: string
  email: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface SetSummary {
  id: string
  code: string
  name: string
  image_url: string | null
  printing_count: number
  owned_count: number | null
}

export interface CardListItem {
  id: string
  name: string
  card_type: string
  hero_class: string | null
  talent: string | null
  pitch: number | null
}

export interface PrintingWithCard {
  id: string
  printing_id: string
  edition: string
  foiling: string
  rarity: string
  artists: string[]
  art_variations: string[]
  image_url: string | null
  tcgplayer_product_id: string | null
  tcgplayer_url: string | null
  card: CardListItem
  set: { id: string; code: string; name: string; image_url: string | null }
}

export interface PaginatedPrintings {
  items: PrintingWithCard[]
  total: number
  page: number
  page_size: number
}

export interface OwnedPrintingOut {
  printing: PrintingWithCard
  qty: number
}

export interface ItemResult {
  printing_id: string
  qty: number | null
}

export type BulkAction = 'set_qty' | 'increment' | 'mark_playset' | 'clear'

export interface BulkItem {
  printing_id: string
  action: BulkAction
  qty?: number
}

// ── HTTP helper ───────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  opts: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(opts.headers as Record<string, string>),
  }
  const res = await fetch(`${BASE}${path}`, { ...opts, headers })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export function apiLogin(email: string, password: string): Promise<TokenResponse> {
  return fetch(`${BASE}/auth/token`, {
    method: 'POST',
    body: new URLSearchParams({ username: email, password }),
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }).then(async res => {
    if (!res.ok) throw new Error('Invalid email or password')
    return res.json() as Promise<TokenResponse>
  })
}

export function apiRegister(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    headers: { 'Content-Type': 'application/json' },
  })
}

// ── Sets ──────────────────────────────────────────────────────────────────────

export function apiGetSets(token?: string | null): Promise<SetSummary[]> {
  return request<SetSummary[]>('/sets', {}, token)
}

export interface PrintingFilters {
  q?: string
  foiling?: string
  rarity?: string
  page?: number
  page_size?: number
}

export function apiGetSetPrintings(
  setId: string,
  filters: PrintingFilters = {},
): Promise<PaginatedPrintings> {
  const params = new URLSearchParams()
  if (filters.q) params.set('q', filters.q)
  if (filters.foiling) params.set('foiling', filters.foiling)
  if (filters.rarity) params.set('rarity', filters.rarity)
  params.set('page', String(filters.page ?? 1))
  params.set('page_size', String(filters.page_size ?? 20))
  return request<PaginatedPrintings>(`/sets/${setId}/printings?${params}`)
}

// ── Collection ────────────────────────────────────────────────────────────────

export function apiGetCollectionSummary(
  token: string,
  setId?: string,
): Promise<OwnedPrintingOut[]> {
  const qs = setId ? `?set_id=${setId}` : ''
  return request<OwnedPrintingOut[]>(`/collection/summary${qs}`, {}, token)
}

export function apiUpsertItem(
  token: string,
  printingId: string,
  qty: number,
): Promise<ItemResult> {
  return request<ItemResult>(
    '/collection/items',
    { method: 'POST', body: JSON.stringify({ printing_id: printingId, qty }), headers: { 'Content-Type': 'application/json' } },
    token,
  )
}

export function apiBulkApply(token: string, items: BulkItem[]): Promise<ItemResult[]> {
  return request<ItemResult[]>(
    '/collection/bulk',
    { method: 'POST', body: JSON.stringify({ items }), headers: { 'Content-Type': 'application/json' } },
    token,
  )
}

// ── Missing ────────────────────────────────────────────────────────────────

export interface MissingFilters {
  set_id?: string
  card_id?: string
  edition?: string
  foiling?: string
  rarity?: string
  artists?: string
  page?: number
  page_size?: number
}

export function apiGetMissing(token: string, filters: MissingFilters = {}): Promise<PaginatedPrintings> {
  const params = new URLSearchParams()
  if (filters.set_id) params.set('set_id', filters.set_id)
  if (filters.card_id) params.set('card_id', filters.card_id)
  if (filters.edition) params.set('edition', filters.edition)
  if (filters.foiling) params.set('foiling', filters.foiling)
  if (filters.rarity) params.set('rarity', filters.rarity)
  if (filters.artists) params.set('artists', filters.artists)
  params.set('page', String(filters.page ?? 1))
  params.set('page_size', String(filters.page_size ?? 20))
  return request<PaginatedPrintings>(`/missing?${params}`, {}, token)
}

// ── Wishlists ──────────────────────────────────────────────────────────────

export interface WishlistFilter {
  card_id?: string
  set_id?: string
  edition?: string
  foiling?: string
  rarity?: string
  artists?: string
}

export interface WishlistOut {
  id: string
  name: string
  filter_json: WishlistFilter
  created_at: string
  updated_at: string
}

export function apiGetWishlists(token: string): Promise<WishlistOut[]> {
  return request<WishlistOut[]>('/wishlists', {}, token)
}

export function apiCreateWishlist(
  token: string,
  name: string,
  filter_json: WishlistFilter,
): Promise<WishlistOut> {
  return request<WishlistOut>(
    '/wishlists',
    { method: 'POST', body: JSON.stringify({ name, filter_json }), headers: { 'Content-Type': 'application/json' } },
    token,
  )
}

export function apiDeleteWishlist(token: string, id: string): Promise<void> {
  return request<void>(`/wishlists/${id}`, { method: 'DELETE' }, token)
}
