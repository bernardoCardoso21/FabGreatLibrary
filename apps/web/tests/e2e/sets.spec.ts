import { test, expect } from '@playwright/test'

test.describe('sets', () => {
  test('set grid loads', async ({ page }) => {
    await page.goto('/sets')

    await expect(page.getByRole('heading', { name: 'Sets' })).toBeVisible()
    await expect(page.getByText(/\d+ sets/)).toBeVisible()
    await expect(page.locator('a').filter({ has: page.locator('[class*="card"]') }).first()).toBeVisible()
  })

  test('completion bars visible when authed', async ({ page }) => {
    await page.goto('/sets')

    await expect(page.getByText(/\d+ \/ \d+ owned/).first()).toBeVisible()
  })

  test('click set opens detail', async ({ page }) => {
    await page.goto('/sets')

    const firstSetLink = page.locator('main a[href^="/sets/"]').first()
    await firstSetLink.click()

    await expect(page).toHaveURL(/\/sets\/[\w-]+/)
    await expect(page.locator('th', { hasText: 'Card' })).toBeVisible()
    await expect(page.locator('tbody tr').first()).toBeVisible()
  })
})
