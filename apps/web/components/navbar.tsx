'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { clearToken, getToken } from '@/lib/auth'

export function Navbar() {
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    setIsLoggedIn(!!getToken())
  }, [])

  function logout() {
    clearToken()
    setIsLoggedIn(false)
    router.push('/')
  }

  return (
    <nav className="border-b bg-background">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          FabGreat Library
        </Link>
        <div className="flex items-center gap-3">
          {isLoggedIn ? (
            <>
              <Link href="/sets" className="text-sm text-muted-foreground hover:text-foreground">
                My Collection
              </Link>
              <Link href="/missing" className="text-sm text-muted-foreground hover:text-foreground">
                Missing
              </Link>
              <Button variant="outline" size="sm" onClick={logout}>
                Log out
              </Button>
            </>
          ) : (
            <>
              <Link href="/sets" className="text-sm text-muted-foreground hover:text-foreground">
                Browse Sets
              </Link>
              <Link href="/login">
                <Button variant="ghost" size="sm">Log in</Button>
              </Link>
              <Link href="/register">
                <Button size="sm">Sign up</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
