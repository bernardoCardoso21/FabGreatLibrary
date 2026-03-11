import { useSyncExternalStore } from 'react'

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

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
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
