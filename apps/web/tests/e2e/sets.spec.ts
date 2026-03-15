import { test, expect } from '@playwright/test'

test.describe('sets', () => {
  test('category picker loads', async ({ page }) => {
    await page.goto('/sets')

    await expect(page.getByRole('heading', { name: 'Browse Sets' })).toBeVisible()
    await expect(page.getByText('Booster Sets')).toBeVisible()
  })

  test('set grid loads with category', async ({ page }) => {
    await page.goto('/sets?type=booster')

    await expect(page.getByText(/\d+ sets/)).toBeVisible()
    await expect(page.locator('main a[href^="/sets/"]').first()).toBeVisible()
  })

  test('completion bars visible when authed', async ({ page }) => {
    await page.goto('/sets?type=booster')

    await expect(page.getByText(/\d+ \/ \d+ cards/).first()).toBeVisible()
  })

  test('click set opens detail', async ({ page }) => {
    await page.goto('/sets?type=booster')

    const firstSetLink = page.locator('main a[href^="/sets/"]').first()
    await firstSetLink.click()

    await expect(page).toHaveURL(/\/sets\/[\w-]+/)
    await expect(page.locator('th', { hasText: 'Card' })).toBeVisible()
    await expect(page.locator('tbody tr').first()).toBeVisible()
  })
})
