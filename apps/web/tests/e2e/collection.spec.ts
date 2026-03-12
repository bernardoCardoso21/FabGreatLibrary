import { test, expect } from '@playwright/test'

test.describe('collection', () => {
  test('+1 increment', async ({ page }) => {
    await page.goto('/sets')

    const firstSetLink = page.locator('main a[href^="/sets/"]').first()
    await firstSetLink.click()
    await expect(page.locator('tbody tr').first()).toBeVisible()

    const firstRow = page.locator('tbody tr').first()
    const qtyCell = firstRow.locator('td.text-center')
    const beforeText = await qtyCell.textContent()
    const beforeQty = beforeText === '\u2014' ? 0 : parseInt(beforeText ?? '0', 10)

    await firstRow.getByRole('button', { name: '+1' }).click()

    await expect(qtyCell).toHaveText(String(beforeQty + 1), { timeout: 5000 })
  })

  test('bulk clear', async ({ page }) => {
    await page.goto('/sets')

    const firstSetLink = page.locator('main a[href^="/sets/"]').first()
    await firstSetLink.click()
    await expect(page.locator('tbody tr').first()).toBeVisible()

    const firstRow = page.locator('tbody tr').first()
    const qtyCell = firstRow.locator('td.text-center')

    const currentText = await qtyCell.textContent()
    if (currentText === '\u2014' || currentText === '0') {
      await firstRow.getByRole('button', { name: '+1' }).click()
      await expect(qtyCell).not.toHaveText('\u2014', { timeout: 5000 })
    }

    await firstRow.locator('button[role="checkbox"]').click()
    await expect(page.getByText(/\d+ selected/)).toBeVisible()

    await page.getByRole('button', { name: 'Clear' }).click()
    await expect(qtyCell).toHaveText('\u2014', { timeout: 5000 })
  })
})
