#!/usr/bin/env node

// Test localhost frontend behavior to identify issues
const puppeteer = require('puppeteer');
const fs = require('fs');

async function testLocalhostFrontend() {
  console.log('🧪 TESTING LOCALHOST FRONTEND');
  console.log('==============================\n');
  
  let browser;
  try {
    // Launch browser
    browser = await puppeteer.launch({ 
      headless: false, // Show browser for debugging
      devtools: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Listen for console messages
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') {
        console.log('❌ Browser Error:', text);
      } else if (type === 'warn') {
        console.log('⚠️  Browser Warning:', text);
      } else if (text.includes('AWS') || text.includes('auth') || text.includes('config')) {
        console.log(`📝 Browser Log (${type}):`, text);
      }
    });
    
    // Listen for network failures
    page.on('requestfailed', request => {
      console.log('🌐 Network Failed:', request.url(), request.failure().errorText);
    });
    
    console.log('1. Loading localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
    
    // Wait a bit for config to load
    await page.waitForTimeout(2000);
    
    console.log('2. Checking page title...');
    const title = await page.title();
    console.log('   Title:', title);
    
    console.log('3. Checking for AWS config...');
    const awsConfig = await page.evaluate(() => {
      return window.AWS_CONFIG;
    });
    console.log('   AWS Config:', awsConfig);
    
    console.log('4. Checking for authentication state...');
    const authState = await page.evaluate(() => {
      // Try to get auth context state
      const authElements = document.querySelectorAll('[data-testid*="auth"], [class*="auth"]');
      return {
        hasAuthElements: authElements.length > 0,
        bodyText: document.body.innerText.substring(0, 500)
      };
    });
    console.log('   Auth elements found:', authState.hasAuthElements);
    console.log('   Page content preview:', authState.bodyText.substring(0, 200) + '...');
    
    console.log('5. Looking for login form...');
    const loginForm = await page.$('form, [type="email"], [type="password"], button[type="submit"]');
    if (loginForm) {
      console.log('   ✅ Login form found');
      
      // Try to find email and password fields
      const emailField = await page.$('input[type="email"], input[name*="email"], input[placeholder*="email"]');
      const passwordField = await page.$('input[type="password"], input[name*="password"]');
      
      if (emailField && passwordField) {
        console.log('6. Attempting login...');
        await emailField.type('***REMOVED***');
        await passwordField.type('***REMOVED***');
        
        // Look for submit button
        const submitButton = await page.$('button[type="submit"], button:contains("Sign"), button:contains("Login")');
        if (submitButton) {
          await submitButton.click();
          console.log('   ✅ Login attempted');
          
          // Wait for navigation or auth state change
          await page.waitForTimeout(5000);
          
          console.log('7. Checking post-login state...');
          const postLoginContent = await page.evaluate(() => {
            return {
              url: window.location.href,
              bodyText: document.body.innerText.substring(0, 500),
              hasAccountSelector: !!document.querySelector('[data-testid*="account"], select, [class*="account"]')
            };
          });
          
          console.log('   Current URL:', postLoginContent.url);
          console.log('   Has account selector:', postLoginContent.hasAccountSelector);
          console.log('   Content preview:', postLoginContent.bodyText.substring(0, 200) + '...');
          
          // Check if we can navigate to executions
          console.log('8. Navigating to executions page...');
          try {
            await page.goto('http://localhost:3000/executions', { waitUntil: 'networkidle0' });
            await page.waitForTimeout(3000);
            
            const executionsContent = await page.evaluate(() => {
              return {
                bodyText: document.body.innerText,
                hasTable: !!document.querySelector('table, [role="table"]'),
                hasExecutions: document.body.innerText.includes('execution') || document.body.innerText.includes('drill')
              };
            });
            
            console.log('   Has table:', executionsContent.hasTable);
            console.log('   Has executions:', executionsContent.hasExecutions);
            console.log('   Executions page content:', executionsContent.bodyText.substring(0, 300) + '...');
            
          } catch (error) {
            console.log('   ❌ Failed to navigate to executions:', error.message);
          }
        } else {
          console.log('   ❌ No submit button found');
        }
      } else {
        console.log('   ❌ Email or password field not found');
      }
    } else {
      console.log('   ❌ No login form found');
      console.log('   This might indicate the user is already logged in or there\'s an error');
    }
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'localhost-test-screenshot.png', fullPage: true });
    console.log('📸 Screenshot saved as localhost-test-screenshot.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Check if puppeteer is available
try {
  require('puppeteer');
  testLocalhostFrontend();
} catch (error) {
  console.log('⚠️  Puppeteer not available, running simplified test...');
  
  // Fallback: Test the config loading manually
  const https = require('https');
  
  console.log('🧪 SIMPLIFIED LOCALHOST TEST');
  console.log('=============================\n');
  
  // Test if localhost:3000 is responding
  const http = require('http');
  const req = http.get('http://localhost:3000', (res) => {
    console.log('✅ Localhost:3000 is responding');
    console.log('   Status:', res.statusCode);
    console.log('   Headers:', res.headers['content-type']);
    
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      if (data.includes('AWS DRS Orchestrator')) {
        console.log('✅ Frontend loaded correctly');
      } else {
        console.log('❌ Frontend content issue');
      }
      
      // Test config endpoint
      const configReq = http.get('http://localhost:3000/aws-config.local.json', (configRes) => {
        let configData = '';
        configRes.on('data', chunk => configData += chunk);
        configRes.on('end', () => {
          try {
            const config = JSON.parse(configData);
            console.log('✅ Local config loaded:', config);
          } catch (e) {
            console.log('❌ Config parsing failed:', e.message);
          }
        });
      });
      
      configReq.on('error', (err) => {
        console.log('❌ Config request failed:', err.message);
      });
    });
  });
  
  req.on('error', (err) => {
    console.log('❌ Localhost request failed:', err.message);
    console.log('   Make sure frontend is running on localhost:3000');
  });
}