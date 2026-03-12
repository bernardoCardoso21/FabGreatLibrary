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

  test.describe.serial('wishlist CRUD', () => {
    test('cleanup existing wishlist', async ({ page }) => {
      await goToMissing(page)

      const savedWishlist = page.getByText('Saved wishlist:')
      if (await savedWishlist.isVisible({ timeout: 2000 }).catch(() => false)) {
        await page.getByRole('button', { name: 'Delete' }).click()
        await expect(savedWishlist).toBeHidden({ timeout: 10000 })
      }
    })

    test('save wishlist', async ({ page }) => {
      await goToMissing(page)

      const input = page.getByPlaceholder(/Wishlist name/)
      await expect(input).toBeVisible({ timeout: 10000 })
      await input.fill('Test Wishlist')
      await page.getByRole('button', { name: 'Save current filter' }).click()

      await expect(page.getByText('Saved wishlist:')).toBeVisible({ timeout: 10000 })
      await expect(page.getByText('Test Wishlist')).toBeVisible()
    })

    test('delete wishlist', async ({ page }) => {
      await goToMissing(page)

      await expect(page.getByText('Saved wishlist:')).toBeVisible({ timeout: 10000 })
      await page.getByRole('button', { name: 'Delete' }).click()

      await expect(page.getByText('Saved wishlist:')).toBeHidden({ timeout: 10000 })
      await expect(page.getByRole('button', { name: 'Save current filter' })).toBeVisible()
    })
  })
})
