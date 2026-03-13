import { test as setup, expect } from '@playwright/test'

const authFile = 'tests/e2e/.auth/demo.json'

setup('authenticate as demo user', async ({ page }) => {
  await page.goto('/login')
  await page.getByPlaceholder('Email').fill('demo@fabgreatlibrary.com')
  await page.getByPlaceholder('Password').fill('demo1234')
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page).toHaveURL('/sets')

  await page.context().storageState({ path: authFile })
})
