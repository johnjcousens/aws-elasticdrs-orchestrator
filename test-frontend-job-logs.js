#!/usr/bin/env node

/**
 * Test the frontend job logs functionality by opening browser and checking the execution details page
 */

const puppeteer = require('puppeteer');

const EXECUTION_ID = '118991a4-6b5a-4400-a159-4b0b88b2f446';
const FRONTEND_URL = 'http://localhost:5173';
const TEST_EMAIL = 'testuser@example.com';
const TEST_PASSWORD = 'TestPassword123!';

async function testFrontendJobLogs() {
  console.log('🚀 Starting frontend job logs test...');
  
  const browser = await puppeteer.launch({ 
    headless: false, 
    defaultViewport: { width: 1200, height: 800 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Enable console logging
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (text.includes('🔍') || text.includes('📊') || text.includes('✅') || text.includes('❌')) {
        console.log(`[BROWSER ${type.toUpperCase()}] ${text}`);
      }
    });
    
    // Navigate to frontend
    console.log('🌐 Navigating to frontend...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle0' });
    
    // Check if we're on login page
    const isLoginPage = await page.$('input[type="email"]') !== null;
    
    if (isLoginPage) {
      console.log('🔐 Login page detected, logging in...');
      
      // Fill login form
      await page.type('input[type="email"]', TEST_EMAIL);
      await page.type('input[type="password"]', TEST_PASSWORD);
      
      // Click sign in button
      await page.click('button[type="submit"]');
      
      // Wait for navigation
      await page.waitForNavigation({ waitUntil: 'networkidle0' });
      console.log('✅ Login successful');
    }
    
    // Navigate to execution details page
    const executionUrl = `${FRONTEND_URL}/executions/${EXECUTION_ID}`;
    console.log(`🔍 Navigating to execution details: ${executionUrl}`);
    
    await page.goto(executionUrl, { waitUntil: 'networkidle0' });
    
    // Wait a bit for the page to load
    await page.waitForTimeout(3000);
    
    // Check if execution details loaded
    const executionTitle = await page.$eval('h1', el => el.textContent).catch(() => null);
    console.log(`📊 Page title: ${executionTitle}`);
    
    // Look for DRS Job Events section
    const jobEventsSection = await page.$('text/DRS Job Events').catch(() => null);
    if (jobEventsSection) {
      console.log('✅ Found DRS Job Events section');
    } else {
      console.log('❌ DRS Job Events section not found');
    }
    
    // Look for "Waiting for DRS job events..." text
    const waitingText = await page.$('text/Waiting for DRS job events...').catch(() => null);
    if (waitingText) {
      console.log('❌ Found "Waiting for DRS job events..." - this is the issue!');
    } else {
      console.log('✅ No "Waiting for DRS job events..." text found');
    }
    
    // Check network requests
    console.log('🔍 Checking network requests...');
    
    // Listen for network requests
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/job-logs')) {
        console.log(`📊 Job logs API call: ${response.status()} ${url}`);
      }
    });
    
    // Wait for any additional network requests
    await page.waitForTimeout(5000);
    
    // Take a screenshot
    await page.screenshot({ path: 'execution-details-screenshot.png', fullPage: true });
    console.log('📸 Screenshot saved as execution-details-screenshot.png');
    
    // Keep browser open for manual inspection
    console.log('🔍 Browser will stay open for manual inspection. Press Ctrl+C to close.');
    await page.waitForTimeout(60000); // Wait 1 minute
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  testFrontendJobLogs().catch(console.error);
}