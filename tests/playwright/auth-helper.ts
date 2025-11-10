import { Page } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load test environment
dotenv.config({ path: path.resolve(__dirname, '../../.env.test') });

/**
 * Authentication helper for AWS Cognito login
 * 
 * Provides utilities for logging in, logging out, and managing
 * authentication state during Playwright tests.
 */
export class AuthHelper {
  private page: Page;
  private baseUrl: string;
  private username: string;
  private password: string;

  constructor(page: Page) {
    this.page = page;
    this.baseUrl = process.env.CLOUDFRONT_URL || '';
    this.username = process.env.TEST_USER_USERNAME || '';
    this.password = process.env.TEST_USER_PASSWORD || '';
  }

  /**
   * Navigate to login page and authenticate with Cognito
   * @returns Promise that resolves when login is complete
   */
  async login(): Promise<void> {
    console.log(`Logging in as: ${this.username}`);
    
    // Navigate to application (should redirect to login if not authenticated)
    await this.page.goto(this.baseUrl);
    
    // Wait for login form to appear
    await this.page.waitForSelector('input[name="username"], input[type="email"]', { 
      timeout: 10000 
    });
    
    // Fill in credentials
    const usernameField = await this.page.locator('input[name="username"], input[type="email"]').first();
    await usernameField.fill(this.username);
    
    const passwordField = await this.page.locator('input[name="password"], input[type="password"]').first();
    await passwordField.fill(this.password);
    
    // Click sign in button
    const signInButton = await this.page.locator('button[type="submit"], button:has-text("Sign In")').first();
    await signInButton.click();
    
    // Wait for successful login (redirect to dashboard)
    await this.page.waitForURL('**/dashboard', { 
      timeout: 15000,
      waitUntil: 'networkidle'
    });
    
    console.log('Login successful');
  }

  /**
   * Alternative login method with custom credentials
   * @param username Custom username
   * @param password Custom password
   */
  async loginWithCredentials(username: string, password: string): Promise<void> {
    console.log(`Logging in as: ${username}`);
    
    await this.page.goto(this.baseUrl);
    await this.page.waitForSelector('input[name="username"], input[type="email"]');
    
    await this.page.fill('input[name="username"], input[type="email"]', username);
    await this.page.fill('input[name="password"], input[type="password"]', password);
    await this.page.click('button[type="submit"], button:has-text("Sign In")');
    
    await this.page.waitForURL('**/dashboard', { timeout: 15000 });
    console.log('Login successful');
  }

  /**
   * Logout from the application
   */
  async logout(): Promise<void> {
    console.log('Logging out');
    
    // Click user menu
    const userMenuButton = await this.page.locator('[aria-label="User menu"], button:has-text("Account")').first();
    await userMenuButton.click();
    
    // Wait for menu to appear
    await this.page.waitForTimeout(500);
    
    // Click logout option
    const logoutButton = await this.page.locator('text="Sign Out", text="Logout"').first();
    await logoutButton.click();
    
    // Wait for redirect to login page
    await this.page.waitForURL('**/login', { timeout: 10000 });
    
    console.log('Logout successful');
  }

  /**
   * Check if user is currently authenticated
   * @returns true if authenticated, false otherwise
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      // Check for auth token in localStorage
      const token = await this.page.evaluate(() => {
        return localStorage.getItem('CognitoIdentityServiceProvider.access_token') || 
               localStorage.getItem('accessToken');
      });
      
      return !!token;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current auth token from localStorage
   * @returns Auth token or null
   */
  async getAuthToken(): Promise<string | null> {
    try {
      return await this.page.evaluate(() => {
        return localStorage.getItem('CognitoIdentityServiceProvider.access_token') || 
               localStorage.getItem('accessToken');
      });
    } catch (error) {
      return null;
    }
  }

  /**
   * Clear authentication state
   */
  async clearAuth(): Promise<void> {
    await this.page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    console.log('Authentication state cleared');
  }

  /**
   * Wait for authentication to complete
   * Useful after login redirects
   */
  async waitForAuth(timeout: number = 5000): Promise<void> {
    await this.page.waitForFunction(
      () => {
        return !!localStorage.getItem('CognitoIdentityServiceProvider.access_token') ||
               !!localStorage.getItem('accessToken');
      },
      { timeout }
    );
  }

  /**
   * Setup authentication for a test
   * Logs in if not already authenticated
   */
  async ensureAuthenticated(): Promise<void> {
    const isAuth = await this.isAuthenticated();
    if (!isAuth) {
      await this.login();
    } else {
      console.log('Already authenticated');
    }
  }
}
