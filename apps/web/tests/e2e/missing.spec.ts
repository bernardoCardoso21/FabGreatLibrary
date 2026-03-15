import { test, expect } from '@playwright/test'

async function goToMissing(page: import('@playwright/test').Page) {
  await page.goto('/sets')
  await expect(page.getByRole('heading', { name: 'Sets' })).toBeVisible()
  await page.getByRole('link', { name: 'Missing' }).click()
  await expect(page.getByRole('heading', { name: 'Missing Printings' })).toBeVisible()
}

test.describe('missing', () => {
  test('page loads', async ({ page }) => {
    await goToMissing(page)

    await expect(page.getByText(/\d+ missing printing/)).toBeVisible()
    await expect(page.locator('tbody tr').first()).toBeVisible()
  })

  test('filter by foiling', async ({ page }) => {
    await goToMissing(page)

    await expect(page.getByText(/\d+ missing printing/)).toBeVisible()
    const beforeText = await page.getByText(/\d+ missing printing/).textContent()

    const foilingSelect = page.locator('select').nth(1)
    await foilingSelect.selectOption('R')

    await expect(page.getByText(/\d+ missing printing/)).not.toHaveText(beforeText!, { timeout: 5000 })
  })
})
