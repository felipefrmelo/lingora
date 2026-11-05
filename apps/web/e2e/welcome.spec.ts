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

test('anonymous visitors cannot open a student account', async ({ page, request }) => {
  const accountRequests: string[] = []
  page.on('request', (call) => {
    if (call.url().includes('/api/v1/me')) accountRequests.push(call.url())
  })
  for (const path of ['/app', '/app/onboarding', '/app/profile']) {
    await page.goto(path)
    await expect(page.getByRole('heading', { name: 'Sign-in is temporarily unavailable' })).toBeVisible()
    await expect(page.getByText('Account created', { exact: false })).toHaveCount(0)
  }
  expect(accountRequests).toEqual([])
  const response = await request.get('/api/v1/me')
  expect(response.status()).toBe(401)
  expect((await request.get('/api/v1/me/profile')).status()).toBe(401)
  expect((await request.get('/api/v1/me/assessments')).status()).toBe(401)
  await page.getByRole('link', { name: 'Return home' }).click()
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Your world.')
})
