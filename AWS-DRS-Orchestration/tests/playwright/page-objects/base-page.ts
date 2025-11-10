import { Page, Locator } from '@playwright/test';

/**
 * Base Page Object
 * 
 * Provides common functionality for all page objects including
 * navigation, waiting, screenshots, and error checking.
 */
export abstract class BasePage {
  protected page: Page;
  protected baseUrl: string;

  constructor(page: Page) {
    this.page = page;
    this.baseUrl = process.env.CLOUDFRONT_URL || '';
  }

  /**
   * Navigate to the page
   * Must be implemented by each page object
   */
  abstract navigateToPage(): Promise<void>;

  /**
   * Wait for page-specific elements to load
   * Must be implemented by each page object
   */
  abstract waitForPageLoad(): Promise<void>;

  /**
   * Navigate to dashboard
   */
  async goToDashboard(): Promise<void> {
    await this.page.click('a[href="/"], a[href="/dashboard"]');
    await this.page.waitForURL('**/dashboard');
  }

  /**
   * Navigate to Protection Groups page
   */
  async goToProtectionGroups(): Promise<void> {
    await this.page.click('a[href="/protection-groups"]');
    await this.page.waitForURL('**/protection-groups');
  }

  /**
   * Navigate to Recovery Plans page
   */
  async goToRecoveryPlans(): Promise<void> {
    await this.page.click('a[href="/recovery-plans"]');
    await this.page.waitForURL('**/recovery-plans');
  }

  /**
   * Navigate to Executions page
   */
  async goToExecutions(): Promise<void> {
    await this.page.click('a[href="/executions"]');
    await this.page.waitForURL('**/executions');
  }

  /**
   * Wait for element to be visible
   * @param selector CSS selector
   * @param timeout Timeout in milliseconds
   */
  async waitForElement(selector: string, timeout: number = 5000): Promise<Locator> {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout });
    return element;
  }

  /**
   * Wait for element to be hidden
   * @param selector CSS selector
   * @param timeout Timeout in milliseconds
   */
  async waitForElementHidden(selector: string, timeout: number = 5000): Promise<void> {
    await this.page.locator(selector).waitFor({ state: 'hidden', timeout });
  }

  /**
   * Click element with retry logic
   * @param selector CSS selector
   * @param maxAttempts Maximum retry attempts
   */
  async clickWithRetry(selector: string, maxAttempts: number = 3): Promise<void> {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        await this.page.click(selector, { timeout: 5000 });
        return;
      } catch (error) {
        if (attempt === maxAttempts) {
          throw new Error(`Failed to click ${selector} after ${maxAttempts} attempts: ${error}`);
        }
        console.log(`Click attempt ${attempt} failed, retrying...`);
        await this.page.waitForTimeout(1000);
      }
    }
  }

  /**
   * Fill input field with retry
   * @param selector CSS selector
   * @param value Value to fill
   */
  async fillWithRetry(selector: string, value: string): Promise<void> {
    await this.page.fill(selector, value);
    
    // Verify value was set
    const actualValue = await this.page.inputValue(selector);
    if (actualValue !== value) {
      // Retry once
      await this.page.fill(selector, '');
      await this.page.fill(selector, value);
    }
  }

  /**
   * Take screenshot
   * @param name Screenshot name
   */
  async screenshot(name: string): Promise<string> {
    const timestamp = Date.now();
    const path = `test-results/screenshots/${name}-${timestamp}.png`;
    await this.page.screenshot({ path, fullPage: true });
    console.log(`Screenshot saved: ${path}`);
    return path;
  }

  /**
   * Check for console errors
   */
  async hasConsoleErrors(): Promise<boolean> {
    const errors = await this.page.evaluate(() => {
      const logs = (window as any).__consoleLogs || [];
      return logs.filter((log: any) => log.type === 'error');
    });
    return errors.length > 0;
  }

  /**
   * Get console errors
   */
  async getConsoleErrors(): Promise<string[]> {
    return await this.page.evaluate(() => {
      const logs = (window as any).__consoleLogs || [];
      return logs
        .filter((log: any) => log.type === 'error')
        .map((log: any) => log.message);
    });
  }

  /**
   * Wait for toast notification
   * @param message Expected message (partial match)
   * @param timeout Timeout in milliseconds
   */
  async waitForToast(message?: string, timeout: number = 5000): Promise<boolean> {
    try {
      const toastSelector = '.Toastify__toast';
      await this.page.waitForSelector(toastSelector, { timeout });
      
      if (message) {
        const toastText = await this.page.locator(toastSelector).textContent();
        return toastText?.includes(message) || false;
      }
      
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Wait for toast to disappear
   */
  async waitForToastHidden(timeout: number = 5000): Promise<void> {
    try {
      await this.page.waitForSelector('.Toastify__toast', { state: 'hidden', timeout });
    } catch (error) {
      // Toast already hidden or never appeared
    }
  }

  /**
   * Check if element exists
   * @param selector CSS selector
   */
  async elementExists(selector: string): Promise<boolean> {
    try {
      const element = await this.page.locator(selector).count();
      return element > 0;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get element text
   * @param selector CSS selector
   */
  async getElementText(selector: string): Promise<string> {
    const element = await this.waitForElement(selector);
    const text = await element.textContent();
    return text?.trim() || '';
  }

  /**
   * Wait for loading to complete
   * Waits for common loading indicators to disappear
   */
  async waitForLoadingComplete(timeout: number = 10000): Promise<void> {
    const loadingSelectors = [
      '.MuiCircularProgress-root',
      '[role="progressbar"]',
      '.loading-spinner',
      '.MuiSkeleton-root'
    ];
    
    for (const selector of loadingSelectors) {
      try {
        const count = await this.page.locator(selector).count();
        if (count > 0) {
          await this.page.locator(selector).first().waitFor({ state: 'hidden', timeout });
        }
      } catch (error) {
        // Element not found or already hidden
      }
    }
  }

  /**
   * Wait for network idle
   */
  async waitForNetworkIdle(timeout: number = 5000): Promise<void> {
    await this.page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Refresh page and wait for load
   */
  async refresh(): Promise<void> {
    await this.page.reload({ waitUntil: 'networkidle' });
    await this.waitForPageLoad();
  }

  /**
   * Get current URL
   */
  getCurrentUrl(): string {
    return this.page.url();
  }

  /**
   * Generate test data with timestamp
   * @param prefix Prefix for test data
   */
  generateTestName(prefix: string = 'Test'): string {
    const timestamp = Date.now();
    return `${prefix} ${timestamp}`;
  }
}
