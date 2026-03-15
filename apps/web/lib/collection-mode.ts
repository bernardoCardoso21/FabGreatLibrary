import { useSyncExternalStore } from 'react'

const STORAGE_KEY = 'fab_collection_mode'
type CollectionMode = 'master_set' | 'playset'

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

export function getCollectionMode(): CollectionMode {
  if (typeof window === 'undefined') return 'playset'
  return (localStorage.getItem(STORAGE_KEY) as CollectionMode) ?? 'playset'
}

export function setCollectionMode(mode: CollectionMode): void {
  localStorage.setItem(STORAGE_KEY, mode)
  emitChange()
}

export function useCollectionMode(): CollectionMode {
  return useSyncExternalStore(subscribe, getCollectionMode, () => 'playset' as CollectionMode)
}
