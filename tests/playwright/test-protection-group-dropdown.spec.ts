import { test, expect, Page } from '@playwright/test';
import { AuthHelper } from './auth-helper';

/**
 * Test: Protection Group Dropdown Debug
 * 
 * This test reproduces the issue where clicking a Protection Group in the
 * dropdown doesn't add it to the Wave 1 configuration. The test captures
 * console logs to see if:
 * 
 * 1. Protection Groups API returns data (🟣 purple circle logs)
 * 2. onChange handler fires (🔵 blue circle logs)
 * 3. What the actual bug is
 */

test.describe('Protection Group Dropdown Debug', () => {
  let authHelper: AuthHelper;
  const consoleLogs: string[] = [];
  const consoleErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    // Capture console logs
    page.on('console', (msg) => {
      const text = msg.text();
      consoleLogs.push(text);
      console.log(`[BROWSER CONSOLE] ${text}`);
    });

    // Capture console errors
    page.on('pageerror', (error) => {
      const text = error.message;
      consoleErrors.push(text);
      console.error(`[BROWSER ERROR] ${text}`);
    });

    // Login
    authHelper = new AuthHelper(page);
    await authHelper.login();
    console.log('✅ Login successful');
  });

  test('should debug Protection Group dropdown interaction', async ({ page }) => {
    console.log('\n🔍 Starting Protection Group dropdown debug test...\n');

    // Step 1: Navigate to Recovery Plans page
    console.log('Step 1: Navigating to Recovery Plans page...');
    await page.goto('/recovery-plans');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/screenshots/debug-01-recovery-plans.png' });
    console.log('✅ Recovery Plans page loaded');

    // Step 2: Click "Create New Recovery Plan" button
    console.log('\nStep 2: Clicking "Create New Recovery Plan" button...');
    const createButton = page.locator('button:has-text("Create New Recovery Plan")');
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();
    console.log('✅ Create button clicked');

    // Step 3: Wait for dialog to appear
    console.log('\nStep 3: Waiting for Recovery Plan dialog...');
    const dialog = page.locator('[role="dialog"]').first();
    await expect(dialog).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(2000); // Let dialog fully render
    await page.screenshot({ path: 'test-results/screenshots/debug-02-dialog-opened.png' });
    console.log('✅ Dialog opened');

    // Step 4: Expand Wave 1 accordion
    console.log('\nStep 4: Expanding Wave 1 accordion...');
    const wave1Header = page.locator('.MuiAccordion-root').filter({ hasText: 'Wave 1' }).locator('.MuiAccordionSummary-root');
    await wave1Header.click();
    await page.waitForTimeout(1000); // Let accordion expand
    await page.screenshot({ path: 'test-results/screenshots/debug-03-wave1-expanded.png' });
    console.log('✅ Wave 1 expanded');

    // Step 5: Clear console logs before dropdown interaction
    consoleLogs.length = 0;
    console.log('\n🧹 Cleared console logs - now watching for 🟣🔵 logs...\n');

    // Step 6: Click Protection Group dropdown
    console.log('Step 6: Clicking Protection Group dropdown...');
    const pgDropdown = page.locator('.MuiAccordion-root').filter({ hasText: 'Wave 1' })
      .locator('label:has-text("Protection Groups")').locator('..').locator('.MuiAutocomplete-root');
    
    await pgDropdown.click();
    await page.waitForTimeout(1000); // Let dropdown open
    await page.screenshot({ path: 'test-results/screenshots/debug-04-dropdown-opened.png' });
    console.log('✅ Protection Group dropdown clicked');

    // Step 7: Wait for options to load and appear
    console.log('\nStep 7: Waiting for Protection Group options...');
    const dropdownOptions = page.locator('.MuiAutocomplete-popper .MuiAutocomplete-option');
    
    try {
      await dropdownOptions.first().waitFor({ state: 'visible', timeout: 5000 });
      const optionCount = await dropdownOptions.count();
      console.log(`✅ Found ${optionCount} Protection Group options`);
    } catch (error) {
      console.error('❌ No Protection Group options appeared');
      await page.screenshot({ path: 'test-results/screenshots/debug-04b-no-options.png' });
    }

    // Step 8: Check console logs for 🟣 (API data)
    console.log('\n📊 Checking console logs for API data (🟣)...');
    const apiLogs = consoleLogs.filter(log => log.includes('🟣') || log.toLowerCase().includes('protection group'));
    if (apiLogs.length > 0) {
      console.log(`✅ Found ${apiLogs.length} API-related logs:`);
      apiLogs.forEach(log => console.log(`  ${log}`));
    } else {
      console.log('❌ No 🟣 API logs found - Protection Groups may not be loading');
    }

    // Step 9: Click first Protection Group option
    console.log('\nStep 9: Clicking first Protection Group option...');
    try {
      const firstOption = dropdownOptions.first();
      const optionText = await firstOption.textContent();
      console.log(`Clicking option: "${optionText}"`);
      
      await firstOption.click();
      await page.waitForTimeout(2000); // Let selection process
      await page.screenshot({ path: 'test-results/screenshots/debug-05-option-clicked.png' });
      console.log('✅ Protection Group option clicked');
    } catch (error) {
      console.error('❌ Failed to click Protection Group option');
    }

    // Step 10: Check console logs for 🔵 (onChange handler)
    console.log('\n📊 Checking console logs for onChange handler (🔵)...');
    const onChangeLogs = consoleLogs.filter(log => log.includes('🔵'));
    if (onChangeLogs.length > 0) {
      console.log(`✅ Found ${onChangeLogs.length} onChange logs:`);
      onChangeLogs.forEach(log => console.log(`  ${log}`));
    } else {
      console.log('❌ No 🔵 onChange logs found - Handler NOT firing!');
    }

    // Step 11: Check if chip appeared in Autocomplete
    console.log('\nStep 11: Checking if Protection Group chip appeared...');
    const chips = page.locator('.MuiAutocomplete-root .MuiChip-root');
    const chipCount = await chips.count();
    if (chipCount > 0) {
      console.log(`✅ Found ${chipCount} chip(s) - Selection successful!`);
      const chipText = await chips.first().textContent();
      console.log(`  Chip text: "${chipText}"`);
    } else {
      console.log('❌ No chips found - Selection FAILED!');
    }
    await page.screenshot({ path: 'test-results/screenshots/debug-06-final-state.png' });

    // Step 12: Check for any console errors
    console.log('\n🔍 Checking for console errors...');
    if (consoleErrors.length > 0) {
      console.log(`❌ Found ${consoleErrors.length} console errors:`);
      consoleErrors.forEach(error => console.error(`  ${error}`));
    } else {
      console.log('✅ No console errors detected');
    }

    // Final Summary
    console.log('\n' + '='.repeat(80));
    console.log('📋 TEST SUMMARY');
    console.log('='.repeat(80));
    console.log(`Total console logs captured: ${consoleLogs.length}`);
    console.log(`API logs (🟣): ${apiLogs.length}`);
    console.log(`onChange logs (🔵): ${onChangeLogs.length}`);
    console.log(`Console errors: ${consoleErrors.length}`);
    console.log(`Chips found: ${chipCount}`);
    console.log('='.repeat(80));

    // Print all captured logs for detailed analysis
    console.log('\n📝 ALL CAPTURED CONSOLE LOGS:');
    console.log('='.repeat(80));
    consoleLogs.forEach((log, index) => {
      console.log(`[${index + 1}] ${log}`);
    });
    console.log('='.repeat(80) + '\n');

    // Don't fail the test - we're just debugging
    console.log('✅ Debug test completed - check logs above for diagnosis');
  });

  test.afterEach(async () => {
    // Summary output
    console.log('\n📊 Test completed - check screenshots in test-results/screenshots/');
  });
});
