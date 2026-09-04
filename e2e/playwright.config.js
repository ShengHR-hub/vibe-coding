// @ts-check
import { defineConfig } from '@playwright/test'

const BASE = process.env.E2E_BASE_URL || 'http://127.0.0.1:5001'

export default defineConfig({
  testDir: './tests',
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: './results/html', open: 'never' }]],
  outputDir: './results/artifacts',
  use: {
    baseURL: BASE,
    headless: true,
    channel: 'msedge',
    viewport: { width: 1440, height: 900 },
    locale: 'zh-CN',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
})
