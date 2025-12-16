#!/usr/bin/env node

/**
 * Frontend Browser Test
 * 
 * Tests the deployed frontend to see if hardware data is displaying correctly.
 * Uses headless browser to login and check the Create Protection Group dialog.
 */

const puppeteer = require('puppeteer');

const CLOUDFRONT_URL = 'https://dh8z4705848un.cloudfront.net';
const TEST_EMAIL = '***REMOVED***';
const TEST_PASSWORD = '***REMOVED***';

async function testFrontend() {
  console.log('=== Frontend Browser Test ===');
  
  const browser = await puppeteer.launch({ 
    headless: false,  // Show browser for debugging
    defaultViewport: { width: 1200, height: 800 }
  });
  
  try {
    const page = await browser.newPage();
    
    // Enable console logging
    page.on('console', msg => {
      if (msg.text().includes('ServerDiscoveryPanel') || 
          msg.text().includes('ServerListItem') || 
          msg.text().includes('hardware')) {
        console.log('BROWSER CONSOLE:', msg.text());
      }
    });
    
    console.log('1. Navigating to CloudFront URL...');
    await page.goto(CLOUDFRONT_URL, { waitUntil: 'networkidle0' });
    
    console.log('2. Logging in...');
    await page.waitForSelector('input[type="email"]', { timeout: 10000 });
    await page.type('input[type="email"]', TEST_EMAIL);
    await page.type('input[type="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    
    console.log('3. Waiting for dashboard...');
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 15000 });
    
    console.log('4. Navigating to Protection Groups...');
    await page.click('a[href="/protection-groups"]');
    await page.waitForSelector('button:contains("Create Protection Group")', { timeout: 10000 });
    
    console.log('5. Opening Create Protection Group dialog...');
    await page.click('button:contains("Create Protection Group")');
    
    console.log('6. Waiting for region selector...');
    await page.waitForSelector('[data-testid="region-selector"]', { timeout: 10000 });
    
    console.log('7. Selecting us-west-2 region...');
    await page.click('[data-testid="region-selector"]');
    await page.click('option[value="us-west-2"]');
    
    console.log('8. Waiting for server discovery panel...');
    await page.waitForTimeout(3000); // Wait for API call
    
    console.log('9. Checking for test components...');
    const testComponents = await page.$$eval('[style*="border: 1px solid red"]', elements => {
      return elements.map(el => ({
        text: el.textContent,
        visible: el.offsetHeight > 0
      }));
    });
    
    console.log('Test components found:', testComponents.length);
    testComponents.forEach((comp, i) => {
      console.log(`Test Component ${i + 1}:`, comp.text.substring(0, 200));
    });
    
    console.log('10. Checking for DEBUG banners...');
    const debugBanners = await page.$$eval('[style*="background-color: rgb(255, 235, 59)"]', elements => {
      return elements.map(el => el.textContent);
    });
    
    console.log('DEBUG banners found:', debugBanners.length);
    debugBanners.forEach((banner, i) => {
      console.log(`DEBUG ${i + 1}:`, banner);
    });
    
    console.log('11. Taking screenshot...');
    await page.screenshot({ path: 'frontend-test-screenshot.png', fullPage: true });
    
    console.log('12. Waiting 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
  
  console.log('=== Test Complete ===');
}

// Check if puppeteer is available
try {
  require('puppeteer');
  testFrontend();
} catch (e) {
  console.log('Puppeteer not available. Install with: npm install puppeteer');
  console.log('Falling back to manual test instructions...');
  console.log('');
  console.log('MANUAL TEST STEPS:');
  console.log('1. Open:', CLOUDFRONT_URL);
  console.log('2. Login with:', TEST_EMAIL, '/', TEST_PASSWORD);
  console.log('3. Go to Protection Groups');
  console.log('4. Click "Create Protection Group"');
  console.log('5. Select region "us-west-2"');
  console.log('6. Look for red-bordered test components');
  console.log('7. Look for yellow DEBUG banners');
  console.log('8. Check browser console for hardware data logs');
}