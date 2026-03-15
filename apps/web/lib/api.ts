import type { components } from '@fabgreat/types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Re-exports from generated types (backend is source of truth) ──────────────

export type TokenResponse    = components['schemas']['TokenResponse']
export type UserResponse     = components['schemas']['UserResponse']
export type SetSummary       = components['schemas']['SetSummary']
export type CardListItem     = components['schemas']['CardListItem']
export type PrintingWithCard = components['schemas']['PrintingWithCard']
export type PaginatedPrintings = components['schemas']['PaginatedPrintings']
export type OwnedPrintingOut = components['schemas']['OwnedPrintingOut']
export type ItemResult       = components['schemas']['ItemResult']
export type BulkAction       = components['schemas']['BulkAction']
export type BulkItem         = components['schemas']['BulkItemRequest']
export type WishlistFilter   = components['schemas']['WishlistFilter']
export type WishlistOut      = components['schemas']['WishlistOut']
export type UpdatePreferencesRequest = components['schemas']['UpdatePreferencesRequest']
export type PlaysetCardItem  = components['schemas']['PlaysetCardItem']
export type PaginatedPlaysetCards = components['schemas']['PaginatedPlaysetCards']

// ── Frontend-only query param groupings (not backend schemas) ─────────────────

export interface PrintingFilters {
  q?: string
  foiling?: string
  rarity?: string
  page?: number
  page_size?: number
}

export interface PlaysetFilters {
  q?: string
  rarity?: string
  page?: number
  page_size?: number
}

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
  if (res.status === 204) return undefined as T
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

export function apiGetSets(
  token?: string | null,
  setType?: string,
  collectionMode?: string,
): Promise<SetSummary[]> {
  const params = new URLSearchParams()
  if (setType) params.set('set_type', setType)
  if (collectionMode) params.set('collection_mode', collectionMode)
  const qs = params.toString()
  return request<SetSummary[]>(`/sets${qs ? `?${qs}` : ''}`, {}, token)
}

export function apiUpdateMe(
  token: string,
  body: UpdatePreferencesRequest,
): Promise<UserResponse> {
  return request<UserResponse>('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  }, token)
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

export function apiGetSetCards(
  setId: string,
  filters: PlaysetFilters = {},
  token?: string | null,
): Promise<PaginatedPlaysetCards> {
  const params = new URLSearchParams()
  if (filters.q) params.set('q', filters.q)
  if (filters.rarity) params.set('rarity', filters.rarity)
  params.set('page', String(filters.page ?? 1))
  params.set('page_size', String(filters.page_size ?? 20))
  return request<PaginatedPlaysetCards>(`/sets/${setId}/cards?${params}`, {}, token)
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
