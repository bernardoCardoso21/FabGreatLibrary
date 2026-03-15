import { useEffect, useSyncExternalStore } from 'react'
import { useRouter } from 'next/navigation'

const TOKEN_KEY = 'fab_access_token'

let listeners: (() => void)[] = []

function emitChange() {
  for (const listener of listeners) listener()
}

function subscribe(listener: () => void) {
  listeners = [...listeners, listener]
  return () => {
    listeners = listeners.filter(l => l !== listener)
  }
}

function isTokenExpired(token: string): boolean {
  try {
    const payload = token.split('.')[1]
    if (!payload) return true
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    if (typeof decoded.exp !== 'number') return true
    return decoded.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  const token = localStorage.getItem(TOKEN_KEY)
  if (token && isTokenExpired(token)) {
    localStorage.removeItem(TOKEN_KEY)
    emitChange()
    return null
  }
  return token
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  emitChange()
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  emitChange()
}

export function useTokenValue(): string | null {
  return useSyncExternalStore(subscribe, getToken, () => null)
}

export function useRequireAuth(): string | null {
  const token = useTokenValue()
  const router = useRouter()
  useEffect(() => {
    if (token === null) router.push('/login')
  }, [token, router])
  return token
}
