import { expect, test } from '@playwright/test'

test('welcome communicates with the actual API and fits the viewport', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await expect(page).toHaveTitle(/Lingora/)
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Your world.')
  await expect(page.getByRole('status')).toHaveText('Connection ready')
  await page.getByRole('button', { name: 'Check connection' }).click()
  await expect(page.getByRole('status')).toHaveText('Connection ready')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  expect(errors).toEqual([])
})

test('unavailable API offers a working retry', async ({ page }) => {
  await page.route('**/api/v1/health', (route) => route.abort())
  await page.goto('/')
  await expect(page.getByRole('status')).toContainText('We couldn’t connect')
  await page.unroute('**/api/v1/health')
  await page.getByRole('button', { name: 'Try again' }).click()
  await expect(page.getByRole('status')).toHaveText('Connection ready')
})
