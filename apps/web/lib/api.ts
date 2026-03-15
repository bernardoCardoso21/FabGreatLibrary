import type { components } from '@fabgreat/types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Re-exports from generated types (backend is source of truth) ──────────────

export type TokenResponse    = components['schemas']['TokenResponse']
export type UserResponse     = components['schemas']['UserResponse']
export type SetSummary       = components['schemas']['SetSummary']
export type CardListItem     = components['schemas']['CardListItem']
export type PrintingWithCard = components['schemas']['PrintingWithCard']
export type PaginatedPrintings = components['schemas']['PaginatedPrintings']
export type ItemResult       = components['schemas']['ItemResult']
export type BulkAction       = components['schemas']['BulkAction']
export type BulkItem         = components['schemas']['BulkItemRequest']
export type PlaysetCardItem  = components['schemas']['PlaysetCardItem']
export type PaginatedPlaysetCards = components['schemas']['PaginatedPlaysetCards']

// ── Frontend-only query param groupings (not backend schemas) ─────────────────

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
    if (res.status === 401 && token) {
      const { clearToken } = await import('@/lib/auth')
      clearToken()
    }
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
): Promise<SetSummary[]> {
  const params = new URLSearchParams()
  if (setType) params.set('set_type', setType)
  const qs = params.toString()
  return request<SetSummary[]>(`/sets${qs ? `?${qs}` : ''}`, {}, token)
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
