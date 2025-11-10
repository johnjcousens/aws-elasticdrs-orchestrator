import { test, expect } from '@playwright/test';
import { AuthHelper } from './auth-helper';
import { ProtectionGroupsPage } from './page-objects/protection-groups-page';

/**
 * Smoke Tests for AWS DRS Orchestration
 * 
 * Quick validation tests that check critical functionality:
 * 1. Login works
 * 2. Protection Groups "Create Group" button is responsive
 * 3. Recovery Plans "Create Plan" button is responsive
 * 4. Dialog can be opened and closed
 * 
 * These tests should run in < 3 minutes and confirm basic functionality.
 * 
 * CRITICAL: These tests are expected to FAIL initially, confirming
 * the button responsiveness issue from Session 26.
 */

test.describe('Smoke Tests - Button Responsiveness', () => {
  test.beforeEach(async ({ page }) => {
    // Setup page for console error tracking
    const consoleLogs: any[] = [];
    page.on('console', msg => {
      consoleLogs.push({
        type: msg.type(),
        message: msg.text()
      });
    });
    (page as any).__consoleLogs = consoleLogs;
  });

  test('User can login successfully', async ({ page }) => {
    const auth = new AuthHelper(page);
    
    // Navigate and login
    await auth.login();
    
    // Verify we're on the dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Verify user is authenticated
    const isAuth = await auth.isAuthenticated();
    expect(isAuth).toBeTruthy();
    
    console.log('✓ Login test passed');
  });

  test('Protection Groups "Create Group" button opens dialog', async ({ page }) => {
    // Login first
    const auth = new AuthHelper(page);
    await auth.login();
    
    // Navigate to Protection Groups page
    const protectionGroupsPage = new ProtectionGroupsPage(page);
    await protectionGroupsPage.navigateToPage();
    
    // Take screenshot before clicking
    await protectionGroupsPage.screenshot('before-create-button-click');
    
    // THIS IS THE CRITICAL TEST - Click Create Group button
    try {
      await protectionGroupsPage.clickCreateButton();
      
      // Verify dialog opened
      const isOpen = await protectionGroupsPage.isDialogOpen();
      expect(isOpen).toBeTruthy();
      
      // Get dialog title
      const title = await protectionGroupsPage.getDialogTitle();
      console.log(`Dialog title: ${title}`);
      
      // Take screenshot of opened dialog
      await protectionGroupsPage.screenshot('create-group-dialog-open');
      
      // Check for console errors
      const errors = await protectionGroupsPage.getConsoleErrors();
      if (errors.length > 0) {
        console.log('Console errors detected:');
        errors.forEach(err => console.log(`  - ${err}`));
      }
      
      // Close dialog
      await protectionGroupsPage.closeDialog();
      
      console.log('✓ Protection Groups button test passed');
    } catch (error) {
      // Take failure screenshot
      await protectionGroupsPage.screenshot('create-button-click-FAILED');
      
      // Log console errors
      const errors = await protectionGroupsPage.getConsoleErrors();
      console.log('Console errors:');
      errors.forEach(err => console.log(`  - ${err}`));
      
      throw new Error(`Button click failed: ${error}`);
    }
  });

  test('Recovery Plans "Create Plan" button opens dialog', async ({ page }) => {
    // Login first
    const auth = new AuthHelper(page);
    await auth.login();
    
    // Navigate to Recovery Plans page
    await page.goto(`${process.env.CLOUDFRONT_URL}/recovery-plans`);
    
    // Wait for page load
    await page.waitForSelector('button:has-text("Create Plan"), button:has-text("Create New")', { 
      timeout: 10000 
    });
    
    // Take screenshot before clicking
    await page.screenshot({ 
      path: 'test-results/screenshots/before-create-plan-button-click.png',
      fullPage: true 
    });
    
    // THIS IS THE CRITICAL TEST - Click Create Plan button
    try {
      const createButton = page.locator('button:has-text("Create Plan"), button:has-text("Create New")').first();
      await createButton.click();
      
      // Wait for dialog
      await page.waitForSelector('[role="dialog"]', { timeout: 5000 });
      
      // Verify dialog is visible
      const dialog = page.locator('[role="dialog"]');
      await expect(dialog).toBeVisible();
      
      console.log('Dialog opened successfully');
      
      // Take screenshot of opened dialog
      await page.screenshot({ 
        path: 'test-results/screenshots/create-plan-dialog-open.png',
        fullPage: true 
      });
      
      // Close dialog
      const closeButton = page.locator('[role="dialog"] button:has-text("Cancel"), [aria-label="close"]').first();
      await closeButton.click();
      await page.waitForSelector('[role="dialog"]', { state: 'hidden', timeout: 5000 });
      
      console.log('✓ Recovery Plans button test passed');
    } catch (error) {
      // Take failure screenshot
      await page.screenshot({ 
        path: 'test-results/screenshots/create-plan-button-click-FAILED.png',
        fullPage: true 
      });
      
      throw new Error(`Button click failed: ${error}`);
    }
  });

  test('Dialog can be opened and closed', async ({ page }) => {
    // Login first
    const auth = new AuthHelper(page);
    await auth.login();
    
    // Navigate to Protection Groups
    const protectionGroupsPage = new ProtectionGroupsPage(page);
    await protectionGroupsPage.navigateToPage();
    
    // Open dialog
    await protectionGroupsPage.clickCreateButton();
    const isOpen = await protectionGroupsPage.isDialogOpen();
    expect(isOpen).toBeTruthy();
    
    // Close dialog
    await protectionGroupsPage.closeDialog();
    const isStillOpen = await protectionGroupsPage.isDialogOpen();
    expect(isStillOpen).toBeFalsy();
    
    console.log('✓ Dialog open/close test passed');
  });
});
