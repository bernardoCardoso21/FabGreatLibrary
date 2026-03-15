import { test, expect } from '@playwright/test'

test.describe('collection', () => {
  test('increment and decrement', async ({ page }) => {
    await page.goto('/sets?type=booster')

    const firstSetLink = page.locator('main a[href^="/sets/"]').first()
    await firstSetLink.click()
    await expect(page.locator('tbody tr').first()).toBeVisible()

    const firstRow = page.locator('tbody tr').first()
    const qtySpan = firstRow.locator('span.font-mono')
    const beforeText = await qtySpan.textContent()
    const beforeOwned = parseInt(beforeText?.split('/')[0].trim() ?? '0', 10)

    await firstRow.getByRole('button', { name: '+' }).click()

    await expect(qtySpan).toContainText(`${beforeOwned + 1} /`, { timeout: 5000 })

    await firstRow.getByRole('button', { name: '-' }).click()

    await expect(qtySpan).toContainText(`${beforeOwned} /`, { timeout: 5000 })
  })
})
