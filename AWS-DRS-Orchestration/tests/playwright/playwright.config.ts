import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load test environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env.test') });

/**
 * Playwright Test Configuration for AWS DRS Orchestration
 * 
 * This configuration supports testing via Cline MCP Playwright integration.
 * Tests run against the deployed CloudFront distribution.
 */
export default defineConfig({
  testDir: './',
  
  // Test execution settings
  fullyParallel: false, // Run tests sequentially for data consistency
  forbidOnly: !!process.env.CI,
  retries: parseInt(process.env.TEST_RETRIES || '2'),
  workers: 1, // Single worker for sequential execution
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['list'],
    ['json', { outputFile: 'test-results/test-results.json' }]
  ],
  
  // Global test settings
  use: {
    // Base URL from environment
    baseURL: process.env.CLOUDFRONT_URL || 'https://d20h85rw0j51j.cloudfront.net',
    
    // Browser settings
    headless: process.env.HEADLESS === 'true',
    viewport: { width: 1280, height: 720 },
    
    // Timeouts
    actionTimeout: parseInt(process.env.TEST_TIMEOUT || '30000'),
    navigationTimeout: parseInt(process.env.TEST_TIMEOUT || '30000'),
    
    // Screenshots and videos
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Ignore HTTPS errors for testing
    ignoreHTTPSErrors: true,
  },

  // Test timeout
  timeout: 120000, // 2 minutes per test
  expect: {
    timeout: 10000 // 10 seconds for assertions
  },

  // Project configurations for different browsers
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // AWS Cognito login requires these permissions
        permissions: ['clipboard-read', 'clipboard-write']
      },
    },
    
    // Uncomment to test on Firefox
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    
    // Uncomment to test on WebKit (Safari)
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Output directories
  outputDir: 'test-results/artifacts',
  
  // Web server (not needed - testing deployed app)
  // webServer: undefined,
});
