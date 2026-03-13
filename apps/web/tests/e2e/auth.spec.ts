import { test, expect } from '@playwright/test'

test.describe('auth', () => {
  test('register new account', async ({ browser }) => {
    const context = await browser.newContext({ storageState: { cookies: [], origins: [] } })
    const page = await context.newPage()

    await page.goto('/register')
    await page.getByPlaceholder('Email').fill(`test-${Date.now()}@example.com`)
    await page.getByPlaceholder('Password').fill('testpass123')
    await page.getByRole('button', { name: 'Create account' }).click()

    await expect(page).toHaveURL('/sets')
    await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible()

    await context.close()
  })

  test('login with demo account', async ({ browser }) => {
    const context = await browser.newContext({ storageState: { cookies: [], origins: [] } })
    const page = await context.newPage()

    await page.goto('/login')
    await page.getByRole('button', { name: 'Try demo account' }).click()
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page).toHaveURL('/sets')

    await context.close()
  })

  test('logout', async ({ page }) => {
    await page.goto('/sets')
    await page.getByRole('button', { name: 'Log out' }).click()

    await expect(page).toHaveURL('/')
    await expect(page.getByRole('button', { name: 'Log in' })).toBeVisible()
  })
})
